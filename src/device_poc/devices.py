"""
디바이스 매니저 - 디바이스 및 액션 정의
========================================
다양한 IoT 디바이스와 각 디바이스가 수행할 수 있는 액션을 JSON 형태로 정의한다.
각 액션에는 자연어 설명과 파라미터 스펙이 포함되어 있어
STT 텍스트와의 시맨틱 매칭에 활용된다.
"""

DEVICES = [
    # ───────────────── 조명 ─────────────────
    {
        "device_id": "light_living",
        "device_name": "거실 조명",
        "device_type": "light",
        "location": "거실",
        "actions": [
            {
                "action_id": "light_living_on",
                "action_name": "켜기",
                "description": "거실 조명을 켠다",
                "params": {},
            },
            {
                "action_id": "light_living_off",
                "action_name": "끄기",
                "description": "거실 조명을 끈다",
                "params": {},
            },
            {
                "action_id": "light_living_brightness",
                "action_name": "밝기 조절",
                "description": "거실 조명의 밝기를 조절한다",
                "params": {"brightness": {"type": "int", "min": 0, "max": 100, "unit": "%"}},
            },
            {
                "action_id": "light_living_color",
                "action_name": "색상 변경",
                "description": "거실 조명의 색상을 변경한다",
                "params": {"color": {"type": "string", "options": ["따뜻한 흰색", "차가운 흰색", "주황", "파랑", "빨강", "초록", "보라"]}},
            },
        ],
    },
    {
        "device_id": "light_bedroom",
        "device_name": "침실 조명",
        "device_type": "light",
        "location": "침실",
        "actions": [
            {
                "action_id": "light_bedroom_on",
                "action_name": "켜기",
                "description": "침실 조명을 켠다",
                "params": {},
            },
            {
                "action_id": "light_bedroom_off",
                "action_name": "끄기",
                "description": "침실 조명을 끈다",
                "params": {},
            },
            {
                "action_id": "light_bedroom_brightness",
                "action_name": "밝기 조절",
                "description": "침실 조명의 밝기를 조절한다",
                "params": {"brightness": {"type": "int", "min": 0, "max": 100, "unit": "%"}},
            },
            {
                "action_id": "light_bedroom_night",
                "action_name": "수면 모드",
                "description": "침실 조명을 수면 모드로 전환한다. 어둡고 따뜻한 색으로 변경.",
                "params": {},
            },
        ],
    },
    {
        "device_id": "light_kitchen",
        "device_name": "주방 조명",
        "device_type": "light",
        "location": "주방",
        "actions": [
            {
                "action_id": "light_kitchen_on",
                "action_name": "켜기",
                "description": "주방 조명을 켠다",
                "params": {},
            },
            {
                "action_id": "light_kitchen_off",
                "action_name": "끄기",
                "description": "주방 조명을 끈다",
                "params": {},
            },
        ],
    },
    # ───────────────── 에어컨 ─────────────────
    {
        "device_id": "ac_living",
        "device_name": "거실 에어컨",
        "device_type": "air_conditioner",
        "location": "거실",
        "actions": [
            {
                "action_id": "ac_living_on",
                "action_name": "켜기",
                "description": "거실 에어컨을 켠다",
                "params": {},
            },
            {
                "action_id": "ac_living_off",
                "action_name": "끄기",
                "description": "거실 에어컨을 끈다",
                "params": {},
            },
            {
                "action_id": "ac_living_temp",
                "action_name": "온도 설정",
                "description": "거실 에어컨의 설정 온도를 변경한다",
                "params": {"temperature": {"type": "int", "min": 18, "max": 30, "unit": "℃"}},
            },
            {
                "action_id": "ac_living_mode",
                "action_name": "모드 변경",
                "description": "거실 에어컨의 운전 모드를 변경한다",
                "params": {"mode": {"type": "string", "options": ["냉방", "난방", "제습", "송풍", "자동"]}},
            },
            {
                "action_id": "ac_living_wind",
                "action_name": "풍량 조절",
                "description": "거실 에어컨의 바람 세기를 조절한다",
                "params": {"wind_speed": {"type": "string", "options": ["약풍", "중풍", "강풍", "자동"]}},
            },
        ],
    },
    {
        "device_id": "ac_bedroom",
        "device_name": "침실 에어컨",
        "device_type": "air_conditioner",
        "location": "침실",
        "actions": [
            {
                "action_id": "ac_bedroom_on",
                "action_name": "켜기",
                "description": "침실 에어컨을 켠다",
                "params": {},
            },
            {
                "action_id": "ac_bedroom_off",
                "action_name": "끄기",
                "description": "침실 에어컨을 끈다",
                "params": {},
            },
            {
                "action_id": "ac_bedroom_temp",
                "action_name": "온도 설정",
                "description": "침실 에어컨의 설정 온도를 변경한다",
                "params": {"temperature": {"type": "int", "min": 18, "max": 30, "unit": "℃"}},
            },
            {
                "action_id": "ac_bedroom_sleep",
                "action_name": "취침 모드",
                "description": "침실 에어컨을 취침 모드로 설정한다. 시간이 지나면 자동으로 온도를 올리고 풍량을 줄인다.",
                "params": {},
            },
        ],
    },
    # ───────────────── TV ─────────────────
    {
        "device_id": "tv_living",
        "device_name": "거실 TV",
        "device_type": "tv",
        "location": "거실",
        "actions": [
            {
                "action_id": "tv_living_on",
                "action_name": "켜기",
                "description": "거실 TV를 켠다",
                "params": {},
            },
            {
                "action_id": "tv_living_off",
                "action_name": "끄기",
                "description": "거실 TV를 끈다",
                "params": {},
            },
            {
                "action_id": "tv_living_channel",
                "action_name": "채널 변경",
                "description": "거실 TV의 채널을 변경한다",
                "params": {"channel": {"type": "int", "min": 1, "max": 999}},
            },
            {
                "action_id": "tv_living_volume",
                "action_name": "볼륨 조절",
                "description": "거실 TV의 소리 크기를 조절한다",
                "params": {"volume": {"type": "int", "min": 0, "max": 100}},
            },
            {
                "action_id": "tv_living_volume_up",
                "action_name": "볼륨 올리기",
                "description": "거실 TV의 소리를 더 크게 한다",
                "params": {},
            },
            {
                "action_id": "tv_living_volume_down",
                "action_name": "볼륨 내리기",
                "description": "거실 TV의 소리를 더 작게 한다",
                "params": {},
            },
            {
                "action_id": "tv_living_mute",
                "action_name": "음소거",
                "description": "거실 TV의 소리를 음소거한다",
                "params": {},
            },
            {
                "action_id": "tv_living_input",
                "action_name": "입력 소스 변경",
                "description": "거실 TV의 입력 소스를 변경한다",
                "params": {"source": {"type": "string", "options": ["HDMI1", "HDMI2", "USB", "넷플릭스", "유튜브"]}},
            },
        ],
    },
    # ───────────────── 스피커 ─────────────────
    {
        "device_id": "speaker_living",
        "device_name": "거실 스피커",
        "device_type": "speaker",
        "location": "거실",
        "actions": [
            {
                "action_id": "speaker_living_on",
                "action_name": "켜기",
                "description": "거실 스피커를 켠다",
                "params": {},
            },
            {
                "action_id": "speaker_living_off",
                "action_name": "끄기",
                "description": "거실 스피커를 끈다",
                "params": {},
            },
            {
                "action_id": "speaker_living_play",
                "action_name": "음악 재생",
                "description": "거실 스피커에서 음악을 재생한다",
                "params": {},
            },
            {
                "action_id": "speaker_living_pause",
                "action_name": "일시정지",
                "description": "거실 스피커의 음악 재생을 일시 정지한다",
                "params": {},
            },
            {
                "action_id": "speaker_living_next",
                "action_name": "다음 곡",
                "description": "거실 스피커에서 다음 곡을 재생한다",
                "params": {},
            },
            {
                "action_id": "speaker_living_volume",
                "action_name": "볼륨 조절",
                "description": "거실 스피커의 볼륨을 조절한다",
                "params": {"volume": {"type": "int", "min": 0, "max": 100}},
            },
        ],
    },
    # ───────────────── 블라인드/커튼 ─────────────────
    {
        "device_id": "blind_living",
        "device_name": "거실 블라인드",
        "device_type": "blind",
        "location": "거실",
        "actions": [
            {
                "action_id": "blind_living_open",
                "action_name": "열기",
                "description": "거실 블라인드를 올려서 연다",
                "params": {},
            },
            {
                "action_id": "blind_living_close",
                "action_name": "닫기",
                "description": "거실 블라인드를 내려서 닫는다",
                "params": {},
            },
            {
                "action_id": "blind_living_half",
                "action_name": "반만 열기",
                "description": "거실 블라인드를 반만 연다",
                "params": {"position": {"type": "int", "min": 0, "max": 100, "unit": "%"}},
            },
        ],
    },
    {
        "device_id": "blind_bedroom",
        "device_name": "침실 커튼",
        "device_type": "blind",
        "location": "침실",
        "actions": [
            {
                "action_id": "blind_bedroom_open",
                "action_name": "열기",
                "description": "침실 커튼을 연다",
                "params": {},
            },
            {
                "action_id": "blind_bedroom_close",
                "action_name": "닫기",
                "description": "침실 커튼을 닫는다",
                "params": {},
            },
        ],
    },
    # ───────────────── 로봇 청소기 ─────────────────
    {
        "device_id": "vacuum",
        "device_name": "로봇 청소기",
        "device_type": "vacuum_cleaner",
        "location": "거실",
        "actions": [
            {
                "action_id": "vacuum_start",
                "action_name": "청소 시작",
                "description": "로봇 청소기로 청소를 시작한다",
                "params": {},
            },
            {
                "action_id": "vacuum_stop",
                "action_name": "청소 중지",
                "description": "로봇 청소기를 정지시키고 충전 스테이션으로 복귀한다",
                "params": {},
            },
            {
                "action_id": "vacuum_room",
                "action_name": "특정 방 청소",
                "description": "로봇 청소기가 지정한 방만 청소한다",
                "params": {"room": {"type": "string", "options": ["거실", "침실", "주방", "화장실"]}},
            },
            {
                "action_id": "vacuum_mode",
                "action_name": "흡입력 변경",
                "description": "로봇 청소기의 흡입 세기를 변경한다",
                "params": {"power": {"type": "string", "options": ["약", "보통", "강", "터보"]}},
            },
        ],
    },
    # ───────────────── 공기청정기 ─────────────────
    {
        "device_id": "air_purifier",
        "device_name": "공기청정기",
        "device_type": "air_purifier",
        "location": "거실",
        "actions": [
            {
                "action_id": "air_purifier_on",
                "action_name": "켜기",
                "description": "공기청정기를 켠다",
                "params": {},
            },
            {
                "action_id": "air_purifier_off",
                "action_name": "끄기",
                "description": "공기청정기를 끈다",
                "params": {},
            },
            {
                "action_id": "air_purifier_auto",
                "action_name": "자동 모드",
                "description": "공기청정기를 자동 모드로 전환한다. 공기 질에 따라 자동 조절.",
                "params": {},
            },
            {
                "action_id": "air_purifier_speed",
                "action_name": "팬 속도 조절",
                "description": "공기청정기의 팬 속도를 조절한다",
                "params": {"speed": {"type": "string", "options": ["약", "중", "강", "터보"]}},
            },
        ],
    },
    # ───────────────── 가습기 ─────────────────
    {
        "device_id": "humidifier",
        "device_name": "가습기",
        "device_type": "humidifier",
        "location": "침실",
        "actions": [
            {
                "action_id": "humidifier_on",
                "action_name": "켜기",
                "description": "가습기를 켠다",
                "params": {},
            },
            {
                "action_id": "humidifier_off",
                "action_name": "끄기",
                "description": "가습기를 끈다",
                "params": {},
            },
            {
                "action_id": "humidifier_level",
                "action_name": "습도 설정",
                "description": "가습기의 목표 습도를 설정한다",
                "params": {"humidity": {"type": "int", "min": 30, "max": 80, "unit": "%"}},
            },
        ],
    },
    # ───────────────── 도어락 ─────────────────
    {
        "device_id": "doorlock",
        "device_name": "현관 도어락",
        "device_type": "door_lock",
        "location": "현관",
        "actions": [
            {
                "action_id": "doorlock_lock",
                "action_name": "잠금",
                "description": "현관 도어락을 잠근다",
                "params": {},
            },
            {
                "action_id": "doorlock_unlock",
                "action_name": "잠금 해제",
                "description": "현관 도어락의 잠금을 해제한다",
                "params": {},
            },
            {
                "action_id": "doorlock_status",
                "action_name": "상태 확인",
                "description": "현관 도어락의 잠금 상태를 확인한다",
                "params": {},
            },
        ],
    },
]


def get_all_actions() -> list[dict]:
    """모든 디바이스의 모든 액션을 평탄화하여 반환한다."""
    actions = []
    for device in DEVICES:
        for action in device["actions"]:
            actions.append({
                **action,
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "device_type": device["device_type"],
                "location": device["location"],
                # 벡터 검색용 통합 텍스트: 디바이스명 + 위치 + 액션명 + 설명
                "search_text": f"{device['location']} {device['device_name']} {action['action_name']}: {action['description']}",
            })
    return actions


def get_device_summary() -> str:
    """디바이스 목록 요약 출력용 문자열."""
    lines = []
    for device in DEVICES:
        action_names = ", ".join(a["action_name"] for a in device["actions"])
        lines.append(f"  {device['device_name']} ({device['location']}) → [{action_names}]")
    return "\n".join(lines)
