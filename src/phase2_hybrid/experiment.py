"""
Phase 2: 하이브리드 검색 실험 (Vector + BM25 + 메타데이터 필터)
===============================================================
벡터 검색에 BM25 키워드 검색과 메타데이터 필터를 결합하여 검색 품질 향상을 측정.

실행 방법:
    python -m src.phase2_hybrid.experiment

RRF 가중치 변경:
    python -m src.phase2_hybrid.experiment --alpha 0.7

메타데이터 필터 실험 포함:
    python -m src.phase2_hybrid.experiment --with-filters
"""

import argparse
import json
import os
import re

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from src.evaluation.metrics import SearchTimer, evaluate_single_query, aggregate_metrics


def simple_tokenize(text: str) -> list[str]:
    """한국어 텍스트를 간단히 토큰화한다 (공백 + 2~4글자 n-gram)."""
    # 공백 기반 분리
    words = re.findall(r"[가-힣a-zA-Z0-9]+", text)
    # 2글자 이상 단어만 유지
    tokens = [w for w in words if len(w) >= 2]
    return tokens


class HybridSearchExperiment:
    """Phase 2: 하이브리드 검색 실험 클래스"""

    def __init__(self, model_name: str = "default", alpha: float = 0.5):
        """
        Args:
            model_name: 임베딩 모델 이름 ("default" = ChromaDB 내장)
            alpha: 벡터 검색 가중치 (1-alpha = BM25 가중치)
                   alpha=1.0 → 순수 벡터, alpha=0.0 → 순수 BM25
        """
        self.model_name = model_name
        self.alpha = alpha

        # ChromaDB
        self.client = chromadb.Client()
        self.embedding_fn = None
        if model_name != "default":
            try:
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=model_name
                )
            except Exception as e:
                print(f"[!] 모델 로드 실패, 기본 임베딩 사용: {e}")
        self.collection = None

        # BM25
        self.bm25 = None
        self.bm25_doc_ids = []

        self.diaries = []

    def load_data(self, data_path: str = "data/diaries.json"):
        """일기 데이터를 로드한다."""
        with open(data_path, "r", encoding="utf-8") as f:
            self.diaries = json.load(f)
        print(f"[Phase 2] 일기 {len(self.diaries)}개 로드 완료")

    def build_index(self):
        """벡터 인덱스와 BM25 인덱스를 동시에 구축한다."""
        # ── ChromaDB 벡터 인덱스 ──
        try:
            self.client.delete_collection("diaries_hybrid")
        except Exception:
            pass

        create_kwargs = {
            "name": "diaries_hybrid",
            "metadata": {"hnsw:space": "cosine"},
        }
        if self.embedding_fn is not None:
            create_kwargs["embedding_function"] = self.embedding_fn
        self.collection = self.client.create_collection(**create_kwargs)

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

        # ── BM25 키워드 인덱스 ──
        tokenized_corpus = []
        self.bm25_doc_ids = []
        for d in self.diaries:
            tokens = simple_tokenize(d["content"])
            tokenized_corpus.append(tokens)
            self.bm25_doc_ids.append(d["entry_id"])

        self.bm25 = BM25Okapi(tokenized_corpus)

        print(f"[Phase 2] 인덱싱 완료 (벡터 + BM25)")

    def search_vector(self, query: str, n_results: int = 20, where: dict = None) -> list[tuple[str, float]]:
        """벡터 검색 → (doc_id, score) 리스트"""
        kwargs = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)
        pairs = []
        for doc_id, distance in zip(results["ids"][0], results["distances"][0]):
            score = 1 - distance  # 코사인 거리 → 유사도
            pairs.append((doc_id, score))
        return pairs

    def search_bm25(self, query: str, n_results: int = 20) -> list[tuple[str, float]]:
        """BM25 검색 → (doc_id, score) 리스트"""
        tokens = simple_tokenize(query)
        scores = self.bm25.get_scores(tokens)
        # 상위 N개 추출
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        pairs = []
        for idx, score in indexed_scores[:n_results]:
            if score > 0:
                pairs.append((self.bm25_doc_ids[idx], score))
        return pairs

    def reciprocal_rank_fusion(
        self,
        results_lists: list[list[tuple[str, float]]],
        k: int = 60,
    ) -> list[str]:
        """
        Reciprocal Rank Fusion (RRF) — 여러 검색 결과를 융합한다.

        Args:
            results_lists: 각 검색기의 (doc_id, score) 리스트
            k: RRF 파라미터 (기본 60)

        Returns:
            융합된 doc_id 리스트 (점수 내림차순)
        """
        fused_scores = {}
        for results in results_lists:
            for rank, (doc_id, _) in enumerate(results):
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = 0.0
                fused_scores[doc_id] += 1.0 / (k + rank + 1)

        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        return sorted_ids

    def weighted_fusion(
        self,
        vector_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]],
    ) -> list[str]:
        """
        가중 합산 방식 융합.

        alpha가 벡터 가중치, (1-alpha)가 BM25 가중치.
        """
        scores = {}

        # 벡터 점수 정규화 (0~1)
        if vector_results:
            max_v = max(s for _, s in vector_results) or 1
            for doc_id, score in vector_results:
                scores[doc_id] = self.alpha * (score / max_v)

        # BM25 점수 정규화 (0~1)
        if bm25_results:
            max_b = max(s for _, s in bm25_results) or 1
            for doc_id, score in bm25_results:
                normalized = (1 - self.alpha) * (score / max_b)
                scores[doc_id] = scores.get(doc_id, 0) + normalized

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_ids

    def search_hybrid(
        self,
        query: str,
        n_results: int = 10,
        fusion: str = "rrf",
        where: dict = None,
    ) -> dict:
        """
        하이브리드 검색을 수행한다.

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            fusion: 융합 방법 ("rrf" 또는 "weighted")
            where: 메타데이터 필터

        Returns:
            dict: 검색 결과
        """
        with SearchTimer() as timer:
            # 두 검색기 실행
            vector_results = self.search_vector(query, n_results=20, where=where)
            bm25_results = self.search_bm25(query, n_results=20)

            # 메타데이터 필터가 있으면 BM25 결과도 필터링
            if where:
                filtered_ids = {r[0] for r in vector_results}
                # 벡터 검색의 필터 결과에 있는 것만 BM25에서도 유지
                diary_map = {d["entry_id"]: d for d in self.diaries}
                bm25_filtered = []
                for doc_id, score in bm25_results:
                    if doc_id in filtered_ids or self._matches_filter(diary_map.get(doc_id, {}), where):
                        bm25_filtered.append((doc_id, score))
                bm25_results = bm25_filtered

            # 융합
            if fusion == "rrf":
                merged_ids = self.reciprocal_rank_fusion([vector_results, bm25_results])
            else:
                merged_ids = self.weighted_fusion(vector_results, bm25_results)

        # 결과 조합
        merged_ids = merged_ids[:n_results]
        diary_map = {d["entry_id"]: d for d in self.diaries}

        return {
            "ids": merged_ids,
            "documents": [diary_map[did]["content"] for did in merged_ids if did in diary_map],
            "metadatas": [
                {
                    "person_name": diary_map[did]["person_name"],
                    "date": diary_map[did]["date"],
                    "mood": diary_map[did]["mood"],
                }
                for did in merged_ids if did in diary_map
            ],
            "latency_ms": timer.elapsed_ms,
            "fusion": fusion,
        }

    def _matches_filter(self, diary: dict, where: dict) -> bool:
        """일기가 필터 조건에 맞는지 확인한다."""
        if not diary:
            return False
        for key, value in where.items():
            if key.startswith("$"):
                continue
            if diary.get(key) != value:
                return False
        return True

    def run_experiment(self, queries: list[dict]) -> list[dict]:
        """전체 실험을 실행한다."""
        results = []

        for fusion_method in ["rrf", "weighted"]:
            for q in queries:
                search_result = self.search_hybrid(
                    q["query"], n_results=10, fusion=fusion_method
                )

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
                    "method": f"hybrid_{fusion_method}",
                    "alpha": self.alpha,
                    "top_results": [
                        {
                            "id": search_result["ids"][i],
                            "content": search_result["documents"][i][:100] + "..."
                                if i < len(search_result["documents"]) else "",
                            "metadata": search_result["metadatas"][i]
                                if i < len(search_result["metadatas"]) else {},
                        }
                        for i in range(min(5, len(search_result["ids"])))
                    ],
                    "metrics": metrics,
                })

        return results

    def run_filter_experiment(self, queries: list[dict]) -> list[dict]:
        """메타데이터 필터를 활용한 추가 실험."""
        filter_scenarios = [
            {"name": "인물필터_A", "query": "스트레스 받는 날", "where": {"person_id": "A"}},
            {"name": "인물필터_D", "query": "논문 관련 고민", "where": {"person_id": "D"}},
            {"name": "감정필터_부정", "query": "힘든 하루", "where": {"mood_score": {"$lte": 2}}},
            {"name": "감정필터_긍정", "query": "좋았던 하루", "where": {"mood_score": {"$gte": 4}}},
        ]

        results = []
        for scenario in filter_scenarios:
            search_result = self.search_hybrid(
                scenario["query"],
                n_results=5,
                where=scenario["where"],
            )

            results.append({
                "scenario": scenario["name"],
                "query": scenario["query"],
                "filter": str(scenario["where"]),
                "results": [
                    {
                        "id": search_result["ids"][i],
                        "content": search_result["documents"][i][:80] + "..."
                            if i < len(search_result["documents"]) else "",
                        "metadata": search_result["metadatas"][i]
                            if i < len(search_result["metadatas"]) else {},
                    }
                    for i in range(min(5, len(search_result["ids"])))
                ],
                "latency_ms": search_result["latency_ms"],
            })

        return results

    def _find_relevant_ids(self, query: dict) -> set[str]:
        """Ground Truth 기준 관련 문서 찾기 (Phase 1과 동일 로직)."""
        relevant = set()
        for diary in self.diaries:
            is_relevant = False
            if query.get("relevant_tags"):
                if any(tag in diary["tags"] for tag in query["relevant_tags"]):
                    is_relevant = True
            if query.get("relevant_moods"):
                if diary["mood"] in query["relevant_moods"]:
                    is_relevant = True
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


def print_results(results: list[dict], filter_results: list[dict] = None):
    """실험 결과를 출력한다."""
    print("\n" + "=" * 70)
    print("Phase 2: 하이브리드 검색 결과")
    print("=" * 70)

    # 융합 방법별 집계
    for method in ["hybrid_rrf", "hybrid_weighted"]:
        method_results = [r for r in results if r["method"] == method]
        if not method_results:
            continue

        agg = aggregate_metrics([r["metrics"] for r in method_results])
        label = "RRF" if "rrf" in method else "Weighted"
        print(f"\n📊 [{label} 융합] 전체 평균:")
        print(f"   Precision@5: {agg.get('avg_precision@5', 0):.3f}")
        print(f"   Recall@5:    {agg.get('avg_recall@5', 0):.3f}")
        print(f"   MRR:         {agg.get('avg_mrr', 0):.3f}")
        print(f"   Latency:     {agg.get('avg_latency_ms', 0):.1f}ms")

    # 쿼리별 상세 (RRF만)
    rrf_results = [r for r in results if r["method"] == "hybrid_rrf"]
    print(f"\n{'─' * 70}")
    print("🔍 RRF 융합 - 쿼리별 상세:")
    for r in rrf_results:
        print(f"\n  [{r['query_id']}] \"{r['query']}\"")
        print(f"  P@5: {r['metrics']['precision@5']:.2f} | "
              f"R@5: {r['metrics']['recall@5']:.2f} | "
              f"MRR: {r['metrics']['mrr']:.2f}")
        for i, top in enumerate(r["top_results"][:3]):
            meta = top.get("metadata", {})
            print(f"    {i+1}. [{meta.get('person_name', '?')}] {top['content'][:50]}...")

    # 필터 실험 결과
    if filter_results:
        print(f"\n{'─' * 70}")
        print("🏷️  메타데이터 필터 실험:")
        for fr in filter_results:
            print(f"\n  [{fr['scenario']}] \"{fr['query']}\" (필터: {fr['filter']})")
            for i, top in enumerate(fr["results"][:3]):
                meta = top.get("metadata", {})
                print(f"    {i+1}. [{meta.get('person_name', '?')}|{meta.get('mood', '?')}] "
                      f"{top['content'][:50]}...")

    print("=" * 70)


def run(alpha: float = 0.5, with_filters: bool = False, data_path: str = "data/diaries.json"):
    """Phase 2 실험을 실행한다."""

    gt_path = os.path.join(os.path.dirname(data_path), "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    exp = HybridSearchExperiment(alpha=alpha)
    exp.load_data(data_path)
    exp.build_index()

    results = exp.run_experiment(queries)
    filter_results = exp.run_filter_experiment(queries) if with_filters else None

    print_results(results, filter_results)

    os.makedirs("results", exist_ok=True)
    output_path = "results/phase2_hybrid.json"
    output = {"search_results": results}
    if filter_results:
        output["filter_results"] = filter_results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2: 하이브리드 검색 실험")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="벡터 가중치 (0.0~1.0, 기본: 0.5)")
    parser.add_argument("--with-filters", action="store_true",
                        help="메타데이터 필터 실험 포함")
    parser.add_argument("--data", default="data/diaries.json",
                        help="일기 데이터 경로")
    args = parser.parse_args()

    run(alpha=args.alpha, with_filters=args.with_filters, data_path=args.data)
