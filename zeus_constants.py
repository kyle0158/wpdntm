"""
[제우스 매크로 - 설정/상수 모음]
이미지 목록(SIMPLE_CLICK_IMAGES 등), 좌표, 타임아웃, 설정 저장/불러오기 등 순수
데이터와 그와 관련된 아주 가벼운 함수만 모아둔 파일입니다. tkinter/win32api 같은 무거운
GUI 의존성이 없어서, "이미지 하나 추가해줘" 같은 간단한 요청은 이 파일만 보고 고치면
됩니다.

- zeus_macro_logic.py가 이 파일의 상수를 가져다 '무엇을 어떻게 찾을지' 판단합니다.
- zeus_gui.py가 이 파일의 상수를 가져다 GUI/연결/클릭 등 실제 동작을 구현합니다.

[새 이미지 추가하는 방법]
  - "찾으면 그냥 클릭"만 하면 되는 이미지 -> SIMPLE_CLICK_IMAGES 리스트에 한 줄만 추가
    (파일명, 검색영역, transwhite여부)
  - "왼쪽위 기준으로 x/y를 특정 범위만큼 밀어서" 클릭해야 하는 이미지 -> OFFSET_CLICK_IMAGES에
    한 줄만 추가 (파일명, 검색영역, transwhite여부, x오프셋범위, y오프셋범위)
  - "다른 이미지가 없을 때만" 클릭해야 하는 이미지 -> CONDITIONAL_CLICK_IMAGES에 한 줄만
    추가 (파일명, 검색영역, transwhite여부, 없어야하는이미지, 그영역, 그transwhite여부)
  - 더블클릭/여러 단계/대기처럼 특수한 동작이 필요한 이미지는 zeus_macro_logic.py에
    개별 핸들러(_handle_* 함수)로 만들어야 합니다.
"""
import os
import json

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None

from telegram_notifier import DEFAULT_SEND_INTERVAL

# ==========================================================
# [연결 설정] main.py와 같은 값을 씁니다. PC마다 포트 번호(COM3, COM4 등)가 다를 수
# 있는데, 아래 PORT는 '아무 설정도 없을 때 맨 처음 시도해볼 기본값'일 뿐입니다.
# 실제로는 1) GUI에 저장된 포트(zeus_config.json) -> 2) 그게 실패하면 자동 인식 순서로
# 접속을 시도합니다 (connect_serial 참고).
# ==========================================================
PORT = 'COM3'
BAUD_RATE = 115200

# [아두이노 자동 인식] 지정한 포트로 연결이 실패하면, 연결된 장치 중 설명(description)에
# 'Arduino'가 들어있거나 아래 VID:PID 조합과 일치하는 포트를 찾아 자동으로 재시도합니다.
# CH340 등을 쓰는 클론 보드도 웬만하면 잡힙니다. 다른 보드/칩을 쓰신다면 여기에 값만
# 추가하면 됩니다.
KNOWN_ARDUINO_VID_PID = {
    (0x2341, 0x8036),  # Arduino Leonardo
    (0x2341, 0x8037),  # Arduino Micro
    (0x2A03, 0x8036),  # Arduino Leonardo (구 VID)
    (0x2A03, 0x8037),  # Arduino Micro (구 VID)
    (0x1A86, 0x7523),  # CH340 계열 클론 보드
}


def find_arduino_port():
    """연결된 시리얼 포트 중 아두이노로 보이는 것을 찾아 포트 이름을 돌려줍니다.
    pyserial의 list_ports를 못 쓰거나 못 찾으면 None."""
    if list_ports is None:
        return None
    try:
        ports = list(list_ports.comports())
    except Exception:
        return None
    for p in ports:
        if "arduino" in (p.description or "").lower():
            return p.device
    for p in ports:
        if (p.vid, p.pid) in KNOWN_ARDUINO_VID_PID:
            return p.device
    return None


WINDOW_WIDTH = 300
WINDOW_HEIGHT = 570
WINDOW_X = 1620   # GUI 창이 켜질 때 위치할 화면 좌표 (좌상단 X)
WINDOW_Y = 0       # GUI 창이 켜질 때 위치할 화면 좌표 (좌상단 Y)

# [게임 창] 제목에 이 글자가 포함된 창을 찾아서 위치/크기를 바꿉니다.
GAME_TITLE_PART = "제우스: 오만의 신"
GAME_WINDOW_X = 0
GAME_WINDOW_Y = 0
GAME_WINDOW_W = 1280   # 1600 -> 1280으로 변경됨
GAME_WINDOW_H = 800

# [루프 주기] run_loop가 한 바퀴 돌고 나서 쉬는 시간(초). 이미지를 많이/자주 찾을 게
# 아니라면 1초 정도가 무난합니다.
LOOP_INTERVAL_SEC = 1.0

# ==========================================================
# [제우스 이미지/영역] region_image_tester.py로 잡은 좌표를 그대로 씁니다.
# 이미지 파일은 image_lookup.IMAGE_DIRS(기본 images/ 폴더)에 있어야 합니다.
# ==========================================================
# ==========================================================
# [단순 클릭 이미지 목록] "찾으면 그냥 클릭"만 하는 이미지는 여기 한 줄만 추가하면 됩니다.
# 각 항목: (이미지 파일명, 검색영역(x1,y1,x2,y2), transwhite 여부)
#   transwhite=True  -> 원본 단계 없이 바로 흰배경 무시 방식으로만 찾습니다 (image_search.locate_transwhite)
#   transwhite=False -> 원본 -> 실패시 transwhite 순서로 찾습니다 (image_search.locate_smart)
# 순서 = 확인 우선순위입니다 (위에 있을수록 먼저 확인).
# ==========================================================
SIMPLE_CLICK_IMAGES = [
    ('apdlscpzm1.png', (1144, 124, 1183, 381), True),
    ('apdlscpzm.png', (1144, 124, 1183, 381), True),
    ('dhksfy.png',    (561, 266, 735, 355), False),
    ('skip.png',      (1141, 44, 1256, 97), False),
    ('tnfkr.png',     (508, 42, 835, 153), False),
    ('wkdckr.png',    (749, 362, 982, 487), True),
    ('ghkrdls.png',   (694, 471, 778, 530), False),
    ('tnfkr1.png',    (1102, 715, 1183, 759), False),
]

# ==========================================================
# [오프셋 클릭 이미지 목록] 이미지 중앙이 아니라 왼쪽위(left, top) 기준으로 x/y를 지정한
# 범위만큼 방향성 있게 더한 위치를 클릭하는 이미지들. 한 줄만 추가하면 됩니다.
# 각 항목: (이미지 파일명, 검색영역, transwhite 여부, x오프셋범위(min,max), y오프셋범위(min,max))
# y오프셋을 안 쓰려면 (0, 0)으로 두면 됩니다 (원본 y 그대로, 흔들림 없음).
# SIMPLE_CLICK_IMAGES 다음 순서로 확인됩니다.
# ==========================================================
OFFSET_CLICK_IMAGES = [
    ('xbxhfldjf.png',   (824, 181, 857, 400), True,  (30, 40), (5, 10)),
]

# ==========================================================
# [조건부 클릭 이미지 목록] "다른 특정 이미지가 없을 때만" 클릭하는 이미지들. 한 줄만
# 추가하면 됩니다. SIMPLE_CLICK_IMAGES/OFFSET_CLICK_IMAGES 다음 순서로 확인됩니다.
# 각 항목: (이미지 파일명, 검색영역, transwhite 여부,
#           없어야 하는 조건 이미지 파일명, 조건 이미지 검색영역, 조건 이미지 transwhite 여부)
# ==========================================================
CONDITIONAL_CLICK_IMAGES = [
    # skrkrl2.png는 tnfkr.png가 없을 때만 클릭합니다.
    ('skrkrl2.png', (17, 44, 82, 99), False, 'tnfkr.png', (508, 42, 835, 153), False),
]

# ==========================================================
# [연속 동작(시퀀스) 이미지] 발견되면 여러 단계를 순서대로 수행하는 특수 이미지들입니다.
# 단순/오프셋 리스트와 달리 각자 로직이 달라서 개별 핸들러(_handle_*)로 처리합니다.
# ==========================================================
# fpdlswj.png - 있으면 '연속 동작' 수행: 이미지 더블클릭 -> (1065,735) 더블클릭 ->
# (740,500) 더블클릭 -> 10초 대기. 이 전체를 하나의 행동으로 취급합니다.
ZEUS_FPDLSWJ_IMG = 'fpdlswj.png'
ZEUS_FPDLSWJ_REGION = (35, 229, 294, 310)
ZEUS_FPDLSWJ_STEP2 = (1065, 735)
ZEUS_FPDLSWJ_STEP3 = (740, 500)
ZEUS_FPDLSWJ_WAIT_SEC = 10.0

# rhkfgh.png - gkdl.png 타임아웃으로 (900,150)을 보정 클릭하기 '직전'에 확인합니다.
# 이 이미지가 떠 있는 상태에서 보정 클릭을 하면 다른 화면으로 넘어가버리므로,
# 떠 있으면 클릭을 건너뛰고 미인식 타이머를 리셋해서 대기시간을 늘립니다.
ZEUS_RHKFGH_IMG = 'rhkfgh.png'
ZEUS_RHKFGH_REGION = (10, 33, 1269, 788)

# wkehdrnao.png(자동구매) - 발견되면 '연속 동작' 수행:
#   1~6) 고정 좌표 6곳을 순서대로 1회씩 클릭
#   7) ghkausdlstlr.png(화면인식)가 보일 때까지 (50,65)를 딜레이를 두고 반복 클릭
ZEUS_AUTOBUY_IMG = 'wkehdrnao.png'
ZEUS_AUTOBUY_REGION = (287, 701, 412, 771)
ZEUS_AUTOBUY_CLICKS = [
    (185, 160),
    (690, 630),
    (720, 585),
    (215, 335),
    (690, 630),
    (720, 585),
]
ZEUS_AUTOBUY_WAIT_IMG = 'ghkausdlstlr.png'
ZEUS_AUTOBUY_WAIT_REGION = (1027, 29, 1151, 109)
ZEUS_AUTOBUY_REPEAT_CLICK = (50, 65)
# [가정] 반복 클릭 사이 딜레이/최대 반복 횟수를 지정 안 해주셔서 임의로 잡았습니다.
# 필요하면 이 두 값만 바꾸면 됩니다.
ZEUS_AUTOBUY_REPEAT_DELAY_SEC = 1.0
ZEUS_AUTOBUY_REPEAT_MAX = 30

# tmzlfqnr.png(스킬북) - 발견되면 '연속 동작' 수행: 고정 좌표 3곳 클릭 -> 창끄기 로직 실행
ZEUS_SKILLBOOK_IMG = 'tmzlfqnr.png'
ZEUS_SKILLBOOK_REGION = (28, 117, 108, 203)
ZEUS_SKILLBOOK_CLICKS = [
    (75, 165),
    (700, 625),
    (725, 575),
]

# ==========================================================
# [HP 확인 / 귀환로직] anfdir0ro.png 또는 anfdiron.png 중 하나라도 있을 때(=사냥중일
# 때)만 hp.png를 확인합니다(매 턴 제일 먼저). 화면 로딩 중처럼 둘 다 안 보이는 상태에서는
# hp.png도 당연히 안 보이는데 그걸 "hp 없음"으로 오판하지 않게 하기 위함입니다.
# 사냥중인데 hp.png가 안 보이면 귀환로직을 수행합니다. 귀환로직은 물약구매 로직
# 시작할 때도 재사용합니다.
#   1) (45,195) -> (682,515) 클릭 쌍을 2회 빠르게 반복
#   2) 10초 대기 후 wkqghkqjxms.png(잡화버튼) 확인. 보이면 귀환 성공, 정상 흐름으로 복귀.
#   3) 없으면 다시 10초 대기 후 재확인 - 최대 30초까지 반복
#   4) 30초 안에 wkqghkqjxms.png가 안 보이면 텔레그램 알림 후 정지
# [가정] "2회 빠르게 반복"의 반복 사이 간격은 지정 안 해주셔서 0.2초로 짧게 잡았습니다.
# ==========================================================
ZEUS_HP_IMG = 'hp.png'
ZEUS_HP_REGION = (179, 59, 214, 83)
ZEUS_RETURN_CLICK1 = (45, 195)
ZEUS_RETURN_CLICK2 = (682, 515)
ZEUS_RETURN_REPEAT = 2
ZEUS_RETURN_REPEAT_GAP_SEC = 0.2  # [가정] 반복 사이 간격
ZEUS_HP_RECHECK_INTERVAL_SEC = 10.0
ZEUS_HP_RECHECK_MAX_SEC = 30.0

# ==========================================================
# [물약구매 로직] anfdir0ro.png가 보이면 발동합니다:
#   1) 귀환로직 수행 (위 [HP 확인 / 귀환로직]과 동일한 동작 재사용)
#   2) 10초 대기
#   3) 잡화버튼(wkqghkqjxms.png)을 찾아서 클릭
#   4) 잡화상점이 열렸는지(wkehdrnao.png - 자동구매 게이트와 같은 이미지/영역을 재사용)
#      최대 30초까지 확인. 안 열리면 텔레그램 알림 후 정지.
#   5) 열렸으면 고정좌표 클릭(70,155)->(680,625)->(825,475)더블클릭->(725,575) 수행
#   6) 3초 대기 후 anfdiron.png로 구매가 실제로 됐는지 확인 (로그만 남기고 정상 흐름 복귀)
# [가정] 잡화상점 열림 확인 주기는 1초로 잡았습니다. 잡화버튼을 못 찾거나 anfdiron
# 확인에 실패해도 명시적으로 정지하라고 하시지 않아서, 경고 로그만 남기고 계속
# 진행하도록 했습니다 (정지가 필요한 두 곳: hp 30초 초과 / 상점 30초 미오픈만 정지).
# ==========================================================
ZEUS_POTION_TRIGGER_IMG = 'anfdir0ro.png'
ZEUS_POTION_TRIGGER_REGION = (298, 692, 347, 755)
# anfdir0ro.png가 처음 보이면 바로 발동하지 않고 이 시간만큼 기다린 뒤 재확인해서,
# 그때도 여전히 보여야 물약구매 로직을 시작합니다 (순간적으로 지나가는 오탐 방지).
ZEUS_POTION_CONFIRM_WAIT_SEC = 4.0
ZEUS_GROCERY_BUTTON_IMG = 'wkqghkqjxms.png'
ZEUS_GROCERY_BUTTON_REGION = (1002, 595, 1236, 764)
ZEUS_SHOP_OPEN_CHECK_IMG = ZEUS_AUTOBUY_IMG        # wkehdrnao.png (자동구매 게이트와 동일)
ZEUS_SHOP_OPEN_CHECK_REGION = ZEUS_AUTOBUY_REGION
ZEUS_SHOP_OPEN_MAX_WAIT_SEC = 30.0
ZEUS_SHOP_OPEN_POLL_SEC = 1.0  # [가정] 상점 열림 확인 주기
ZEUS_POTION_CLICKS = [
    (70, 155),
    (680, 625),
]
ZEUS_POTION_DOUBLE_CLICK = (825, 475)
ZEUS_POTION_LAST_CLICK = (725, 575)
ZEUS_POTION_CLICK_DELAY_SEC = 1.5  # 물약구매 클릭들 사이에 주는 딜레이
ZEUS_POTION_VERIFY_WAIT_SEC = 3.0
ZEUS_POTION_VERIFY_IMG = 'anfdiron.png'
ZEUS_POTION_VERIFY_REGION = ZEUS_POTION_TRIGGER_REGION  # 같은 영역, 다른 이미지(오타 아님)

# ==========================================================
# [무한의 탑] angksdmlxkq5cmd.png가 보이면 발동합니다:
#   1) (1225,65) 클릭 -> 2초 대기 -> (885,665) 클릭 -> 2초 대기 (무한의 탑 화면 진입)
#   2) dusthrwlsgodcpzm.png가 있으면 좌상단 클릭 -> 마우스 치움 -> 재확인, 사라질 때까지 반복
#   3) dlqwkd.png 클릭 -> 2초 대기 -> (733,500) 클릭 (입장 완료)
#   4) dpvlrznptmxm.png 또는 tjqmznptmxm.png가 보일 때까지 대기 (=일반필드 복귀 확인.
#      체류 시간이 정해져 있지 않아 정지 버튼 누르기 전까지 계속 확인합니다)
#   5) (1000,160) 더블클릭 -> 2초 대기 -> 다시 더블클릭 (종료)
# [가정] 장애물 재확인 주기(0.5초)와 퇴장 확인 주기(5초)는 지정 안 해주셔서 임의로
# 잡았습니다. 필요하면 이 두 값만 바꾸면 됩니다.
# ==========================================================
ZEUS_TOWER_TRIGGER_IMG = 'angksdmlxkq5cmd.png'
ZEUS_TOWER_TRIGGER_REGION = (905, 124, 1075, 184)

ZEUS_TOWER_CLICK1 = (1225, 65)
ZEUS_TOWER_CLICK2 = (885, 665)
ZEUS_TOWER_CLICK_DELAY_SEC = 2.0

ZEUS_TOWER_SCREEN_IMG = 'dlqwkd.png'  # 무한의 탑 화면 확인 + 입장 클릭용
ZEUS_TOWER_SCREEN_REGION = (1093, 701, 1224, 782)

ZEUS_TOWER_OBSTACLE_IMG = 'dusthrwlsgodcpzm.png'
ZEUS_TOWER_OBSTACLE_REGION = (889, 715, 996, 766)
ZEUS_TOWER_OBSTACLE_POLL_SEC = 0.5  # [가정] 사라졌는지 재확인하는 주기

ZEUS_TOWER_ENTER_CLICK = (733, 500)

ZEUS_TOWER_EXIT_IMG1 = 'dpvlrznptmxm.png'
ZEUS_TOWER_EXIT_IMG2 = 'tjqmznptmxm.png'
ZEUS_TOWER_EXIT_REGION = (822, 126, 860, 370)
ZEUS_TOWER_EXIT_POLL_SEC = 5.0  # [가정] 일반필드 복귀 확인 주기 (탑 체류시간이 길어서 여유있게)

ZEUS_TOWER_FINISH_CLICK = (1000, 160)
ZEUS_TOWER_FINISH_GAP_SEC = 2.0

# [창끄기] gkdl.png 타임아웃으로 보정 클릭(900,150)을 실행하기 '직전'에 처리하는 정리
# 동작 모음입니다. 나중에 항목이 더 추가될 수 있어서 별도로 분리해 뒀습니다.
#   - dlsqpsxhflx.png가 있으면 그 이미지를 클릭
#   - skrkrl.png가 있으면 (1222,70)을 클릭
ZEUS_CHANGKKEUGI1_IMG = 'dlsqpsxhflx.png'
ZEUS_CHANGKKEUGI1_REGION = (1197, 109, 1251, 160)
ZEUS_CHANGKKEUGI2_IMG = 'skrkrl.png'
ZEUS_CHANGKKEUGI2_REGION = (1130, 712, 1198, 789)
ZEUS_CHANGKKEUGI2_CLICK = (1222, 70)

# [정체 감지] 보정 클릭(900,150)+드래그, HP 미확인, 잡화상점 미오픈 등 "자동 정지가
# 필요한 상황"이 연속 이 횟수 이상 발생하면 텔레그램으로 알리고 매크로를 정지합니다.
# (지금은 보정 클릭+드래그 쪽만 이 카운트를 실제로 세고, HP/상점 미오픈은 각자 자체
# 타임아웃 즉시 정지합니다 - 전부 같은 텔레그램 이벤트('stuck')를 씁니다) GUI에서 값을
# 바꿀 수 있습니다.
DEFAULT_STUCK_REPEAT_THRESHOLD = 3

# ==========================================================
# [서브퀘스트] gkdl.png(메인퀘스트) 관련 로직보다 먼저 확인합니다. tjqmznptmxm.png가
# 보이면(서브퀘스트가 진행 중이라는 뜻) 이번 턴은 서브퀘스트만 처리하고, 메인퀘스트 쪽
# (gkdl.png 등)은 아예 확인하지 않습니다 - "서브퀘스트가 있을 땐 서브퀘스트부터" 반영.
#   - tjqm.png가 보이면: 대기 (아무것도 안 함, gkdl.png 있을 때와 같은 맥락)
#   - tjqm.png가 [미인식 대기] n초 동안 안 보이면: (945,215) 1회 클릭
#   - tjqmznptmxm.png 자체가 안 보이면: 서브퀘스트가 없는 것이므로 바로 메인퀘스트로 넘어감
# tjqmznptmxm.png 자체는 이제 클릭 대상이 아니라 '서브퀘스트가 떠 있는지' 확인하는
# 용도로만 씁니다.
#
# [NORMAL/RAID 두 영역을 직접 순서대로 확인] 레이드 중엔 화면 배치가 달라져서
# tjqmznptmxm.png/tjqm.png가 다른 위치에 나타나고, 보정 클릭 좌표도 달라집니다.
# 예전엔 fpdlem.png 인식 여부로 어느 영역을 볼지 '미리' 정했는데, fpdlem.png 인식이
# 프레임마다 흔들려서(오탐/미탐) 실제로는 레이드 중인데도 NORMAL 영역만 보고 서브퀘스트를
# 놓치는 문제가 있었습니다. 그래서 지금은 fpdlem.png를 거치지 않고, tjqmznptmxm.png
# 자체를 NORMAL -> RAID 순서로 직접 찾아서 걸리는 쪽 영역/좌표를 그대로 씁니다.
# ==========================================================
ZEUS_SUBQUEST_GATE_IMG = 'tjqmznptmxm.png'
ZEUS_SUBQUEST_GATE_REGION_NORMAL = (821, 185, 860, 221)
ZEUS_SUBQUEST_GATE_REGION_RAID = (826, 242, 859, 276)
ZEUS_SUBQUEST_CHECK_IMG = 'tjqm.png'
ZEUS_SUBQUEST_CHECK_REGION_NORMAL = (1183, 180, 1200, 243)
ZEUS_SUBQUEST_CHECK_REGION_RAID = (1183, 243, 1201, 301)
ZEUS_SUBQUEST_CLICK_NORMAL = (945, 215)
ZEUS_SUBQUEST_CLICK_RAID = (945, 275)

# [참고용 - 더 이상 서브퀘스트 영역 선택에는 안 씀] fpdlem.png 인식이 불안정해서 위
# 로직을 fpdlem 의존 없이(NORMAL/RAID 직접 탐색으로) 바꿨습니다. 다른 용도로 필요해질
# 수 있어 상수는 남겨뒀습니다.
ZEUS_RAID_GATE_IMG = 'fpdlem.png'
ZEUS_RAID_GATE_REGION = (914, 187, 1005, 242)

# ==========================================================
# [무한의 탑] angksdmlxkq5cmd.png가 보이면 발동합니다:
#   1) (1225,65) 클릭 -> 2초 대기 -> (885,665) 클릭 -> 2초 대기
#   2) dlqwkd.png(무한의탑 화면) 확인
#   3) dusthrwlsgodcpzm.png가 있으면 좌상단을 클릭하고(자동으로 마우스 치워짐) 다시
#      있는지 확인 - 사라질 때까지 반복
#   4) 사라지면 dlqwkd.png 클릭 -> 2초 대기 -> (733,500) 클릭 (입장 완료)
#   5) dpvlrznptmxm.png 또는 tjqmznptmxm.png가 보일 때까지 대기 (시간 제한 없음 -
#      일반필드로 자동 복귀할 때까지 기다립니다)
#   6) (1000,160) 더블클릭 -> 2초 대기 -> (1000,160) 더블클릭 (종료)
# [가정] dpvlrznptmxm.png/tjqmznptmxm.png(탈출 확인용)의 검색 영역을 안 주셔서, 기존
# 서브퀘스트 게이트 영역(ZEUS_SUBQUEST_GATE_REGION_NORMAL)을 임시로 재사용했습니다.
# 실제 좌표를 알려주시면 바로 고치면 됩니다. 팝업(dusthrwlsgodcpzm) 재확인 전 딜레이(0.5초)
# 와 탈출 확인 폴링 주기(2초)도 지정 안 해주셔서 임의로 잡았습니다.
# ==========================================================
ZEUS_TOWER_TRIGGER_IMG = 'angksdmlxkq5cmd.png'
ZEUS_TOWER_TRIGGER_REGION = (905, 124, 1075, 184)
ZEUS_TOWER_STEP1 = (1225, 65)
ZEUS_TOWER_STEP2 = (885, 665)
ZEUS_TOWER_SCREEN_IMG = 'dlqwkd.png'
ZEUS_TOWER_SCREEN_REGION = (1093, 701, 1224, 782)
ZEUS_TOWER_POPUP_IMG = 'dusthrwlsgodcpzm.png'
ZEUS_TOWER_POPUP_REGION = (889, 715, 996, 766)
ZEUS_TOWER_POPUP_RECHECK_DELAY_SEC = 0.5  # [가정]
ZEUS_TOWER_ENTER_CLICK = (733, 500)
ZEUS_TOWER_EXIT_CHECK1_IMG = 'dpvlrznptmxm.png'
ZEUS_TOWER_EXIT_CHECK1_REGION = ZEUS_SUBQUEST_GATE_REGION_NORMAL  # [가정]
ZEUS_TOWER_EXIT_CHECK2_IMG = 'tjqmznptmxm.png'
ZEUS_TOWER_EXIT_CHECK2_REGION = ZEUS_SUBQUEST_GATE_REGION_NORMAL  # [가정]
ZEUS_TOWER_EXIT_POLL_SEC = 2.0  # [가정]
ZEUS_TOWER_FINISH_CLICK = (1000, 160)

# [미인식 시 드래그] 액션 이미지/서브퀘스트/메인퀘스트 아무것도 못 찾은 상태가 n초
# 넘으면, (900,150) 보정 클릭에 이어 이 드래그도 1회 실행합니다. (막혔을 때 화면을
# 조금 움직여서 인식이 다시 되게 하기 위함)
ZEUS_NO_MATCH_DRAG_START = (453, 346)
ZEUS_NO_MATCH_DRAG_END = (530, 466)

# gkdl.png - 있으면 대기 (클릭 안 함). 액션 이미지들이 전부 없을 때만 확인합니다.
ZEUS_WAIT_IMG = 'gkdl.png'
ZEUS_WAIT_REGION = (1176, 120, 1199, 186)

# dpvlrwlsgod.png - gkdl.png와 같은 자리에서 같이 나타난다고 하셔서 같은 영역을 씁니다.
# (실제로 다른 위치면 알려주세요) gkdl.png와 OR 조건으로 묶여서, 둘 중 하나라도 있으면 대기,
# 둘 다 없어야 미인식으로 취급합니다.
ZEUS_WAIT2_IMG = 'dpvlrwlsgod.png'
ZEUS_WAIT2_REGION = ZEUS_WAIT_REGION

# [미인식 타임아웃 보정 클릭] 액션 이미지 3개도, gkdl.png도 전부 안 보이는 상태가
# n초 이상 지속되면 이 좌표를 1회 클릭합니다. n초는 GUI 입력칸에서 바꿀 수 있습니다.
FALLBACK_CLICK_X = 900
FALLBACK_CLICK_Y = 150
DEFAULT_NO_IMAGE_TIMEOUT_SEC = 5.0

# [이미지 검색 오차범위 (tolerance)] AHK의 shade variation과 동일한 개념 (0~255).
ZEUS_TOLERANCE = 15
ZEUS_TRANSWHITE_TOLERANCE = 15  # transwhite 전용 이미지(apdlscpzm.png)에 쓰는 오차범위

# [클릭 좌표 랜덤화] 클릭할 때 찾은 위치의 중심에서 x, y 각각 이 범위만큼 무작위로 흔듭니다.
# (요청하신 대로 특별한 말이 없으면 기본값을 씁니다)
CLICK_JITTER_MIN = 3
CLICK_JITTER_MAX = 7

# [클릭 후 마우스 치우기] 클릭할 때마다 끝나고 나서 게임창(1280x800) 바깥의 이 좌표로
# 커서를 옮깁니다. 이미지 위에 커서가 계속 남아있으면 호버 상태 때문에 다음 인식이
# 꼬일 수 있어서입니다. 게임창 오른쪽 바로 바깥, 이미지테스터/GUI 창과도 안 겹치는
# 자리로 잡았습니다 (게임창 0~1280, 테스터 1350~, GUI 1620~).
MOUSE_PARK_X = GAME_WINDOW_X + GAME_WINDOW_W + 10
MOUSE_PARK_Y = 10

# [더블클릭 두 번째 클릭까지의 간격] 아두이노 펌웨어가 같은 버튼을 150ms 안에 다시
# 누르면 무시하도록 되어 있어서(디바운스), 그보다 여유 있게 잡습니다.
DOUBLE_CLICK_GAP_SEC = 0.15

# ==========================================================
# [설정 저장/불러오기] "저장" 버튼을 누르면 여기(zeus_config.json)에 저장되고,
# 다음에 켤 때 저장된 값으로 시작합니다. 파일이 없거나 깨져 있으면 기본값을 씁니다.
# region_image_tester.py의 tester_config.json과 같은 패턴입니다.
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "zeus_config.json")

# [로그 파일 / 정지 스크린샷 폴더] 미리 만들어두시면 확실하지만, 없어도 프로그램이
# 자동으로 만듭니다. 나중에 예측하기 힘든 상황을 로그+스크린샷으로 같이 보면서
# 확인하는 용도입니다.
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

DEFAULT_CONFIG = {
    "serial_port": PORT,
    "timeout_sec": DEFAULT_NO_IMAGE_TIMEOUT_SEC,
    "tolerance": ZEUS_TOLERANCE,
    "transwhite_tolerance": ZEUS_TRANSWHITE_TOLERANCE,
    "stuck_threshold": DEFAULT_STUCK_REPEAT_THRESHOLD,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_pc_name": "1",
    "telegram_send_interval": DEFAULT_SEND_INTERVAL,
    "telegram_event_stuck_enabled": True,
    "telegram_event_stuck_count": 2,
}


def load_config():
    """zeus_config.json을 읽어 기본값에 덮어씁니다. 파일이 없거나 깨져 있으면 기본값만 돌려줍니다."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for key in DEFAULT_CONFIG:
                if key in saved:
                    cfg[key] = saved[key]
    except Exception:
        pass  # 설정 파일이 깨져 있어도 기본값으로 정상 실행되어야 합니다.
    return cfg


def save_config(cfg):
    """현재 설정을 zeus_config.json에 저장합니다. 실패해도 프로그램은 계속 돌아야 하므로 예외를 삼킵니다."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False