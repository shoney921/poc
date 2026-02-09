#!/usr/bin/env python3
"""
디바이스 매니저 시맨틱 매칭 POC
================================
STT 텍스트 → 디바이스 액션 매칭을 벡터 검색으로 수행한다.

실행 방법:
    # 전체 실험 실행
    python -m src.device_poc.experiment

    # 인터랙티브 모드 (직접 명령어 입력)
    python -m src.device_poc.experiment --interactive

    # 특정 난이도만 테스트
    python -m src.device_poc.experiment --difficulty easy
    python -m src.device_poc.experiment --difficulty medium
    python -m src.device_poc.experiment --difficulty hard

    # Top-K 변경 (기본 5)
    python -m src.device_poc.experiment --top-k 3
"""

import argparse
import json
import os
import re
import time

import chromadb
from rank_bm25 import BM25Okapi

from .devices import DEVICES, get_all_actions, get_device_summary
from .commands import TEST_COMMANDS, get_commands_by_difficulty


# ─────────────────────────────────────────────
# 액션별 동의어/구어체 확장 (검색 품질 향상의 핵심)
# "켜줘"와 "끄기"를 구분하려면 각 액션에 고유한 표현들을 풍부하게 포함시켜야 한다.
# ─────────────────────────────────────────────
ACTION_SYNONYMS = {
    # 조명
    "light_living_on": "불 켜 조명 켜 전등 켜 밝게 불 좀 켜줘 거실 환하게 어두워",
    "light_living_off": "불 꺼 조명 꺼 전등 꺼 거실 어둡게 불 좀 꺼줘 소등",
    "light_living_brightness": "밝기 조절 밝기 변경 밝기 퍼센트 어둡게 밝게 조도",
    "light_living_color": "색상 색깔 분위기 무드등 컬러 조명 색 바꿔",
    "light_bedroom_on": "침실 불 켜 방 불 켜 안방 조명 켜",
    "light_bedroom_off": "침실 불 꺼 방 불 꺼 안방 조명 꺼",
    "light_bedroom_brightness": "침실 밝기 방 밝기",
    "light_bedroom_night": "수면 모드 취침등 잘래 자러 갈게 잠자기 굿나잇 나이트",
    "light_kitchen_on": "주방 불 켜 부엌 조명 켜",
    "light_kitchen_off": "주방 불 꺼 부엌 조명 꺼",
    # 에어컨
    "ac_living_on": "에어컨 켜 시원하게 덥다 더워 냉방 틀어",
    "ac_living_off": "에어컨 꺼 에어컨 끄기 냉방 그만 에어컨 멈춰",
    "ac_living_temp": "온도 설정 온도 변경 도 몇도 시원하게 따뜻하게 춥다 추워",
    "ac_living_mode": "모드 변경 냉방 난방 제습 송풍 에어컨 모드",
    "ac_living_wind": "바람 세기 풍량 풍속 약풍 강풍 바람 세게 바람 약하게",
    "ac_bedroom_on": "침실 에어컨 켜 방 에어컨 켜 방 시원하게",
    "ac_bedroom_off": "침실 에어컨 꺼 방 에어컨 꺼",
    "ac_bedroom_temp": "침실 온도 방 온도 몇 도",
    "ac_bedroom_sleep": "취침 모드 수면 모드 잠잘 때 자기 좋게 잠자기 좋게",
    # TV
    "tv_living_on": "TV 켜 텔레비전 켜 티비 켜",
    "tv_living_off": "TV 꺼 텔레비전 꺼 티비 꺼",
    "tv_living_channel": "채널 변경 채널 바꿔 채널 돌려 번으로",
    "tv_living_volume": "볼륨 소리 크기 조절",
    "tv_living_volume_up": "소리 키워 볼륨 올려 크게 소리 크게",
    "tv_living_volume_down": "소리 줄여 볼륨 내려 작게 소리 작게 시끄러워 조용히",
    "tv_living_mute": "음소거 뮤트 소리 없애 조용",
    "tv_living_input": "입력 소스 HDMI 넷플릭스 유튜브 입력 변경",
    # 스피커
    "speaker_living_play": "음악 재생 노래 틀어 음악 틀어 재생",
    "speaker_living_pause": "일시정지 멈춰 음악 멈춰 잠깐 스톱 정지",
    "speaker_living_next": "다음 곡 넘겨 스킵 다음 노래",
    "speaker_living_volume": "스피커 볼륨 스피커 소리",
    "speaker_living_on": "스피커 켜",
    "speaker_living_off": "스피커 꺼",
    # 블라인드/커튼
    "blind_living_open": "블라인드 열어 블라인드 올려 햇빛 들어오게",
    "blind_living_close": "블라인드 닫아 블라인드 내려 눈부셔 햇빛 차단 가려줘",
    "blind_living_half": "블라인드 반만 반쯤",
    "blind_bedroom_open": "커튼 열어 침실 커튼 열어",
    "blind_bedroom_close": "커튼 닫아 커튼 쳐 침실 커튼 닫아",
    # 로봇청소기
    "vacuum_start": "청소 시작 청소해 바닥 더러워 먼지 청소기 돌려",
    "vacuum_stop": "청소 멈춰 청소 중지 청소기 꺼 충전",
    "vacuum_room": "방만 청소 특정 방 침실만 거실만 주방만",
    "vacuum_mode": "흡입력 세기 터보 강력 약하게",
    # 공기청정기
    "air_purifier_on": "공기청정기 켜 공기 깨끗하게 미세먼지 숨쉬기 힘들어 공기 나빠",
    "air_purifier_off": "공기청정기 꺼",
    "air_purifier_auto": "자동 모드 자동 공기청정기 자동",
    "air_purifier_speed": "공기청정기 세기 팬 속도",
    # 가습기
    "humidifier_on": "가습기 켜 습도 올려 건조해 목 칼칼 촉촉하게",
    "humidifier_off": "가습기 꺼 습도 그만",
    "humidifier_level": "습도 설정 습도 몇 퍼센트",
    # 도어락
    "doorlock_lock": "문 잠가 잠금 나간다 외출 현관 잠금",
    "doorlock_unlock": "문 열어 잠금 해제 열어줘 도어락 열어",
    "doorlock_status": "문 상태 잠겼어 열려있어 현관 상태 확인",
}


# ─────────────────────────────────────────────
# 디바이스 액션 매처
# ─────────────────────────────────────────────

class DeviceActionMatcher:
    """
    STT 텍스트를 디바이스 액션에 매칭하는 시맨틱 검색 엔진.

    3가지 검색 방식을 지원한다:
      1. vector:  순수 벡터 검색 (ChromaDB 임베딩 유사도)
      2. bm25:    순수 키워드 검색 (BM25)
      3. hybrid:  벡터 + BM25 + RRF 융합
    """

    def __init__(self):
        self.client = chromadb.Client()
        self.collection = None          # 기본 컬렉션
        self.collection_enriched = None  # 동의어 확장 컬렉션
        self.actions = []

        # BM25 (기본 / 확장)
        self.bm25 = None
        self.bm25_enriched = None
        self.bm25_action_ids = []

    def build_index(self):
        """디바이스 액션을 인덱싱한다. 기본 + 동의어 확장 두 가지 인덱스를 구축."""
        self.actions = get_all_actions()

        # 동의어 확장된 검색 텍스트 추가
        for a in self.actions:
            synonyms = ACTION_SYNONYMS.get(a["action_id"], "")
            a["enriched_text"] = f"{a['search_text']} {synonyms}"

        metadatas = [{
            "device_id": a["device_id"],
            "device_name": a["device_name"],
            "device_type": a["device_type"],
            "location": a["location"],
            "action_name": a["action_name"],
        } for a in self.actions]

        ids = [a["action_id"] for a in self.actions]

        # ── 기본 ChromaDB 인덱스 ──
        for name in ["device_actions", "device_actions_enriched"]:
            try:
                self.client.delete_collection(name)
            except Exception:
                pass

        self.collection = self.client.create_collection(
            name="device_actions", metadata={"hnsw:space": "cosine"})
        self.collection.add(
            ids=ids,
            documents=[a["search_text"] for a in self.actions],
            metadatas=metadatas,
        )

        # ── 동의어 확장 ChromaDB 인덱스 ──
        self.collection_enriched = self.client.create_collection(
            name="device_actions_enriched", metadata={"hnsw:space": "cosine"})
        self.collection_enriched.add(
            ids=ids,
            documents=[a["enriched_text"] for a in self.actions],
            metadatas=metadatas,
        )

        # ── BM25 (기본) ──
        tokenized = []
        self.bm25_action_ids = []
        for a in self.actions:
            tokens = re.findall(r"[가-힣a-zA-Z0-9]+", a["search_text"])
            tokens = [t for t in tokens if len(t) >= 2]
            tokenized.append(tokens)
            self.bm25_action_ids.append(a["action_id"])
        self.bm25 = BM25Okapi(tokenized)

        # ── BM25 (동의어 확장) ──
        tokenized_enriched = []
        for a in self.actions:
            tokens = re.findall(r"[가-힣a-zA-Z0-9]+", a["enriched_text"])
            tokens = [t for t in tokens if len(t) >= 2]
            tokenized_enriched.append(tokens)
        self.bm25_enriched = BM25Okapi(tokenized_enriched)

        print(f"[디바이스 매처] 인덱싱 완료: {len(self.actions)}개 액션 (기본 + 동의어 확장)")

    def match_vector(self, text: str, top_k: int = 5) -> list[dict]:
        """벡터 검색으로 매칭."""
        results = self.collection.query(
            query_texts=[text],
            n_results=top_k,
        )
        return self._format_results(results["ids"][0], results["distances"][0], results["metadatas"][0])

    def match_bm25(self, text: str, top_k: int = 5) -> list[dict]:
        """BM25 키워드 검색으로 매칭."""
        tokens = re.findall(r"[가-힣a-zA-Z0-9]+", text)
        tokens = [t for t in tokens if len(t) >= 2]
        scores = self.bm25.get_scores(tokens)

        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in indexed[:top_k]:
            if score > 0:
                action_id = self.bm25_action_ids[idx]
                action = self._find_action(action_id)
                results.append({
                    "action_id": action_id,
                    "score": round(score, 4),
                    "device_name": action["device_name"],
                    "action_name": action["action_name"],
                    "location": action["location"],
                    "description": action["description"],
                })
        return results

    def match_hybrid(self, text: str, top_k: int = 5, rrf_k: int = 60) -> list[dict]:
        """하이브리드 검색 (벡터 + BM25 + RRF 융합)."""
        # 벡터 검색
        vec_results = self.collection.query(query_texts=[text], n_results=top_k * 2)
        vec_ids = vec_results["ids"][0]

        # BM25 검색
        tokens = re.findall(r"[가-힣a-zA-Z0-9]+", text)
        tokens = [t for t in tokens if len(t) >= 2]
        bm25_scores = self.bm25.get_scores(tokens)
        bm25_ranked = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)
        bm25_ids = [self.bm25_action_ids[idx] for idx, s in bm25_ranked[:top_k * 2] if s > 0]

        # RRF 융합
        fused_scores = {}
        for rank, action_id in enumerate(vec_ids):
            fused_scores[action_id] = fused_scores.get(action_id, 0) + 1.0 / (rrf_k + rank + 1)
        for rank, action_id in enumerate(bm25_ids):
            fused_scores[action_id] = fused_scores.get(action_id, 0) + 1.0 / (rrf_k + rank + 1)

        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)[:top_k]

        results = []
        for action_id in sorted_ids:
            action = self._find_action(action_id)
            if action:
                results.append({
                    "action_id": action_id,
                    "score": round(fused_scores[action_id], 6),
                    "device_name": action["device_name"],
                    "action_name": action["action_name"],
                    "location": action["location"],
                    "description": action["description"],
                })
        return results

    def match_enriched(self, text: str, top_k: int = 5, rrf_k: int = 60) -> list[dict]:
        """동의어 확장 하이브리드 검색 (확장 벡터 + 확장 BM25 + RRF)."""
        # 확장 벡터 검색
        vec_results = self.collection_enriched.query(query_texts=[text], n_results=top_k * 2)
        vec_ids = vec_results["ids"][0]

        # 확장 BM25 검색
        tokens = re.findall(r"[가-힣a-zA-Z0-9]+", text)
        tokens = [t for t in tokens if len(t) >= 2]
        bm25_scores = self.bm25_enriched.get_scores(tokens)
        bm25_ranked = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)
        bm25_ids = [self.bm25_action_ids[idx] for idx, s in bm25_ranked[:top_k * 2] if s > 0]

        # RRF 융합
        fused_scores = {}
        for rank, action_id in enumerate(vec_ids):
            fused_scores[action_id] = fused_scores.get(action_id, 0) + 1.0 / (rrf_k + rank + 1)
        for rank, action_id in enumerate(bm25_ids):
            fused_scores[action_id] = fused_scores.get(action_id, 0) + 1.0 / (rrf_k + rank + 1)

        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)[:top_k]

        results = []
        for action_id in sorted_ids:
            action = self._find_action(action_id)
            if action:
                results.append({
                    "action_id": action_id,
                    "score": round(fused_scores[action_id], 6),
                    "device_name": action["device_name"],
                    "action_name": action["action_name"],
                    "location": action["location"],
                    "description": action["description"],
                })
        return results

    def _format_results(self, ids, distances, metadatas):
        results = []
        for i, (aid, dist, meta) in enumerate(zip(ids, distances, metadatas)):
            action = self._find_action(aid)
            results.append({
                "action_id": aid,
                "score": round(1 - dist, 4),  # 코사인 거리 → 유사도
                "device_name": meta["device_name"],
                "action_name": meta["action_name"],
                "location": meta["location"],
                "description": action["description"] if action else "",
            })
        return results

    def _find_action(self, action_id: str) -> dict | None:
        for a in self.actions:
            if a["action_id"] == action_id:
                return a
        return None


# ─────────────────────────────────────────────
# 실험 실행
# ─────────────────────────────────────────────

def run_benchmark(matcher: DeviceActionMatcher, commands: list[dict], top_k: int = 5):
    """벤치마크를 실행하고 결과를 반환한다."""
    methods = ["vector", "bm25", "hybrid", "enriched"]
    all_results = {m: [] for m in methods}

    for cmd in commands:
        for method in methods:
            start = time.perf_counter()
            if method == "vector":
                matches = matcher.match_vector(cmd["text"], top_k=top_k)
            elif method == "bm25":
                matches = matcher.match_bm25(cmd["text"], top_k=top_k)
            elif method == "enriched":
                matches = matcher.match_enriched(cmd["text"], top_k=top_k)
            else:
                matches = matcher.match_hybrid(cmd["text"], top_k=top_k)
            elapsed_ms = (time.perf_counter() - start) * 1000

            # 정확도 판정
            top1_correct = matches[0]["action_id"] == cmd["expected_action_id"] if matches else False
            top_k_ids = [m["action_id"] for m in matches]
            top_k_correct = cmd["expected_action_id"] in top_k_ids

            # 순위 찾기
            rank = None
            for i, m in enumerate(matches):
                if m["action_id"] == cmd["expected_action_id"]:
                    rank = i + 1
                    break

            all_results[method].append({
                "command_id": cmd["command_id"],
                "text": cmd["text"],
                "difficulty": cmd["difficulty"],
                "category": cmd["category"],
                "expected": cmd["expected_action_id"],
                "predicted": matches[0]["action_id"] if matches else None,
                "predicted_desc": matches[0]["description"] if matches else "",
                "top1_correct": top1_correct,
                f"top{top_k}_correct": top_k_correct,
                "rank": rank,
                "score": matches[0]["score"] if matches else 0,
                "latency_ms": elapsed_ms,
                "top_matches": matches[:3],
            })

    return all_results


def print_results(all_results: dict, top_k: int = 5):
    """결과를 출력한다."""
    print("\n" + "=" * 80)
    print("  디바이스 매니저 시맨틱 매칭 POC 결과")
    print("=" * 80)

    for method, results in all_results.items():
        label = {"vector": "벡터 검색", "bm25": "BM25 키워드", "hybrid": "하이브리드", "enriched": "동의어 확장"}[method]

        top1_acc = sum(1 for r in results if r["top1_correct"]) / len(results)
        topk_acc = sum(1 for r in results if r.get(f"top{top_k}_correct", False)) / len(results)
        avg_latency = sum(r["latency_ms"] for r in results) / len(results)

        # 난이도별 정확도
        difficulty_acc = {}
        for diff in ["easy", "medium", "hard"]:
            diff_results = [r for r in results if r["difficulty"] == diff]
            if diff_results:
                difficulty_acc[diff] = sum(1 for r in diff_results if r["top1_correct"]) / len(diff_results)

        print(f"\n{'─' * 80}")
        print(f"📊 [{label}]")
        print(f"   Top-1 정확도: {top1_acc:.1%}  ({sum(1 for r in results if r['top1_correct'])}/{len(results)})")
        print(f"   Top-{top_k} 정확도: {topk_acc:.1%}  ({sum(1 for r in results if r.get(f'top{top_k}_correct', False))}/{len(results)})")
        print(f"   평균 응답시간: {avg_latency:.1f}ms")
        print(f"   난이도별 Top-1:")
        for diff, acc in difficulty_acc.items():
            bar = "█" * int(acc * 20)
            label_kr = {"easy": "쉬움  ", "medium": "보통  ", "hard": "어려움"}[diff]
            print(f"     {label_kr}: {bar} {acc:.0%}")

    # 상세 결과 (틀린 것 위주)
    print(f"\n{'═' * 80}")
    print("  오답 분석 (동의어 확장 기준)")
    print("═" * 80)

    hybrid_results = all_results.get("enriched", [])
    wrong = [r for r in hybrid_results if not r["top1_correct"]]

    if not wrong:
        print("  모두 정답! 🎉")
    else:
        for r in wrong:
            expected_action = r["expected"]
            print(f"\n  ❌ [{r['command_id']}] \"{r['text']}\" (난이도: {r['difficulty']})")
            print(f"     정답: {expected_action}")
            print(f"     예측: {r['predicted']} (유사도: {r['score']:.4f})")
            print(f"     정답 순위: {r['rank'] if r['rank'] else 'Top-K 밖'}위")
            print(f"     Top-3 매칭:")
            for i, m in enumerate(r["top_matches"]):
                marker = "✓" if m["action_id"] == expected_action else " "
                print(f"       {i+1}. {marker} [{m['device_name']}] {m['action_name']} "
                      f"- {m['description'][:40]}... ({m['score']:.4f})")

    # 방법별 비교 테이블
    print(f"\n{'═' * 80}")
    print("  방법별 비교 요약")
    print("═" * 80)
    print(f"  {'방법':<15} {'Top-1':>8} {'Top-5':>8} {'Easy':>8} {'Medium':>8} {'Hard':>8} {'Latency':>10}")
    print(f"  {'─' * 15} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 10}")

    for method in ["vector", "bm25", "hybrid", "enriched"]:
        results = all_results[method]
        label = {"vector": "벡터 검색", "bm25": "BM25 키워드", "hybrid": "하이브리드", "enriched": "동의어 확장"}[method]

        top1 = sum(1 for r in results if r["top1_correct"]) / len(results)
        topk = sum(1 for r in results if r.get(f"top{top_k}_correct", False)) / len(results)
        lat = sum(r["latency_ms"] for r in results) / len(results)

        accs = {}
        for diff in ["easy", "medium", "hard"]:
            diff_r = [r for r in results if r["difficulty"] == diff]
            accs[diff] = sum(1 for r in diff_r if r["top1_correct"]) / len(diff_r) if diff_r else 0

        print(f"  {label:<15} {top1:>7.0%} {topk:>7.0%} "
              f"{accs['easy']:>7.0%} {accs['medium']:>7.0%} {accs['hard']:>7.0%} "
              f"{lat:>8.1f}ms")

    print("=" * 80)


def run_interactive(matcher: DeviceActionMatcher, top_k: int = 5):
    """인터랙티브 모드: 사용자가 직접 명령어를 입력한다."""
    print("\n" + "=" * 60)
    print("  디바이스 매니저 인터랙티브 모드")
    print("  명령어를 입력하면 매칭 결과를 보여줍니다.")
    print("  종료: q 또는 quit")
    print("=" * 60)
    print(f"\n등록된 디바이스:")
    print(get_device_summary())
    print()

    while True:
        try:
            text = input("🎤 명령> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not text or text.lower() in ("q", "quit", "exit"):
            break

        print(f"\n  입력: \"{text}\"")

        for method, label in [("vector", "벡터"), ("hybrid", "하이브리드")]:
            if method == "vector":
                matches = matcher.match_vector(text, top_k=top_k)
            else:
                matches = matcher.match_hybrid(text, top_k=top_k)

            print(f"\n  [{label}] 매칭 결과:")
            for i, m in enumerate(matches[:top_k]):
                print(f"    {i+1}. [{m['location']}] {m['device_name']} → {m['action_name']}"
                      f"  (score: {m['score']:.4f})")
                print(f"       {m['description']}")
        print()


def run(difficulty: str = None, top_k: int = 5, interactive: bool = False):
    """실험을 실행한다."""
    matcher = DeviceActionMatcher()
    matcher.build_index()

    if interactive:
        run_interactive(matcher, top_k=top_k)
        return

    commands = get_commands_by_difficulty(difficulty)
    print(f"[실험] 테스트 명령어: {len(commands)}개"
          + (f" (난이도: {difficulty})" if difficulty else " (전체)"))

    all_results = run_benchmark(matcher, commands, top_k=top_k)
    print_results(all_results, top_k=top_k)

    # 결과 저장
    os.makedirs("results", exist_ok=True)
    output_path = "results/device_matching.json"
    # score가 numpy float일 수 있으므로 default 핸들러 추가
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n결과 저장: {output_path}")

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="디바이스 매니저 시맨틱 매칭 POC")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"],
                        help="특정 난이도만 테스트")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Top-K 결과 수 (기본: 5)")
    parser.add_argument("--interactive", action="store_true",
                        help="인터랙티브 모드 (직접 명령어 입력)")
    args = parser.parse_args()

    run(difficulty=args.difficulty, top_k=args.top_k, interactive=args.interactive)
