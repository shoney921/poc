"""
Phase 3: 그래프 기반 검색 실험
==============================
NetworkX로 지식 그래프를 구축하고, 그래프 구조를 활용한 검색을 수행한다.
(외부 서비스 없이 로컬에서 실행 가능)

실행 방법:
    python -m src.phase3_graph.experiment

그래프 통계 확인:
    python -m src.phase3_graph.experiment --stats-only
"""

import argparse
import json
import os
import re
from collections import defaultdict

import networkx as nx

from src.evaluation.metrics import SearchTimer

# ─────────────────────────────────────────────
# 엔티티 추출 규칙 (정규식 + 키워드 기반)
# ─────────────────────────────────────────────

PERSON_NAMES = {
    "김민준": "A", "민준": "A", "민준이": "A", "민준 오빠": "A", "민준 씨": "A",
    "이서연": "B", "서연": "B", "서연이": "B", "서연 씨": "B", "서연 언니": "B",
    "박지호": "C", "지호": "C", "지호 오빠": "C", "지호 씨": "C",
    "최수아": "D", "수아": "D", "수아 씨": "D",
    "정우진": "E", "우진": "E", "우진이": "E", "우진 선생님": "E",
}

PLACE_KEYWORDS = {
    "회사": "회사", "사무실": "회사",
    "카페": "카페 온기", "카페 온기": "카페 온기", "지호 카페": "카페 온기",
    "한강": "한강", "공원": "공원",
    "미술관": "미술관", "전시회": "전시회",
    "대학": "대학교", "연구실": "연구실", "도서관": "도서관",
    "학교": "학교", "교실": "학교",
    "집": "집",
}

EMOTION_KEYWORDS = {
    "행복": "행복", "기쁘": "기쁨", "기쁨": "기쁨",
    "뿌듯": "뿌듯함", "감동": "감동", "설레": "설렘",
    "불안": "불안", "초조": "불안", "걱정": "걱정",
    "스트레스": "스트레스", "힘들": "힘듦",
    "외로": "외로움", "우울": "우울",
    "번아웃": "번아웃", "피곤": "피로",
    "감사": "감사", "편안": "편안함",
}

THEME_KEYWORDS = {
    "코드": "개발", "코딩": "개발", "프로그래밍": "개발", "배포": "개발",
    "버그": "개발", "프레임워크": "개발",
    "디자인": "디자인", "시안": "디자인", "로고": "디자인", "포트폴리오": "디자인",
    "논문": "연구", "데이터 분석": "연구", "통계": "연구", "학회": "연구",
    "수업": "교육", "학생": "교육", "채점": "교육", "학부모": "교육",
    "커피": "커피/카페", "원두": "커피/카페", "메뉴": "커피/카페", "라떼": "커피/카페",
    "게임": "취미", "독서": "취미", "등산": "취미", "요가": "취미",
    "데이트": "연애", "연인": "연애",
}


class KnowledgeGraph:
    """일기 데이터에서 지식 그래프를 구축하고 검색하는 클래스"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.diaries = []

    def load_data(self, data_path: str = "data/diaries.json"):
        """일기 데이터를 로드한다."""
        with open(data_path, "r", encoding="utf-8") as f:
            self.diaries = json.load(f)
        print(f"[Phase 3] 일기 {len(self.diaries)}개 로드 완료")

    def build_graph(self, profiles_path: str = "data/profiles.json"):
        """일기 데이터와 프로필에서 지식 그래프를 구축한다."""

        # 1. 프로필에서 기본 관계 추가
        with open(profiles_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        for person_id, person in profiles["persons"].items():
            self.graph.add_node(
                f"Person:{person['name']}",
                type="Person",
                person_id=person_id,
                name=person["name"],
                job=person["job"],
            )

        for rel in profiles["relationships"]:
            from_name = profiles["persons"][rel["from"]]["name"]
            to_name = profiles["persons"][rel["to"]]["name"]
            self.graph.add_edge(
                f"Person:{from_name}",
                f"Person:{to_name}",
                type=rel["type"],
                closeness=rel["closeness"],
            )
            # 양방향 관계 추가
            self.graph.add_edge(
                f"Person:{to_name}",
                f"Person:{from_name}",
                type=rel["type"],
                closeness=rel["closeness"],
            )

        # 2. 일기에서 엔티티 추출 및 관계 구축
        for diary in self.diaries:
            diary_node = f"Diary:{diary['entry_id']}"
            self.graph.add_node(
                diary_node,
                type="Diary",
                date=diary["date"],
                person_id=diary["person_id"],
                mood=diary["mood"],
                mood_score=diary["mood_score"],
                content_preview=diary["content"][:80],
            )

            # Person → WROTE → Diary
            person_name = diary["person_name"]
            self.graph.add_edge(
                f"Person:{person_name}", diary_node,
                type="WROTE",
            )

            # 언급된 사람: Diary → MENTIONS → Person
            for mentioned in self._extract_persons(diary["content"], diary["person_id"]):
                self.graph.add_edge(
                    diary_node, f"Person:{mentioned}",
                    type="MENTIONS",
                )

            # 장소: Diary → AT_PLACE → Place
            for place in self._extract_places(diary["content"]):
                place_node = f"Place:{place}"
                if not self.graph.has_node(place_node):
                    self.graph.add_node(place_node, type="Place", name=place)
                self.graph.add_edge(diary_node, place_node, type="AT_PLACE")

            # 감정: Diary → FEELS → Emotion
            for emotion in self._extract_emotions(diary["content"]):
                emotion_node = f"Emotion:{emotion}"
                if not self.graph.has_node(emotion_node):
                    self.graph.add_node(emotion_node, type="Emotion", name=emotion)
                self.graph.add_edge(diary_node, emotion_node, type="FEELS")

            # 테마: Diary → HAS_THEME → Theme
            for theme in self._extract_themes(diary["content"]):
                theme_node = f"Theme:{theme}"
                if not self.graph.has_node(theme_node):
                    self.graph.add_node(theme_node, type="Theme", name=theme)
                self.graph.add_edge(diary_node, theme_node, type="HAS_THEME")

            # 공유 이벤트 연결
            if diary.get("shared_event"):
                event_node = f"Event:{diary['shared_event']}"
                if not self.graph.has_node(event_node):
                    self.graph.add_node(event_node, type="Event", name=diary["shared_event"])
                self.graph.add_edge(diary_node, event_node, type="ABOUT_EVENT")
                self.graph.add_edge(
                    f"Person:{person_name}", event_node,
                    type="PARTICIPATED_IN",
                )

        print(f"[Phase 3] 그래프 구축 완료: "
              f"노드 {self.graph.number_of_nodes()}개, "
              f"엣지 {self.graph.number_of_edges()}개")

    def _extract_persons(self, content: str, writer_id: str) -> list[str]:
        """텍스트에서 인물 이름을 추출한다."""
        found = set()
        for keyword, person_id in PERSON_NAMES.items():
            if person_id != writer_id and keyword in content:
                from .profiles_lookup import ID_TO_NAME
                found.add(ID_TO_NAME.get(person_id, keyword))
        return list(found)

    def _extract_places(self, content: str) -> list[str]:
        found = set()
        for keyword, place in PLACE_KEYWORDS.items():
            if keyword in content:
                found.add(place)
        return list(found)

    def _extract_emotions(self, content: str) -> list[str]:
        found = set()
        for keyword, emotion in EMOTION_KEYWORDS.items():
            if keyword in content:
                found.add(emotion)
        return list(found)

    def _extract_themes(self, content: str) -> list[str]:
        found = set()
        for keyword, theme in THEME_KEYWORDS.items():
            if keyword in content:
                found.add(theme)
        return list(found)

    # ─────────────────────────────────────────
    # 그래프 기반 검색/분석 쿼리
    # ─────────────────────────────────────────

    def query_relationship(self, person_a: str, person_b: str) -> dict:
        """두 인물 사이의 관계를 분석한다."""
        node_a = f"Person:{person_a}"
        node_b = f"Person:{person_b}"

        result = {"persons": [person_a, person_b], "direct_relations": [], "shared_events": [],
                  "mutual_mentions": [], "connection_paths": []}

        # 직접 관계
        if self.graph.has_node(node_a) and self.graph.has_node(node_b):
            for _, _, data in self.graph.edges(node_a, data=True):
                pass
            for u, v, data in self.graph.edges(data=True):
                if u == node_a and v == node_b:
                    result["direct_relations"].append(data.get("type", "unknown"))

        # 공유 이벤트
        events_a = {v for _, v, d in self.graph.edges(node_a, data=True) if d.get("type") == "PARTICIPATED_IN"}
        events_b = {v for _, v, d in self.graph.edges(node_b, data=True) if d.get("type") == "PARTICIPATED_IN"}
        shared = events_a & events_b
        for event_node in shared:
            result["shared_events"].append(self.graph.nodes[event_node].get("name", event_node))

        # A가 B를 언급한 일기 / B가 A를 언급한 일기
        for _, diary_node, data in self.graph.edges(node_a, data=True):
            if data.get("type") == "WROTE":
                for _, target, d2 in self.graph.edges(diary_node, data=True):
                    if target == node_b and d2.get("type") == "MENTIONS":
                        diary_data = self.graph.nodes[diary_node]
                        result["mutual_mentions"].append({
                            "writer": person_a,
                            "date": diary_data.get("date", ""),
                            "preview": diary_data.get("content_preview", ""),
                        })

        for _, diary_node, data in self.graph.edges(node_b, data=True):
            if data.get("type") == "WROTE":
                for _, target, d2 in self.graph.edges(diary_node, data=True):
                    if target == node_a and d2.get("type") == "MENTIONS":
                        diary_data = self.graph.nodes[diary_node]
                        result["mutual_mentions"].append({
                            "writer": person_b,
                            "date": diary_data.get("date", ""),
                            "preview": diary_data.get("content_preview", ""),
                        })

        # 최단 경로
        try:
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, node_a, node_b)
            result["connection_paths"] = path
        except nx.NetworkXNoPath:
            result["connection_paths"] = []

        return result

    def query_person_emotions(self, person_name: str) -> dict:
        """특정 인물의 감정 흐름을 분석한다."""
        person_node = f"Person:{person_name}"
        emotion_timeline = []

        for _, diary_node, data in self.graph.edges(person_node, data=True):
            if data.get("type") == "WROTE":
                diary_data = self.graph.nodes[diary_node]
                emotions = []
                for _, emotion_node, d2 in self.graph.edges(diary_node, data=True):
                    if d2.get("type") == "FEELS":
                        emotions.append(self.graph.nodes[emotion_node].get("name", ""))
                emotion_timeline.append({
                    "date": diary_data.get("date", ""),
                    "mood": diary_data.get("mood", ""),
                    "mood_score": diary_data.get("mood_score", 3),
                    "emotions": emotions,
                })

        emotion_timeline.sort(key=lambda x: x["date"])

        # 감정 통계
        emotion_counts = defaultdict(int)
        mood_scores = []
        for entry in emotion_timeline:
            for e in entry["emotions"]:
                emotion_counts[e] += 1
            mood_scores.append(entry["mood_score"])

        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0

        return {
            "person": person_name,
            "timeline": emotion_timeline,
            "emotion_distribution": dict(emotion_counts),
            "avg_mood_score": round(avg_mood, 2),
            "total_entries": len(emotion_timeline),
        }

    def query_common_themes(self) -> dict:
        """모든 인물에 걸친 공통 테마를 분석한다."""
        person_themes = defaultdict(lambda: defaultdict(int))

        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "Diary":
                person_id = data.get("person_id", "")
                for _, theme_node, edge_data in self.graph.edges(node, data=True):
                    if edge_data.get("type") == "HAS_THEME":
                        theme_name = self.graph.nodes[theme_node].get("name", "")
                        person_themes[person_id][theme_name] += 1

        # 전체 테마 집계
        all_themes = defaultdict(int)
        for person_id, themes in person_themes.items():
            for theme, count in themes.items():
                all_themes[theme] += count

        # 2명 이상이 공유하는 테마
        common_themes = {}
        for theme in all_themes:
            shared_by = [pid for pid, themes in person_themes.items() if theme in themes]
            if len(shared_by) >= 2:
                common_themes[theme] = {
                    "total_count": all_themes[theme],
                    "shared_by": shared_by,
                    "per_person": {pid: person_themes[pid][theme] for pid in shared_by},
                }

        return {
            "common_themes": common_themes,
            "per_person_themes": {pid: dict(themes) for pid, themes in person_themes.items()},
            "overall_ranking": sorted(all_themes.items(), key=lambda x: x[1], reverse=True),
        }

    def query_event_perspectives(self, event_name: str) -> dict:
        """특정 이벤트에 대한 각 인물의 시각을 모은다."""
        event_node = f"Event:{event_name}"
        if not self.graph.has_node(event_node):
            return {"event": event_name, "error": "이벤트를 찾을 수 없습니다.", "perspectives": []}

        perspectives = []
        for diary_node, _, data in self.graph.in_edges(event_node, data=True):
            if data.get("type") == "ABOUT_EVENT":
                diary_data = self.graph.nodes[diary_node]
                # 작성자 찾기
                writer = ""
                for person_node, _, d2 in self.graph.in_edges(diary_node, data=True):
                    if d2.get("type") == "WROTE":
                        writer = self.graph.nodes[person_node].get("name", "")
                        break

                # 감정 찾기
                emotions = []
                for _, emotion_node, d2 in self.graph.edges(diary_node, data=True):
                    if d2.get("type") == "FEELS":
                        emotions.append(self.graph.nodes[emotion_node].get("name", ""))

                # 원본 내용 가져오기
                entry_id = diary_node.replace("Diary:", "")
                full_content = ""
                for d in self.diaries:
                    if d["entry_id"] == entry_id:
                        full_content = d["content"]
                        break

                perspectives.append({
                    "writer": writer,
                    "date": diary_data.get("date", ""),
                    "mood": diary_data.get("mood", ""),
                    "emotions": emotions,
                    "content": full_content,
                })

        return {"event": event_name, "perspectives": perspectives}

    def query_most_mentioned(self) -> list[dict]:
        """가장 많이 언급되는 인물 순위."""
        mention_count = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            if data.get("type") == "MENTIONS" and self.graph.nodes[v].get("type") == "Person":
                name = self.graph.nodes[v].get("name", v)
                mention_count[name] += 1

        ranking = sorted(mention_count.items(), key=lambda x: x[1], reverse=True)
        return [{"person": name, "mentions": count} for name, count in ranking]

    def get_stats(self) -> dict:
        """그래프 통계를 반환한다."""
        type_counts = defaultdict(int)
        for _, data in self.graph.nodes(data=True):
            type_counts[data.get("type", "unknown")] += 1

        edge_type_counts = defaultdict(int)
        for _, _, data in self.graph.edges(data=True):
            edge_type_counts[data.get("type", "unknown")] += 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": dict(type_counts),
            "edge_types": dict(edge_type_counts),
        }


def print_results(kg: KnowledgeGraph):
    """Phase 3 실험 결과를 출력한다."""
    print("\n" + "=" * 70)
    print("Phase 3: 그래프 기반 검색 결과")
    print("=" * 70)

    # 그래프 통계
    stats = kg.get_stats()
    print(f"\n📊 그래프 통계:")
    print(f"   노드: {stats['total_nodes']}개, 엣지: {stats['total_edges']}개")
    print(f"   노드 타입: {stats['node_types']}")
    print(f"   엣지 타입: {stats['edge_types']}")

    # 실험 1: 관계 분석
    print(f"\n{'─' * 70}")
    print("🔗 실험 1: 인물 관계 분석")
    test_pairs = [("김민준", "이서연"), ("김민준", "박지호"), ("최수아", "정우진")]
    for a, b in test_pairs:
        rel = kg.query_relationship(a, b)
        print(f"\n  [{a}] ↔ [{b}]")
        print(f"  직접 관계: {rel['direct_relations']}")
        print(f"  공유 이벤트: {rel['shared_events']}")
        print(f"  상호 언급: {len(rel['mutual_mentions'])}건")
        if rel["connection_paths"]:
            path_str = " → ".join(p.split(":")[-1] for p in rel["connection_paths"])
            print(f"  연결 경로: {path_str}")

    # 실험 2: 감정 흐름 분석
    print(f"\n{'─' * 70}")
    print("💭 실험 2: 감정 흐름 분석")
    for name in ["김민준", "최수아"]:
        emotions = kg.query_person_emotions(name)
        print(f"\n  [{name}] 감정 분석:")
        print(f"  평균 기분 점수: {emotions['avg_mood_score']}/5")
        print(f"  감정 분포: {emotions['emotion_distribution']}")
        print(f"  일기 수: {emotions['total_entries']}개")

    # 실험 3: 공통 테마
    print(f"\n{'─' * 70}")
    print("🏷️  실험 3: 공통 테마 분석")
    themes = kg.query_common_themes()
    for theme, info in sorted(themes["common_themes"].items(),
                               key=lambda x: x[1]["total_count"], reverse=True)[:8]:
        print(f"  {theme}: {info['total_count']}회 (참여: {', '.join(info['shared_by'])})")

    # 실험 4: 이벤트 다시점 분석
    print(f"\n{'─' * 70}")
    print("👁️  실험 4: 이벤트 다시점 분석")
    for event_name in ["봄 소풍", "서연이네 전시회"]:
        perspectives = kg.query_event_perspectives(event_name)
        print(f"\n  이벤트: [{perspectives['event']}]")
        for p in perspectives["perspectives"]:
            print(f"    {p['writer']} ({p['mood']}): {p['content'][:60]}...")

    # 실험 5: 인물 언급 순위
    print(f"\n{'─' * 70}")
    print("👤 실험 5: 인물 언급 순위")
    ranking = kg.query_most_mentioned()
    for r in ranking:
        bar = "█" * r["mentions"]
        print(f"  {r['person']}: {bar} ({r['mentions']}회)")

    print("\n" + "=" * 70)


def run(data_path: str = "data/diaries.json", stats_only: bool = False):
    """Phase 3 실험을 실행한다."""
    profiles_path = os.path.join(os.path.dirname(data_path), "profiles.json")

    kg = KnowledgeGraph()
    kg.load_data(data_path)
    kg.build_graph(profiles_path)

    if stats_only:
        stats = kg.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return

    print_results(kg)

    # 결과 저장
    os.makedirs("results", exist_ok=True)
    output = {
        "stats": kg.get_stats(),
        "relationship_김민준_이서연": kg.query_relationship("김민준", "이서연"),
        "emotions_김민준": kg.query_person_emotions("김민준"),
        "common_themes": kg.query_common_themes(),
        "event_봄소풍": kg.query_event_perspectives("봄 소풍"),
        "mention_ranking": kg.query_most_mentioned(),
    }
    output_path = "results/phase3_graph.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n결과 저장: {output_path}")

    return kg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3: 그래프 기반 검색 실험")
    parser.add_argument("--data", default="data/diaries.json", help="일기 데이터 경로")
    parser.add_argument("--stats-only", action="store_true", help="그래프 통계만 출력")
    args = parser.parse_args()

    run(data_path=args.data, stats_only=args.stats_only)
