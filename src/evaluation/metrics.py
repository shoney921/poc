"""
평가 지표 계산 모듈
==================
Precision@K, Recall@K, MRR 등 검색 품질 지표를 계산한다.
"""

import time
from collections import defaultdict


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """
    Precision@K: 상위 K개 결과 중 관련 있는 비율

    Args:
        retrieved_ids: 검색 결과 ID 리스트 (순서 있음)
        relevant_ids: 관련 있는 문서 ID 셋
        k: 상위 K개
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_count / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """
    Recall@K: 전체 관련 문서 중 상위 K개에 포함된 비율
    """
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_count / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """
    MRR (Mean Reciprocal Rank): 첫 번째 관련 결과의 순위 역수
    """
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def evaluate_single_query(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    latency_ms: float,
) -> dict:
    """단일 쿼리에 대한 전체 평가 지표 계산"""
    return {
        "precision@5": precision_at_k(retrieved_ids, relevant_ids, 5),
        "precision@10": precision_at_k(retrieved_ids, relevant_ids, 10),
        "recall@5": recall_at_k(retrieved_ids, relevant_ids, 5),
        "recall@10": recall_at_k(retrieved_ids, relevant_ids, 10),
        "mrr": mrr(retrieved_ids, relevant_ids),
        "latency_ms": latency_ms,
        "num_retrieved": len(retrieved_ids),
        "num_relevant": len(relevant_ids),
    }


def aggregate_metrics(results: list[dict]) -> dict:
    """여러 쿼리의 평가 결과를 집계한다."""
    if not results:
        return {}

    metrics = defaultdict(list)
    for r in results:
        for key, value in r.items():
            if isinstance(value, (int, float)):
                metrics[key].append(value)

    aggregated = {}
    for key, values in metrics.items():
        aggregated[f"avg_{key}"] = sum(values) / len(values)
        aggregated[f"max_{key}"] = max(values)
        aggregated[f"min_{key}"] = min(values)

    return aggregated


class SearchTimer:
    """검색 시간 측정 컨텍스트 매니저"""

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000
