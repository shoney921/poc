"""
합성 일기 데이터 생성기
======================
실행 방법:
    python -m src.data_generation.generate

결과:
    data/diaries.json  - 전체 일기 데이터
    data/ground_truth.json - 평가용 정답 셋
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from .profiles import PERSONS, RELATIONSHIPS, SHARED_EVENTS, WEATHER_BY_MONTH

# ─────────────────────────────────────────────
# 인물별 일기 템플릿
# 각 인물의 성격과 상황을 반영한 다양한 일기 내용
# ─────────────────────────────────────────────

DIARY_TEMPLATES = {
    "A": {  # 김민준 - 소프트웨어 개발자
        "work_stress": [
            "오늘 코드 리뷰에서 팀장님한테 지적을 많이 받았다. 내가 짠 로직이 비효율적이라고. 퇴근하고 나서도 계속 머릿속에 맴돈다. 더 잘해야 하는데.",
            "배포 직전에 버그가 발견됐다. 야근해서 겨우 고쳤는데 정말 초조했다. 이런 날은 집에 와도 긴장이 안 풀린다.",
            "회의가 세 개나 잡혀있어서 코딩할 시간이 없었다. 집중할 수 있는 시간이 점점 줄어드는 것 같아 스트레스다.",
            "프로젝트 마감이 이틀 남았는데 아직 해야 할 게 산더미다. 불안하다. 주말에도 나와야 할 것 같다.",
            "새로운 프레임워크를 도입하자는 제안서를 냈는데 반려됐다. 기술 부채가 쌓이는 게 눈에 보이는데 답답하다.",
        ],
        "work_positive": [
            "오늘 내가 만든 기능이 정식 배포됐다. 유저 반응이 좋다고 PM이 슬랙에 공유해줬다. 뿌듯하다.",
            "새로 들어온 주니어 개발자 멘토링을 시작했다. 가르치면서 나도 다시 배우는 느낌이 들어서 좋았다.",
            "코딩하다가 깔끔한 해결책을 찾았을 때의 쾌감. 오늘 하루가 알차게 느껴졌다.",
        ],
        "relationship": [
            "수아한테 요즘 논문 때문에 바쁜 것 같아서 저녁 도시락을 싸다 줬다. 고맙다고 하면서 눈이 빨개지길래 나까지 울컥했다.",
            "수아랑 오랜만에 데이트했다. 영화 보고 산책하면서 이런저런 이야기를 나눴다. 이런 시간이 참 소중하다.",
            "수아가 논문 스트레스로 예민해져 있어서 조심스럽다. 뭘 해줘야 할지 모르겠어서 그냥 옆에 있어줬다.",
            "수아랑 사소한 걸로 다퉜다. 내가 게임만 한다고... 맞는 말이긴 한데 기분이 안 좋다. 미안한 마음도 들고.",
        ],
        "friendship": [
            "서연이한테 발표 슬라이드 디자인을 부탁했다. 역시 센스가 남다르다. 덕분에 자신감이 좀 생겼다.",
            "서연이가 카페 리뉴얼 작업하느라 바쁘다고 한다. 대학 때부터 열정적인 건 변함이 없다.",
            "서연이랑 오랜만에 통화했다. 대학 때 이야기하면서 웃었다. 역시 오래된 친구가 편하다.",
        ],
        "daily": [
            "퇴근하고 집에서 게임했다. 최근에 시작한 RPG가 재밌다. 현실 도피인 건 알지만 이런 시간이 필요하다.",
            "주말에 혼자 카페에서 사이드 프로젝트를 했다. 회사에서는 못 쓰는 기술 스택으로 뭔가 만드는 게 즐겁다.",
            "오늘은 아무것도 하기 싫어서 하루 종일 넷플릭스만 봤다. 가끔은 이런 날도 필요하지.",
            "새벽에 잠이 안 와서 기술 블로그를 읽었다. AI 관련 글이 쏟아지는데 따라가기가 벅차다.",
        ],
        "emotional": [
            "요즘 번아웃이 온 것 같다. 의욕이 없고 모든 게 귀찮다. 이직을 고민해봐야 하나.",
            "날씨가 좋으니까 마음도 좀 나아진다. 점심에 공원에서 산책했더니 머리가 맑아졌다.",
            "미래가 불안하다. 개발자로 계속 살 수 있을까. 나이 들면 어떻게 될까 하는 생각이 자꾸 든다.",
            "오늘따라 감사한 마음이 든다. 좋은 사람들이 주변에 있고, 좋아하는 일을 하고 있으니까.",
        ],
    },
    "B": {  # 이서연 - 프리랜서 디자이너
        "work": [
            "새로운 클라이언트 미팅이 있었다. 브랜딩 프로젝트인데 규모가 꽤 크다. 설레면서도 잘할 수 있을지 걱정된다.",
            "지호 오빠 카페 리뉴얼 디자인 작업에 들어갔다. 공간의 따뜻한 느낌을 살리고 싶다. 아이디어가 막 떠올라서 신난다!",
            "프리랜서의 고질적 문제... 이번 달 수입이 불안정하다. 그래도 자유로운 시간이 좋아서 포기 못 한다.",
            "카페 로고 시안을 세 가지 만들어서 지호 오빠한테 보여줬다. 두 번째 안을 좋아해줘서 기분 좋다.",
            "밤새 작업해서 포트폴리오 업데이트를 끝냈다. 뿌듯하다! 이제 SNS에 올려야지.",
        ],
        "social": [
            "민준이랑 오래간만에 카페에서 수다 떨었다. 여전히 말수가 적지만 진심이 느껴지는 친구. 발표 슬라이드 부탁해와서 도와줬다.",
            "전시회 오프닝이었다! 민준이랑 수아가 와줬다. 내 작품 앞에서 사진 찍는 모습에 감동받았다.",
            "친구들이랑 와인 파티를 했다. 각자 고민을 나누면서 웃고 울었다. 사람들과 어울리면 에너지를 얻는다.",
            "지호 오빠 카페에서 작업하는 날이 많아졌다. 분위기가 좋아서 집중도 잘 되고 커피도 맛있고.",
        ],
        "creative": [
            "미술관에서 새 전시를 봤다. 색감이 너무 예뻐서 한참 서있었다. 이런 감각을 내 작업에도 녹이고 싶다.",
            "영감이 안 떠오르는 슬럼프. 이런 날은 산책하면서 사진을 찍는 게 도움이 된다.",
            "새벽에 갑자기 아이디어가 떠올라서 바로 스케치했다. 이런 순간이 디자이너로 사는 이유!",
        ],
        "emotional": [
            "혼자 사는 게 외로울 때가 있다. 특히 비 오는 날. 누군가와 따뜻한 차를 마시고 싶다.",
            "오늘 하루가 완벽했다. 좋아하는 작업, 맛있는 밥, 예쁜 노을. 이런 날이 계속되면 좋겠다.",
            "SNS에서 동기들의 성공 소식을 보면 조급해진다. 나만의 속도가 있다고 되뇌이지만 쉽지 않다.",
            "가을이 오면 괜히 센치해진다. 카페에서 따뜻한 라떼를 마시며 창밖을 보는 시간이 좋다.",
        ],
        "daily": [
            "오늘은 카페 세 곳을 돌았다. 인테리어 리서치 겸 새로운 카페 탐방. 역시 공간은 사람을 바꾼다.",
            "아침부터 요가를 하고 맛있는 브런치를 만들어 먹었다. 프리랜서의 좋은 점은 이런 아침이다.",
        ],
    },
    "C": {  # 박지호 - 카페 사장
        "cafe_business": [
            "오늘 매출이 좀 떨어졌다. 주변에 새 카페가 또 생겨서 걱정이다. 뭔가 차별화 포인트를 만들어야 한다.",
            "서연 씨가 보내준 디자인 시안이 너무 마음에 든다. 리뉴얼하면 분위기가 확 달라질 것 같아 기대된다.",
            "새 메뉴 개발에 집중했다. 딸기 라떼가 반응이 좋을 것 같다. 직접 시럽부터 만들었다.",
            "카페 리뉴얼 공사가 시작됐다. 소음 때문에 며칠 휴업해야 한다. 매출 걱정이 되지만 장기적으로 봐야지.",
            "리뉴얼 오픈 첫날! 손님들이 많이 와줘서 감동이다. 서연 씨 디자인 덕분에 분위기가 정말 좋아졌다. 우진이도 축하하러 와줬다.",
            "단골 손님이 커피가 맛있어졌다고 해줬다. 새 원두로 바꾼 보람이 있다. 이런 한마디가 힘이 된다.",
        ],
        "neighbor": [
            "우진이랑 저녁에 맥주 한잔했다. 학교 이야기를 듣다 보면 선생님이 참 대단한 직업이구나 싶다.",
            "우진이가 카페에 자주 와서 채점한다. 아메리카노 한 잔으로 몇 시간씩 있는데 고마운 손님이다.",
            "우진이네 집들이에 다녀왔다. 깔끔하게 잘 꾸며놨다. 직접 만든 파스타도 맛있었다.",
        ],
        "emotional": [
            "카페를 하면서 가장 좋은 건 다양한 사람을 만나는 것. 오늘도 재밌는 손님이 왔다.",
            "새벽에 일어나 원두를 볶을 때의 향기. 이 냄새를 맡으면 힘들어도 다시 힘이 난다.",
            "비 오는 날이면 손님이 뜸해서 걱정이지만, 빗소리 들으며 카페에 앉아있는 시간은 나름 좋다.",
            "요즘 체력이 달린다. 매일 새벽부터 저녁까지 서있으니까. 건강 관리를 좀 해야겠다.",
        ],
        "daily": [
            "새로운 원두를 시음했다. 에티오피아 예가체프. 플로럴한 향이 좋다. 다음 달부터 써봐야겠다.",
            "일요일이라 쉬면서 넷플릭스 봤다. 요리 다큐멘터리를 보면서 메뉴 아이디어를 얻었다.",
        ],
    },
    "D": {  # 최수아 - 대학원생 (심리학)
        "academic": [
            "논문 데이터 분석이 잘 안 풀린다. 통계 결과가 기대와 다르게 나와서 교수님께 상담을 요청했다.",
            "중간 발표가 다가오는데 준비가 부족한 것 같아 마음이 무겁다. 민준 오빠가 응원해줘서 조금 힘이 났다.",
            "논문 발표를 무사히 마쳤다! 교수님이 방향성이 좋다고 해주셔서 안도했다. 민준 오빠랑 우진 선생님이 와줘서 감동.",
            "교수님이 논문 방향을 바꾸라고 하셨다. 지금까지 한 게 다 물거품이 된 기분. 너무 허탈하다.",
            "학회 논문을 제출했다! 결과가 어떨지 초조하지만 일단 해냈다는 게 중요하다.",
            "연구실 후배가 고민 상담을 해왔다. 심리학을 공부하면서 주변 사람들의 마음도 더 잘 보이게 된 것 같다.",
        ],
        "relationship": [
            "민준 오빠랑 오랜만에 데이트. 오빠가 도시락을 싸왔다. 서툴지만 정성이 느껴져서 눈물이 날 뻔했다.",
            "민준 오빠가 게임만 한다고 짜증을 냈다. 나도 논문 스트레스로 예민한 상태라 말이 세게 나갔다. 반성 중.",
            "오빠가 요즘 회사에서 힘들어하는 것 같은데 잘 표현을 안 해서 답답하다. 내향적인 사람과 연애하는 건 인내가 필요하다.",
            "민준 오빠 생일. 서연 언니랑 같이 서프라이즈를 준비했다. 오빠가 진짜 놀라는 표정이 귀여웠다.",
        ],
        "study_group": [
            "우진 선생님이랑 스터디를 했다. 교육 심리학 논문을 같이 읽었는데 실제 교육 현장 이야기를 들으니 이해가 깊어진다.",
            "우진 선생님과 스터디하면서 학생 상담 사례를 들었다. 심리학적으로 조언을 해드렸더니 도움이 됐다고 하셔서 뿌듯했다.",
        ],
        "emotional": [
            "대학원 생활이 외롭다. 연구실에 혼자 앉아있으면 내가 뭘 하고 있는 건지 회의가 든다.",
            "봄 산책을 했더니 기분이 한결 나아졌다. 벚꽃이 예뻤다. 작은 것에서 행복을 찾아야지.",
            "졸업 후 진로가 걱정이다. 상담사가 될지, 연구자가 될지. 선택의 순간이 다가오고 있다.",
            "오늘 상담 실습에서 내담자의 눈물을 보면서 나도 울컥했다. 이 일이 나한테 맞는 것 같다.",
        ],
        "daily": [
            "비 오는 날 연구실에서 혼자 논문을 읽었다. 빗소리가 오히려 집중하기 좋았다.",
            "주말에 도서관 대신 카페에서 공부했다. 지호 씨 카페 분위기가 참 좋다.",
        ],
    },
    "E": {  # 정우진 - 고등학교 교사
        "teaching": [
            "오늘 수업에서 학생들이 눈을 반짝이며 들어줬다. 이런 순간이 교사로서 가장 보람 있다.",
            "문제 학생과 상담을 했다. 가정 환경이 어려운 아이라 마음이 아프다. 내가 해줄 수 있는 게 뭘까.",
            "시험 채점을 하면서 한숨이 나왔다. 열심히 가르쳤는데 결과가 안 나오면 자괴감이 든다.",
            "학부모 상담 주간이다. 하루에 열 명 넘게 상담하니 체력적으로 힘들다.",
            "졸업한 제자가 찾아와서 대학 생활 이야기를 해줬다. 잘 자라고 있는 모습에 뿌듯했다.",
            "학생들과 체육대회를 했다. 같이 뛰면서 웃는 게 참 좋다. 이런 날은 피로가 싹 날아간다.",
        ],
        "neighbor": [
            "지호 씨 카페에서 채점을 했다. 커피 향 속에서 하니까 덜 지루하다. 지호 씨가 새 메뉴 시식도 시켜줬다.",
            "지호 씨랑 동네 맛집에서 저녁을 먹었다. 카페 운영 어려움을 들으며 자영업자의 고충을 알게 됐다.",
            "새 집으로 이사했다! 지호 씨랑 수아 씨가 집들이에 와줬다. 직접 파스타를 만들었는데 맛있다고 해줘서 다행이다.",
        ],
        "study_group": [
            "수아 씨와 스터디를 했다. 교육 심리학 관점에서 내 수업을 분석해보니 개선할 점이 보인다.",
            "수아 씨가 학생 상담에 대해 심리학적 조언을 해줬다. 전문가의 시각은 역시 다르다. 많이 배웠다.",
        ],
        "emotional": [
            "교사라는 직업이 때로는 무겁게 느껴진다. 학생들의 미래에 영향을 미친다고 생각하면 책임감에 어깨가 무겁다.",
            "주말에 등산을 다녀왔다. 정상에서 바라본 풍경이 아름다웠다. 마음의 짐을 좀 내려놓은 기분.",
            "교직 생활 5년 차. 처음의 열정이 조금씩 식어가는 것 같아 걱정이다. 초심을 되찾아야 한다.",
            "오늘 학생이 '선생님 수업이 제일 재밌어요'라고 했다. 이 한마디에 모든 피로가 풀렸다.",
        ],
        "daily": [
            "주말에 새로운 요리를 도전했다. 크림 파스타를 만들었는데 생각보다 잘 됐다. 요리가 취미가 될 것 같다.",
            "퇴근 후 독서를 했다. 교육 관련 책인데 실제 수업에 적용할 아이디어가 많아서 좋았다.",
        ],
    },
}

# 공유 이벤트에 대한 인물별 일기 내용
SHARED_EVENT_ENTRIES = {
    "SE01": {  # 서연이네 전시회
        "A": "서연이 전시회에 수아랑 같이 갔다. 서연이 작품이 정말 멋졌다. 색감이 독특하고 감성적이었다. 수아가 '우리 친구 진짜 대단하다'고 하길래 괜히 뿌듯했다.",
        "B": "내 첫 개인전! 떨리고 설레는 하루였다. 민준이랑 수아가 와줘서 너무 고마웠다. 민준이는 여전히 말수가 적지만 끝까지 다 보고 갔다. 내 작품을 진심으로 봐주는 사람들.",
        "D": "서연 언니 전시회에 민준 오빠랑 갔다. 언니의 작품에서 감정의 깊이가 느껴졌다. 심리학적으로 보면 색채에 무의식이 투영된 느낌. 오빠도 감명받은 것 같았다.",
    },
    "SE02": {  # 카페 온기 리뉴얼 오픈
        "B": "카페 온기 리뉴얼 오픈! 내가 디자인한 공간에 사람들이 들어와 앉는 모습을 보니 감회가 새롭다. 지호 오빠가 기뻐하는 모습에 나까지 행복해졌다.",
        "C": "드디어 리뉴얼 오픈! 서연 씨 디자인 덕분에 카페가 완전히 달라졌다. 우진이도 축하하러 와줬다. 손님들 반응이 너무 좋아서 눈물이 날 뻔했다.",
        "E": "지호 씨 카페 리뉴얼 오픈에 다녀왔다. 분위기가 정말 좋아졌다. 서연 씨라는 디자이너가 했다는데 센스가 대단하다. 앞으로 더 자주 와야겠다.",
    },
    "SE03": {  # 민준 생일 모임
        "A": "생일인 줄도 모르고 갔는데 서연이랑 수아가 깜짝 파티를 준비해놨다. 케이크에 촛불까지. 이런 거 쑥스러운데... 근데 솔직히 감동받았다. 고마운 사람들.",
        "B": "민준이 생일 서프라이즈 성공! 수아랑 같이 준비했는데 민준이 표정이 진짜 볼 만했다. 감정 표현 안 하는 애가 눈이 촉촉해지더라. 역시 준비하길 잘했다.",
        "D": "민준 오빠 생일 서프라이즈를 서연 언니랑 준비했다. 오빠가 정말 놀라더라. 평소에 감정 표현을 잘 안 하는 사람이 고맙다고 작게 말해줬을 때 마음이 뭉클했다.",
    },
    "SE04": {  # 봄 소풍
        "A": "한강에서 다같이 피크닉을 했다. 서연이, 수아, 지호, 우진이까지 다섯 명이 모인 건 처음인데 의외로 분위기가 좋았다. 사람들 사이에서 에너지를 빼앗기는 느낌이지만 가끔은 이런 것도 괜찮다.",
        "B": "한강 피크닉! 다섯 명이 다 모이다니. 지호 오빠가 샌드위치를 만들어왔고 우진 선생님이 과일을 깎아줬다. 민준이는 돗자리에 누워서 하늘만 보고 있었지만 그것도 민준이답다.",
        "C": "한강에서 모두 함께 소풍! 샌드위치를 직접 만들어갔는데 다들 맛있다고 해줘서 뿌듯했다. 서연 씨, 우진이, 민준 씨, 수아 씨 모두 좋은 사람들이다.",
        "D": "다같이 한강 피크닉. 봄바람이 기분 좋았다. 다섯 명이 모이니까 다양한 이야기가 오가서 재밌었다. 민준 오빠가 조용히 내 손을 잡아줬다.",
        "E": "한강에서 단체 소풍! 지호 씨 샌드위치가 맛있었다. 수아 씨와 교육 관련 이야기도 나눌 수 있어서 좋았다. 이렇게 다양한 사람들과 어울리는 게 새삼 즐겁다.",
    },
    "SE05": {  # 수아 논문 발표
        "A": "수아 논문 중간 발표에 갔다. 떨리는 게 보여서 마음이 졸였는데 잘 해냈다. 발표 끝나고 꽃을 줬더니 부끄러워하면서도 좋아하는 게 보였다. 자랑스럽다.",
        "D": "중간 발표를 무사히 끝냈다! 교수님이 연구 방향이 좋다고 해주셨다. 민준 오빠가 꽃을 들고 와줬고 우진 선생님도 응원하러 와줬다. 이 사람들이 있어서 버틸 수 있다.",
        "E": "수아 씨 논문 발표에 다녀왔다. 심리학 연구가 교육 현장에도 시사하는 바가 컸다. 발표 후에 같이 밥을 먹으면서 연구 이야기를 나눴다. 자극을 많이 받았다.",
    },
    "SE06": {  # 우진이네 집들이
        "C": "우진이네 집들이에 갔다. 깔끔하게 잘 꾸며놨더라. 직접 만든 파스타가 맛있어서 놀랐다. 나도 요리 실력을 더 키워야겠다.",
        "D": "우진 선생님 집들이. 새 집이 아담하고 따뜻한 느낌이었다. 파스타도 맛있었고 지호 씨도 와서 세 명이 이런저런 이야기를 나눴다.",
        "E": "집들이를 했다! 지호 씨와 수아 씨가 와줬다. 직접 만든 파스타를 대접했는데 맛있다고 해줘서 다행이다. 새 집에서의 첫 손님맞이. 좋은 출발이다.",
    },
    "SE07": {  # 서연-지호 카페 프로젝트 미팅
        "B": "지호 오빠와 카페 리뉴얼 첫 미팅을 했다. 오빠가 원하는 분위기를 들으면서 머릿속에 그림이 그려졌다. 따뜻하면서도 모던한 느낌. 도전해볼 만한 프로젝트다!",
        "C": "서연 씨와 카페 리뉴얼 미팅을 했다. 내가 원하는 걸 정확히 이해해줘서 믿음이 간다. 디자인 전문가와 일하니까 역시 다르다.",
    },
    "SE08": {  # 민준 회사 발표
        "A": "분기 발표가 있었다. 서연이가 도와준 슬라이드 덕분에 자신감이 좀 생겼다. 발표 자체는 잘 한 것 같은데 팀장님 표정을 읽기가 어려웠다. 결과가 걱정된다.",
    },
    "SE09": {  # 비 오는 날 카페 모임
        "A": "비 오는 일요일. 서연이가 지호 씨 카페에서 만나자고 해서 갔다. 빗소리 들으며 따뜻한 커피 마시니까 좋았다. 지호 씨가 새 메뉴를 시식시켜줬다.",
        "B": "비 오는 날이라 지호 오빠 카페에서 민준이랑 만났다. 빗소리 + 커피 향 + 좋은 음악. 완벽한 조합이다. 민준이도 평소보다 말이 많아졌다.",
        "C": "비가 와서 손님이 적나 했는데 서연 씨랑 민준 씨가 왔다. 새 메뉴 시식도 시키고 즐거운 시간을 보냈다. 비 오는 날의 카페도 나름의 매력이 있다.",
    },
    "SE10": {  # 수아-우진 스터디
        "D": "우진 선생님과 정기 스터디를 했다. 오늘은 청소년 심리 관련 논문을 읽었다. 선생님의 현장 경험과 내 이론 지식이 만나면 시너지가 난다.",
        "E": "수아 씨와 스터디. 청소년 심리 논문을 같이 읽었는데 교실에서 겪는 상황들이 논문에 다 나와있어서 신기했다. 역시 이론과 실천은 함께 가야 한다.",
    },
}

# 요일별 한국어
WEEKDAYS_KR = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _get_weather(date: datetime) -> str:
    """날짜에 따른 날씨 반환"""
    month = date.month
    if month in WEATHER_BY_MONTH:
        weathers = WEATHER_BY_MONTH[month]
    else:
        weathers = ["맑음", "맑음", "흐림", "맑음"]
    return weathers[date.day % len(weathers)]


def _get_mood_from_content(content: str) -> tuple[str, int]:
    """일기 내용에서 감정과 점수를 추출 (간단 규칙 기반)"""
    negative_words = ["불안", "초조", "걱정", "스트레스", "힘들", "답답", "외롭", "슬럼프",
                      "허탈", "짜증", "피곤", "무겁", "자괴감", "울컥", "번아웃", "귀찮",
                      "걱정", "한숨", "눈물", "아프", "무겁게"]
    positive_words = ["뿌듯", "감동", "행복", "좋았다", "신난", "설레", "감사", "기분 좋",
                      "웃었", "즐거", "대단", "자랑스럽", "편안", "기뻐", "맛있", "아름다",
                      "보람", "완벽", "사랑"]

    neg_count = sum(1 for w in negative_words if w in content)
    pos_count = sum(1 for w in positive_words if w in content)

    if pos_count > neg_count + 1:
        return random.choice(["행복", "기쁨", "설렘", "뿌듯"]), random.randint(4, 5)
    elif neg_count > pos_count + 1:
        return random.choice(["불안", "우울", "스트레스", "외로움"]), random.randint(1, 2)
    elif neg_count > pos_count:
        return random.choice(["걱정", "피곤", "불편"]), 3
    elif pos_count > neg_count:
        return random.choice(["평온", "만족", "감사"]), 4
    else:
        return "보통", 3


def _extract_mentioned_people(content: str, person_id: str) -> list[str]:
    """일기 내용에서 언급된 사람 이름 추출"""
    names = {
        "A": ["김민준", "민준"],
        "B": ["이서연", "서연"],
        "C": ["박지호", "지호"],
        "D": ["최수아", "수아"],
        "E": ["정우진", "우진"],
    }
    mentioned = []
    for pid, name_variants in names.items():
        if pid == person_id:
            continue
        for name in name_variants:
            if name in content:
                mentioned.append(PERSONS[pid]["name"])
                break
    return mentioned


def _extract_tags(content: str) -> list[str]:
    """일기 내용에서 태그 추출"""
    tag_keywords = {
        "직장": ["회사", "코드", "배포", "버그", "팀장", "야근", "발표", "회의", "프로젝트"],
        "연애": ["수아", "민준 오빠", "데이트", "연인", "손을 잡", "사랑"],
        "우정": ["서연", "친구", "동기", "오래된 친구"],
        "카페": ["카페", "커피", "원두", "메뉴", "라떼", "온기"],
        "학업": ["논문", "연구", "교수님", "발표", "학회", "데이터 분석", "통계"],
        "교육": ["수업", "학생", "채점", "상담", "교사", "학부모"],
        "음식": ["요리", "파스타", "샌드위치", "브런치", "맛있"],
        "건강": ["체력", "운동", "산책", "등산", "요가", "건강"],
        "취미": ["게임", "독서", "사진", "전시회", "영화", "넷플릭스"],
        "감정": ["불안", "행복", "외롭", "스트레스", "우울", "감동", "번아웃"],
        "날씨": ["비", "맑", "봄", "가을", "벚꽃", "노을"],
    }
    tags = []
    for tag, keywords in tag_keywords.items():
        if any(kw in content for kw in keywords):
            tags.append(tag)
    return tags


def _extract_places(content: str) -> list[str]:
    """일기 내용에서 장소 추출"""
    place_keywords = {
        "회사": ["회사", "사무실"],
        "집": ["집에", "퇴근하고"],
        "카페": ["카페"],
        "한강": ["한강"],
        "공원": ["공원"],
        "미술관": ["미술관", "전시"],
        "대학교": ["연구실", "대학", "도서관"],
        "학교": ["학교", "교실"],
        "식당": ["맛집", "식당", "저녁"],
    }
    places = []
    for place, keywords in place_keywords.items():
        if any(kw in content for kw in keywords):
            places.append(place)
    return places


def generate_diaries() -> list[dict]:
    """
    전체 일기 데이터를 생성한다.

    Returns:
        list[dict]: 일기 항목 리스트
    """
    all_entries = []
    start_date = datetime(2025, 3, 1)
    end_date = datetime(2025, 8, 31)

    # 공유 이벤트 날짜 매핑
    event_dates = {}
    for event in SHARED_EVENTS:
        event_dates[event["date"]] = event

    for person_id, person in PERSONS.items():
        templates = DIARY_TEMPLATES[person_id]
        all_templates_flat = []
        for category, entries in templates.items():
            for entry in entries:
                all_templates_flat.append((category, entry))

        current_date = start_date
        entry_index = 0

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            # 일기를 쓰는 날 (주 3~5회 랜덤)
            write_probability = 0.6
            if current_date.weekday() >= 5:  # 주말은 더 자주
                write_probability = 0.75

            if random.random() > write_probability:
                current_date += timedelta(days=1)
                continue

            content = None
            event_ref = None

            # 공유 이벤트가 있는 날
            if date_str in event_dates:
                event = event_dates[date_str]
                if person_id in event["participants"]:
                    event_id = event["id"]
                    if event_id in SHARED_EVENT_ENTRIES and person_id in SHARED_EVENT_ENTRIES[event_id]:
                        content = SHARED_EVENT_ENTRIES[event_id][person_id]
                        event_ref = event["name"]

            # 일반 일기
            if content is None:
                category, content = all_templates_flat[entry_index % len(all_templates_flat)]
                entry_index += 1

            # 메타데이터 추출
            weather = _get_weather(current_date)
            mood, mood_score = _get_mood_from_content(content)
            mentioned_people = _extract_mentioned_people(content, person_id)
            tags = _extract_tags(content)
            places = _extract_places(content)
            weekday = WEEKDAYS_KR[current_date.weekday()]

            entry = {
                "entry_id": f"diary_{person_id}_{date_str}",
                "person_id": person_id,
                "person_name": person["name"],
                "date": date_str,
                "day_of_week": weekday,
                "weather": weather,
                "mood": mood,
                "mood_score": mood_score,
                "tags": tags,
                "content": content,
                "mentioned_people": mentioned_people,
                "mentioned_places": places,
                "shared_event": event_ref,
            }
            all_entries.append(entry)
            current_date += timedelta(days=1)

    return all_entries


def generate_ground_truth() -> list[dict]:
    """
    평가용 Ground Truth 데이터를 생성한다.
    각 테스트 쿼리에 대해 관련 있는 일기 ID를 수동으로 정의.
    """
    return [
        {
            "query_id": "Q01",
            "query": "스트레스 받는 날들",
            "category": "감정",
            "description": "불안, 초조, 걱정 등 스트레스 관련 일기",
            "relevant_tags": ["감정", "직장", "학업"],
            "relevant_moods": ["불안", "스트레스", "걱정"],
        },
        {
            "query_id": "Q02",
            "query": "행복했던 순간",
            "category": "감정",
            "description": "기쁨, 뿌듯함, 감동 등 긍정적 감정",
            "relevant_tags": ["감정"],
            "relevant_moods": ["행복", "기쁨", "설렘", "뿌듯"],
        },
        {
            "query_id": "Q03",
            "query": "외로움을 느꼈던 때",
            "category": "감정",
            "description": "외로움, 고독, 혼자인 느낌 관련",
            "relevant_tags": ["감정"],
            "relevant_moods": ["외로움", "우울"],
        },
        {
            "query_id": "Q04",
            "query": "마음이 편안했던 날",
            "category": "감정",
            "description": "평화, 여유, 편안 관련 (동의어 매칭 테스트)",
            "relevant_tags": ["감정", "날씨"],
            "relevant_moods": ["평온", "만족", "감사"],
        },
        {
            "query_id": "Q05",
            "query": "친구들과 만난 날",
            "category": "이벤트",
            "description": "친구, 동기 등과 만남",
            "relevant_tags": ["우정"],
            "relevant_moods": [],
        },
        {
            "query_id": "Q06",
            "query": "직장에서 문제가 있었던 날",
            "category": "이벤트",
            "description": "직장/일 관련 스트레스, 문제",
            "relevant_tags": ["직장"],
            "relevant_moods": ["불안", "스트레스", "걱정"],
        },
        {
            "query_id": "Q07",
            "query": "맛있는 음식을 먹은 날",
            "category": "이벤트",
            "description": "음식, 요리, 맛집 관련",
            "relevant_tags": ["음식"],
            "relevant_moods": [],
        },
        {
            "query_id": "Q08",
            "query": "새로운 것을 시작한 경험",
            "category": "이벤트",
            "description": "새로운 도전, 시작 관련",
            "relevant_tags": [],
            "relevant_moods": ["설렘"],
        },
        {
            "query_id": "Q09",
            "query": "서연이와 관련된 이야기",
            "category": "사람",
            "description": "이서연 언급 일기 (키워드 매칭 테스트)",
            "relevant_tags": ["우정"],
            "relevant_moods": [],
            "must_mention": "이서연",
        },
        {
            "query_id": "Q10",
            "query": "연인과 함께한 시간",
            "category": "사람",
            "description": "민준-수아 연인 관계 일기",
            "relevant_tags": ["연애"],
            "relevant_moods": [],
        },
        {
            "query_id": "Q11",
            "query": "인생에 대한 고민",
            "category": "추상",
            "description": "미래, 진로, 존재 의미 관련 깊은 고민",
            "relevant_tags": ["감정"],
            "relevant_moods": ["불안", "우울", "걱정"],
        },
        {
            "query_id": "Q12",
            "query": "미래에 대한 계획",
            "category": "추상",
            "description": "미래 계획, 목표 관련",
            "relevant_tags": [],
            "relevant_moods": [],
        },
        {
            "query_id": "Q13",
            "query": "자기 반성",
            "category": "추상",
            "description": "자기 성찰, 반성, 후회 관련",
            "relevant_tags": ["감정"],
            "relevant_moods": [],
        },
        {
            "query_id": "Q14",
            "query": "비 오는 날의 감정",
            "category": "복합",
            "description": "비+감정 복합 조건",
            "relevant_tags": ["날씨", "감정"],
            "relevant_moods": [],
        },
        {
            "query_id": "Q15",
            "query": "카페에서 있었던 일",
            "category": "장소",
            "description": "카페 관련 일기",
            "relevant_tags": ["카페"],
            "relevant_moods": [],
        },
    ]


def save_data(output_dir: str = "data"):
    """
    데이터를 생성하고 JSON 파일로 저장한다.

    Args:
        output_dir: 저장 디렉토리 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # 시드 고정 (재현성)
    random.seed(42)

    # 일기 데이터 생성
    diaries = generate_diaries()
    diaries_path = os.path.join(output_dir, "diaries.json")
    with open(diaries_path, "w", encoding="utf-8") as f:
        json.dump(diaries, f, ensure_ascii=False, indent=2)

    # Ground Truth 생성
    ground_truth = generate_ground_truth()
    gt_path = os.path.join(output_dir, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    # 프로필 저장
    profiles = {
        "persons": PERSONS,
        "relationships": RELATIONSHIPS,
        "shared_events": SHARED_EVENTS,
    }
    profiles_path = os.path.join(output_dir, "profiles.json")
    with open(profiles_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

    # 통계 출력
    person_counts = {}
    for d in diaries:
        pid = d["person_id"]
        person_counts[pid] = person_counts.get(pid, 0) + 1

    print("=" * 50)
    print("📊 데이터 생성 완료")
    print("=" * 50)
    print(f"총 일기 수: {len(diaries)}개")
    print(f"인물별:")
    for pid, count in sorted(person_counts.items()):
        print(f"  {PERSONS[pid]['name']} ({pid}): {count}개")
    print(f"테스트 쿼리: {len(ground_truth)}개")
    print(f"\n저장 위치:")
    print(f"  일기 데이터: {diaries_path}")
    print(f"  Ground Truth: {gt_path}")
    print(f"  프로필: {profiles_path}")
    print("=" * 50)

    return diaries, ground_truth


# 직접 실행 시
if __name__ == "__main__":
    save_data()
