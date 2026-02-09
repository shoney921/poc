#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  의미 기반 검색 POC - 전체 실험 실행 스크립트
═══════════════════════════════════════════════════════════════

실행 방법:

  1) 패키지 설치 (최초 1회):
     pip install -r requirements.txt

  2) 전체 실험 실행:
     python run_experiments.py

  3) 개별 단계만 실행:
     python run_experiments.py --phase 0     # 데이터 생성만
     python run_experiments.py --phase 1     # Phase 1: 벡터 검색
     python run_experiments.py --phase 2     # Phase 2: 하이브리드 검색
     python run_experiments.py --phase 3     # Phase 3: 그래프 기반 검색

  4) 옵션:
     python run_experiments.py --phase 1 --model bge-m3    # 다른 임베딩 모델
     python run_experiments.py --phase 2 --alpha 0.7       # 벡터 가중치 변경
     python run_experiments.py --phase 2 --with-filters    # 메타데이터 필터 실험

═══════════════════════════════════════════════════════════════
"""

import argparse
import json
import os
import sys
import time


def run_phase0():
    """Step 0: 합성 데이터 생성"""
    print("\n" + "▓" * 70)
    print("  Step 0: 합성 데이터 생성")
    print("▓" * 70)

    from src.data_generation.generate import save_data
    save_data("data")


def run_phase1(model: str = "minilm"):
    """Step 1: 순수 벡터 검색 실험"""
    print("\n" + "▓" * 70)
    print(f"  Phase 1: 순수 벡터 검색 (모델: {model})")
    print("▓" * 70)

    from src.phase1_vector.experiment import run
    return run(model_key=model)


def run_phase2(alpha: float = 0.5, with_filters: bool = False):
    """Step 2: 하이브리드 검색 실험"""
    print("\n" + "▓" * 70)
    print(f"  Phase 2: 하이브리드 검색 (alpha={alpha})")
    print("▓" * 70)

    from src.phase2_hybrid.experiment import run
    return run(alpha=alpha, with_filters=with_filters)


def run_phase3():
    """Step 3: 그래프 기반 검색 실험"""
    print("\n" + "▓" * 70)
    print("  Phase 3: 그래프 기반 검색")
    print("▓" * 70)

    from src.phase3_graph.experiment import run
    return run()


def print_comparison(phase1_results, phase2_results):
    """Phase 1 vs Phase 2 비교 출력"""
    if not phase1_results or not phase2_results:
        return

    print("\n" + "=" * 70)
    print("  Phase 1 vs Phase 2 비교")
    print("=" * 70)

    from src.evaluation.metrics import aggregate_metrics

    p1_metrics = aggregate_metrics([r["metrics"] for r in phase1_results])
    # Phase 2에서 RRF 결과만 비교
    p2_rrf = [r for r in phase2_results if r.get("method") == "hybrid_rrf"]
    p2_metrics = aggregate_metrics([r["metrics"] for r in p2_rrf]) if p2_rrf else {}

    headers = ["지표", "Phase 1 (Vector)", "Phase 2 (Hybrid)", "개선율"]
    rows = []
    for metric_key in ["precision@5", "recall@5", "mrr", "latency_ms"]:
        p1_val = p1_metrics.get(f"avg_{metric_key}", 0)
        p2_val = p2_metrics.get(f"avg_{metric_key}", 0)
        if p1_val > 0:
            improvement = ((p2_val - p1_val) / p1_val) * 100
            imp_str = f"{improvement:+.1f}%"
        else:
            imp_str = "N/A"
        rows.append([metric_key, f"{p1_val:.3f}", f"{p2_val:.3f}", imp_str])

    # 간단한 테이블 출력
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(4)]
    fmt = "  " + " | ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print("  " + "-+-".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt.format(*row))

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="의미 기반 검색 POC - 실험 실행기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--phase", type=int, default=None,
                        choices=[0, 1, 2, 3],
                        help="실행할 단계 (미지정 시 전체 실행)")
    parser.add_argument("--model", default="default",
                        help="Phase 1 임베딩 모델 (default, minilm, mpnet, bge-m3)")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="Phase 2 벡터 가중치 (0.0~1.0)")
    parser.add_argument("--with-filters", action="store_true",
                        help="Phase 2 메타데이터 필터 실험 포함")
    args = parser.parse_args()

    start_time = time.time()

    print("═" * 70)
    print("  의미 기반 검색 POC 실험")
    print("═" * 70)

    # 데이터 확인
    if not os.path.exists("data/diaries.json"):
        if args.phase is not None and args.phase > 0:
            print("[!] 데이터가 없습니다. 먼저 데이터를 생성합니다...")
        run_phase0()

    if args.phase == 0:
        run_phase0()
        return

    phase1_results = None
    phase2_results = None

    if args.phase is None or args.phase == 1:
        phase1_results = run_phase1(model=args.model)

    if args.phase is None or args.phase == 2:
        phase2_results = run_phase2(alpha=args.alpha, with_filters=args.with_filters)

    if args.phase is None or args.phase == 3:
        run_phase3()

    # 전체 실행 시 비교 출력
    if args.phase is None and phase1_results and phase2_results:
        print_comparison(phase1_results, phase2_results)

    elapsed = time.time() - start_time
    print(f"\n총 실행 시간: {elapsed:.1f}초")


if __name__ == "__main__":
    main()
