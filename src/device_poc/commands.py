"""
STT 명령어 테스트 셋
====================
사용자가 음성으로 말한 뒤 STT로 변환된 텍스트를 시뮬레이션한다.
실제 음성 명령처럼 구어체, 줄임말, 다양한 표현을 포함한다.

각 명령어에는 정답(expected_action_id)이 포함되어 있어 정확도를 측정할 수 있다.

난이도:
  - easy:   디바이스명 + 액션이 명확하게 포함
  - medium: 간접적 표현, 동의어, 생략
  - hard:   맥락 의존, 비유, 복합 명령, 모호한 표현
"""

TEST_COMMANDS = [
    # ═══════════════════════════════════════════
    # 난이도 EASY: 직접적인 명령
    # ═══════════════════════════════════════════
    {
        "command_id": "E01",
        "text": "거실 조명 켜줘",
        "expected_action_id": "light_living_on",
        "difficulty": "easy",
        "category": "조명",
    },
    {
        "command_id": "E02",
        "text": "거실 조명 꺼줘",
        "expected_action_id": "light_living_off",
        "difficulty": "easy",
        "category": "조명",
    },
    {
        "command_id": "E03",
        "text": "침실 에어컨 켜줘",
        "expected_action_id": "ac_bedroom_on",
        "difficulty": "easy",
        "category": "에어컨",
    },
    {
        "command_id": "E04",
        "text": "거실 TV 켜줘",
        "expected_action_id": "tv_living_on",
        "difficulty": "easy",
        "category": "TV",
    },
    {
        "command_id": "E05",
        "text": "로봇 청소기 시작해줘",
        "expected_action_id": "vacuum_start",
        "difficulty": "easy",
        "category": "청소기",
    },
    {
        "command_id": "E06",
        "text": "현관문 잠가줘",
        "expected_action_id": "doorlock_lock",
        "difficulty": "easy",
        "category": "도어락",
    },
    {
        "command_id": "E07",
        "text": "공기청정기 켜줘",
        "expected_action_id": "air_purifier_on",
        "difficulty": "easy",
        "category": "공기청정기",
    },
    {
        "command_id": "E08",
        "text": "거실 블라인드 열어줘",
        "expected_action_id": "blind_living_open",
        "difficulty": "easy",
        "category": "블라인드",
    },
    {
        "command_id": "E09",
        "text": "가습기 꺼줘",
        "expected_action_id": "humidifier_off",
        "difficulty": "easy",
        "category": "가습기",
    },
    {
        "command_id": "E10",
        "text": "거실 에어컨 온도 24도로 설정해줘",
        "expected_action_id": "ac_living_temp",
        "difficulty": "easy",
        "category": "에어컨",
    },

    # ═══════════════════════════════════════════
    # 난이도 MEDIUM: 동의어, 간접 표현, 줄임말
    # ═══════════════════════════════════════════
    {
        "command_id": "M01",
        "text": "불 좀 켜",
        "expected_action_id": "light_living_on",
        "difficulty": "medium",
        "category": "조명",
        "note": "'불' = 조명, 위치 생략 → 기본값 거실",
    },
    {
        "command_id": "M02",
        "text": "에어컨 좀 틀어줘",
        "expected_action_id": "ac_living_on",
        "difficulty": "medium",
        "category": "에어컨",
        "note": "'틀어줘' = 켜줘",
    },
    {
        "command_id": "M03",
        "text": "TV 소리 좀 줄여줘",
        "expected_action_id": "tv_living_volume_down",
        "difficulty": "medium",
        "category": "TV",
        "note": "'소리 줄여줘' = 볼륨 내리기",
    },
    {
        "command_id": "M04",
        "text": "에어컨 바람 세게 해줘",
        "expected_action_id": "ac_living_wind",
        "difficulty": "medium",
        "category": "에어컨",
        "note": "'바람 세게' = 풍량 조절",
    },
    {
        "command_id": "M05",
        "text": "청소 좀 해줘",
        "expected_action_id": "vacuum_start",
        "difficulty": "medium",
        "category": "청소기",
        "note": "'청소 해줘' = 로봇 청소기 시작",
    },
    {
        "command_id": "M06",
        "text": "문 열어줘",
        "expected_action_id": "doorlock_unlock",
        "difficulty": "medium",
        "category": "도어락",
        "note": "'문 열어줘' = 도어락 잠금 해제",
    },
    {
        "command_id": "M07",
        "text": "음악 틀어줘",
        "expected_action_id": "speaker_living_play",
        "difficulty": "medium",
        "category": "스피커",
        "note": "'음악 틀어줘' = 스피커 음악 재생",
    },
    {
        "command_id": "M08",
        "text": "커튼 쳐줘",
        "expected_action_id": "blind_bedroom_close",
        "difficulty": "medium",
        "category": "블라인드",
        "note": "'커튼 쳐줘' = 커튼 닫기",
    },
    {
        "command_id": "M09",
        "text": "거실 밝기 50으로 해줘",
        "expected_action_id": "light_living_brightness",
        "difficulty": "medium",
        "category": "조명",
        "note": "'밝기' 만으로 조명 밝기 조절 파악",
    },
    {
        "command_id": "M10",
        "text": "채널 9번으로 돌려줘",
        "expected_action_id": "tv_living_channel",
        "difficulty": "medium",
        "category": "TV",
        "note": "'채널 돌려줘' = TV 채널 변경",
    },
    {
        "command_id": "M11",
        "text": "집 안 공기 좀 깨끗하게 해줘",
        "expected_action_id": "air_purifier_on",
        "difficulty": "medium",
        "category": "공기청정기",
        "note": "'공기 깨끗하게' = 공기청정기 켜기",
    },
    {
        "command_id": "M12",
        "text": "방 습도 좀 올려줘",
        "expected_action_id": "humidifier_on",
        "difficulty": "medium",
        "category": "가습기",
        "note": "'습도 올려줘' = 가습기 켜기",
    },
    {
        "command_id": "M13",
        "text": "TV 음소거 해줘",
        "expected_action_id": "tv_living_mute",
        "difficulty": "medium",
        "category": "TV",
    },
    {
        "command_id": "M14",
        "text": "에어컨 냉방으로 바꿔줘",
        "expected_action_id": "ac_living_mode",
        "difficulty": "medium",
        "category": "에어컨",
    },
    {
        "command_id": "M15",
        "text": "노래 다음 곡으로 넘겨줘",
        "expected_action_id": "speaker_living_next",
        "difficulty": "medium",
        "category": "스피커",
        "note": "'노래 다음 곡' = 스피커 다음 곡",
    },

    # ═══════════════════════════════════════════
    # 난이도 HARD: 맥락 의존, 비유, 모호한 표현
    # ═══════════════════════════════════════════
    {
        "command_id": "H01",
        "text": "덥다",
        "expected_action_id": "ac_living_on",
        "difficulty": "hard",
        "category": "에어컨",
        "note": "감정/상태 → 에어컨 켜기 추론",
    },
    {
        "command_id": "H02",
        "text": "너무 어두워",
        "expected_action_id": "light_living_on",
        "difficulty": "hard",
        "category": "조명",
        "note": "상태 표현 → 조명 켜기 추론",
    },
    {
        "command_id": "H03",
        "text": "자러 갈게",
        "expected_action_id": "light_bedroom_night",
        "difficulty": "hard",
        "category": "조명",
        "note": "의도 표현 → 수면 모드 추론",
    },
    {
        "command_id": "H04",
        "text": "나 나간다",
        "expected_action_id": "doorlock_lock",
        "difficulty": "hard",
        "category": "도어락",
        "note": "외출 의도 → 문 잠금 추론",
    },
    {
        "command_id": "H05",
        "text": "눈이 부셔",
        "expected_action_id": "blind_living_close",
        "difficulty": "hard",
        "category": "블라인드",
        "note": "눈부심 → 블라인드 닫기 추론",
    },
    {
        "command_id": "H06",
        "text": "숨쉬기 힘들어",
        "expected_action_id": "air_purifier_on",
        "difficulty": "hard",
        "category": "공기청정기",
        "note": "공기 질 불만 → 공기청정기 켜기 추론",
    },
    {
        "command_id": "H07",
        "text": "목이 칼칼해",
        "expected_action_id": "humidifier_on",
        "difficulty": "hard",
        "category": "가습기",
        "note": "건조함 증상 → 가습기 켜기 추론",
    },
    {
        "command_id": "H08",
        "text": "넷플릭스 보여줘",
        "expected_action_id": "tv_living_input",
        "difficulty": "hard",
        "category": "TV",
        "note": "앱 이름 → TV 입력 소스 변경",
    },
    {
        "command_id": "H09",
        "text": "바닥이 더러워",
        "expected_action_id": "vacuum_start",
        "difficulty": "hard",
        "category": "청소기",
        "note": "상태 불만 → 청소기 시작 추론",
    },
    {
        "command_id": "H10",
        "text": "시끄러워",
        "expected_action_id": "tv_living_volume_down",
        "difficulty": "hard",
        "category": "TV",
        "note": "불만 → 볼륨 낮추기 추론 (다중 해석 가능)",
    },
    {
        "command_id": "H11",
        "text": "좀 추운데",
        "expected_action_id": "ac_living_temp",
        "difficulty": "hard",
        "category": "에어컨",
        "note": "추위 → 에어컨 온도 올리기 추론",
    },
    {
        "command_id": "H12",
        "text": "침실만 청소해",
        "expected_action_id": "vacuum_room",
        "difficulty": "hard",
        "category": "청소기",
        "note": "특정 방 지정 청소",
    },
    {
        "command_id": "H13",
        "text": "잠자기 좋게 해줘",
        "expected_action_id": "ac_bedroom_sleep",
        "difficulty": "hard",
        "category": "에어컨",
        "note": "수면 환경 → 침실 에어컨 취침 모드 (다중 해석 가능)",
    },
    {
        "command_id": "H14",
        "text": "밖에 뭐 하고 있어",
        "expected_action_id": "doorlock_status",
        "difficulty": "hard",
        "category": "도어락",
        "note": "극단적 모호 — 매칭 실패 예상. 매칭 불가 케이스 테스트",
    },
    {
        "command_id": "H15",
        "text": "분위기 좀 바꿔봐",
        "expected_action_id": "light_living_color",
        "difficulty": "hard",
        "category": "조명",
        "note": "'분위기' → 조명 색상 변경 추론",
    },
]


def get_commands_by_difficulty(difficulty: str = None) -> list[dict]:
    """난이도별 명령어를 반환한다."""
    if difficulty is None:
        return TEST_COMMANDS
    return [c for c in TEST_COMMANDS if c["difficulty"] == difficulty]
