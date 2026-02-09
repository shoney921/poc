"""
Phase 1: 순수 벡터 검색 실험
============================
ChromaDB + Sentence-Transformers를 사용한 의미 기반 검색 실험.

실행 방법:
    python -m src.phase1_vector.experiment

다른 임베딩 모델로 실행:
    python -m src.phase1_vector.experiment --model "BAAI/bge-m3"
"""

import argparse
import json
import os

import chromadb
from chromadb.utils import embedding_functions

from src.evaluation.metrics import SearchTimer, evaluate_single_query, aggregate_metrics

# ─────────────────────────────────────────────
# 사용 가능한 임베딩 모델 목록
# ─────────────────────────────────────────────
# "default" → ChromaDB 내장 임베딩 (외부 다운로드 불필요)
# 나머지는 sentence-transformers 모델 (HuggingFace 접속 필요)
EMBEDDING_MODELS = {
    "default": "default",                       # ChromaDB 내장 (ONNX MiniLM)
    "minilm": "all-MiniLM-L6-v2",              # 384차원, 빠르고 가벼움
    "mpnet": "all-mpnet-base-v2",              # 768차원, 더 높은 품질
    "bge-m3": "BAAI/bge-m3",                   # 1024차원, 다국어 (한국어 우수)
}


def _create_embedding_fn(model_name: str):
    """임베딩 함수를 생성한다. 외부 접속 불가 시 ChromaDB 기본 임베딩으로 폴백."""
    if model_name == "default":
        return None  # ChromaDB 기본 임베딩 사용

    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
    except Exception as e:
        print(f"[!] 모델 '{model_name}' 로드 실패: {e}")
        print("[!] ChromaDB 기본 임베딩으로 폴백합니다.")
        return None


class VectorSearchExperiment:
    """Phase 1: 순수 벡터 검색 실험 클래스"""

    def __init__(self, model_name: str = "default", collection_name: str = "diaries"):
        """
        Args:
            model_name: 임베딩 모델 이름 ("default" = ChromaDB 내장)
            collection_name: ChromaDB 컬렉션 이름
        """
        self.model_name = model_name
        self.collection_name = collection_name

        # ChromaDB 클라이언트 (인메모리 — 실험용)
        self.client = chromadb.Client()

        # 임베딩 함수 설정
        self.embedding_fn = _create_embedding_fn(model_name)

        self.collection = None
        self.diaries = []

    def load_data(self, data_path: str = "data/diaries.json"):
        """일기 데이터를 로드한다."""
        with open(data_path, "r", encoding="utf-8") as f:
            self.diaries = json.load(f)
        print(f"[Phase 1] 일기 {len(self.diaries)}개 로드 완료")

    def build_index(self):
        """ChromaDB에 일기 데이터를 인덱싱한다."""
        # 기존 컬렉션 삭제 후 재생성
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        create_kwargs = {
            "name": self.collection_name,
            "metadata": {"hnsw:space": "cosine"},  # 코사인 유사도 사용
        }
        if self.embedding_fn is not None:
            create_kwargs["embedding_function"] = self.embedding_fn

        self.collection = self.client.create_collection(**create_kwargs)

        # 배치 단위로 추가 (ChromaDB 제한: 한번에 최대 ~5000개)
        batch_size = 100
        for i in range(0, len(self.diaries), batch_size):
            batch = self.diaries[i:i + batch_size]
            self.collection.add(
                ids=[d["entry_id"] for d in batch],
                documents=[d["content"] for d in batch],
                metadatas=[{
                    "person_id": d["person_id"],
                    "person_name": d["person_name"],
                    "date": d["date"],
                    "mood": d["mood"],
                    "mood_score": d["mood_score"],
                    "weather": d["weather"],
                    "tags": ",".join(d["tags"]),
                } for d in batch],
            )

        print(f"[Phase 1] 인덱싱 완료 (모델: {self.model_name}, 문서 수: {self.collection.count()})")

    def search(self, query: str, n_results: int = 10, where: dict = None) -> dict:
        """
        벡터 검색을 수행한다.

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            where: 메타데이터 필터 (예: {"person_id": "A"})

        Returns:
            dict: 검색 결과 (ids, documents, distances, metadatas)
        """
        kwargs = {
            "query_texts": [query],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        with SearchTimer() as timer:
            results = self.collection.query(**kwargs)

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "metadatas": results["metadatas"][0],
            "latency_ms": timer.elapsed_ms,
        }

    def run_experiment(self, queries: list[dict]) -> list[dict]:
        """
        전체 테스트 쿼리를 실행하고 결과를 반환한다.

        Args:
            queries: Ground Truth 쿼리 리스트

        Returns:
            list[dict]: 각 쿼리별 검색 결과 + 평가 지표
        """
        results = []

        for q in queries:
            search_result = self.search(q["query"], n_results=10)

            # Ground Truth 기반 관련 문서 판별 (태그/감정 매칭)
            relevant_ids = self._find_relevant_ids(q)

            metrics = evaluate_single_query(
                retrieved_ids=search_result["ids"],
                relevant_ids=relevant_ids,
                latency_ms=search_result["latency_ms"],
            )

            results.append({
                "query_id": q["query_id"],
                "query": q["query"],
                "category": q["category"],
                "model": self.model_name,
                "method": "vector_only",
                "top_results": [
                    {
                        "id": search_result["ids"][i],
                        "distance": search_result["distances"][i],
                        "content": search_result["documents"][i][:100] + "...",
                        "metadata": search_result["metadatas"][i],
                    }
                    for i in range(min(5, len(search_result["ids"])))
                ],
                "metrics": metrics,
            })

        return results

    def _find_relevant_ids(self, query: dict) -> set[str]:
        """Ground Truth 기준으로 관련 문서 ID를 찾는다."""
        relevant = set()
        for diary in self.diaries:
            is_relevant = False

            # 태그 매칭
            if query.get("relevant_tags"):
                if any(tag in diary["tags"] for tag in query["relevant_tags"]):
                    is_relevant = True

            # 감정 매칭
            if query.get("relevant_moods"):
                if diary["mood"] in query["relevant_moods"]:
                    is_relevant = True

            # 특정 인물 언급 매칭
            if query.get("must_mention"):
                if query["must_mention"] in diary.get("mentioned_people", []):
                    is_relevant = True
                elif query["must_mention"] in diary["content"]:
                    is_relevant = True
                else:
                    is_relevant = False

            if is_relevant:
                relevant.add(diary["entry_id"])

        return relevant


def print_results(results: list[dict]):
    """실험 결과를 보기 좋게 출력한다."""
    print("\n" + "=" * 70)
    print("Phase 1: 순수 벡터 검색 결과")
    print("=" * 70)

    for r in results:
        print(f"\n🔍 [{r['query_id']}] \"{r['query']}\" (카테고리: {r['category']})")
        print(f"   모델: {r['model']}")
        print(f"   Precision@5: {r['metrics']['precision@5']:.2f} | "
              f"Recall@5: {r['metrics']['recall@5']:.2f} | "
              f"MRR: {r['metrics']['mrr']:.2f} | "
              f"Latency: {r['metrics']['latency_ms']:.1f}ms")
        print(f"   상위 3개 결과:")
        for i, top in enumerate(r["top_results"][:3]):
            print(f"   {i+1}. [{top['metadata']['person_name']}] "
                  f"{top['content'][:60]}... "
                  f"(거리: {top['distance']:.4f})")

    # 집계 지표
    all_metrics = [r["metrics"] for r in results]
    agg = aggregate_metrics(all_metrics)
    print(f"\n{'─' * 70}")
    print(f"📊 전체 평균:")
    print(f"   Precision@5: {agg.get('avg_precision@5', 0):.3f}")
    print(f"   Recall@5:    {agg.get('avg_recall@5', 0):.3f}")
    print(f"   MRR:         {agg.get('avg_mrr', 0):.3f}")
    print(f"   Latency:     {agg.get('avg_latency_ms', 0):.1f}ms")
    print("=" * 70)


def run(model_key: str = "default", data_path: str = "data/diaries.json"):
    """Phase 1 실험을 실행한다."""

    # 모델 이름 결정
    model_name = EMBEDDING_MODELS.get(model_key, model_key)

    # Ground Truth 로드
    gt_path = os.path.join(os.path.dirname(data_path), "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # 실험 실행
    exp = VectorSearchExperiment(model_name=model_name)
    exp.load_data(data_path)
    exp.build_index()
    results = exp.run_experiment(queries)

    # 결과 출력
    print_results(results)

    # 결과 저장
    os.makedirs("results", exist_ok=True)
    safe_model = model_key.replace("/", "_")
    output_path = f"results/phase1_{safe_model}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1: 벡터 검색 실험")
    parser.add_argument("--model", default="default",
                        choices=list(EMBEDDING_MODELS.keys()),
                        help="임베딩 모델 (기본: default, ChromaDB 내장)")
    parser.add_argument("--data", default="data/diaries.json",
                        help="일기 데이터 경로")
    args = parser.parse_args()

    run(model_key=args.model, data_path=args.data)
