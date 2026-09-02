"""
[제우스 매크로]
화면 구성:
  [상단]  아두이노 연결 상태(좌, 클릭하면 재연결) + 마우스 좌표(우, 화면 절대좌표, 100ms 갱신)
  [포트]  아두이노 포트 직접 입력 (자동인식 실패 시)
  [상태]  정지됨 / 동작 중 / 일시정지됨
  [설정]  미인식 대기 n초 / 오차범위(일반, transwhite) / 정체판정 반복횟수 - 아래 설명 참고
  [버튼]  시작 / 일시정지 / 정지
  [도구]  이미지 테스터 열기 / 게임창 정렬 / 설정 저장 / 드래그 테스트
  [로그]  진행 상황

이 GUI 창 자체는 항상 위에 떠 있고(-topmost), 켜지면 화면 좌표 (1620, 0)에 자동으로
위치합니다. 게임창을 (0,0)에 1280x800으로 맞춰두면 딱 옆에 붙습니다.

[게임창 정렬] 제목에 "제우스: 오만의 신"이 포함된 창을 찾아서 (0,0)으로 옮기고
1280x800 크기로 바꿉니다. 창을 못 찾으면(게임이 안 켜져 있거나 제목이 다르면) 로그에
이유가 남습니다. 프로그램을 켜면 이 정렬을 1회 자동으로(필수로) 실행합니다 - 게임을
먼저 켜둔 상태에서 이 매크로를 실행해야 정상적으로 맞춰집니다.

[드래그 테스트 버튼] 게임창 정렬을 1회 실행한 뒤, 미인식 시 쓰는 드래그
((453,346) -> (530,466))를 1회 실행해봅니다. 좌표/속도가 맞는지 확인하는 용도입니다.

[새 이미지 추가하는 방법 - 여기가 핵심입니다]
  - "찾으면 그냥 클릭"만 하면 되는 이미지 -> SIMPLE_CLICK_IMAGES 리스트에 한 줄만 추가
    (파일명, 검색영역, transwhite여부)
  - "왼쪽위 기준으로 x/y를 특정 범위만큼 밀어서" 클릭해야 하는 이미지 -> OFFSET_CLICK_IMAGES에
    한 줄만 추가 (파일명, 검색영역, transwhite여부, x오프셋범위, y오프셋범위)
  - "다른 이미지가 없을 때만" 클릭해야 하는 이미지 -> CONDITIONAL_CLICK_IMAGES에 한 줄만
    추가 (파일명, 검색영역, transwhite여부, 없어야하는이미지, 그영역, 그transwhite여부)
  - 더블클릭/여러 단계/대기처럼 특수한 동작이 필요한 이미지만 개별 핸들러(_handle_* 함수)로
    따로 만들면 됩니다. (fpdlswj, wkehdrnao(자동구매), tmzlfqnr(스킬북)가 이 경우)

[이미지 종류 / 영역]
  단순 클릭 (SIMPLE_CLICK_IMAGES, 리스트 순서 = 확인 우선순위):
    - apdlscpzm.png (transwhite) - (1144,124,1183,381)
    - dhksfy.png                 - (561,266,735,355)
    - skip.png                   - (1141,44,1256,97)
    - tnfkr.png                  - (508,42,835,153)
    - wkdckr.png (transwhite)    - (749,362,982,487)
    - ghkrdls.png                - (694,471,778,530)
    - tnfkr1.png                 - (1102,715,1183,759)

  오프셋 클릭 (OFFSET_CLICK_IMAGES, 단순 클릭 다음 순서):
    - xbxhfldjf.png (transwhite)  - (824,181,857,400)   - 왼쪽위 기준 x+30~40, y+5~10

  조건부 클릭 (CONDITIONAL_CLICK_IMAGES, 오프셋 클릭 다음 순서):
    - skrkrl2.png - (17,44,82,99) - tnfkr.png가 없을 때만 클릭

  연속 동작(시퀀스, 개별 핸들러):
    - fpdlswj.png     - (35,229,294,310)   - 더블클릭 3번 + 10초 대기 (아래 참고)
    - wkehdrnao.png   - (287,701,412,771)  - 고정좌표 6클릭 + 반복클릭 (자동구매)
    - tmzlfqnr.png    - (28,117,108,203)   - 고정좌표 3클릭 + 창끄기 (스킬북)

  서브퀘스트 (메인퀘스트(gkdl.png)보다 먼저 확인, 아래 [서브퀘스트] 참고):
    - tjqmznptmxm.png (게이트) - (821,185,860,221)   - 클릭 안 함, 서브퀘스트 존재 여부만 확인
    - tjqm.png (체크)          - (1183,180,1200,243) - 보이면 대기, n초 안 보이면 (945,215) 클릭

  레이드 게이트 (서브퀘스트보다 먼저 확인, 아래 [레이드 게이트] 참고):
    - fpdlem.png (transwhite) - (914,187,1005,242) - 클릭 안 함, 있으면 서브퀘스트 로직 생략

  대기(클릭 안 함):
    - gkdl.png         - (1176,120,1199,186)
    - dpvlrwlsgod.png  - (1176,120,1199,186, gkdl.png와 동일 영역)

  보정 클릭 직전에만 확인:
    - rhkfgh.png - (10,33,1269,788) (아래 [보정 클릭 전 rhkfgh 확인] 참고)

[fpdlswj.png 연속 동작] (_handle_fpdlswj_sequence)
  발견되면 아래 순서를 전부 실행한 뒤에야 다음 턴으로 넘어갑니다 (하나의 '행동'):
    1) fpdlswj.png 위치 더블클릭
    2) (1065,735) 더블클릭
    3) (740,500) 더블클릭
    4) 10초 대기 (정지 버튼을 누르면 대기 중에도 바로 멈춥니다)

[서브퀘스트] tjqmznptmxm.png는 "서브퀘스트가 지금 떠 있다"는 표시로만 씁니다 (그 자체는
클릭 안 함). gkdl.png(메인퀘스트) 로직보다 먼저 확인해서, 서브퀘스트가 떠 있는 동안은
메인퀘스트 쪽을 아예 확인하지 않고 이 분기만 처리합니다 ("서브퀘스트가 있으면 서브퀘스트
먼저"):
  - tjqm.png가 보이면: 대기 (gkdl.png 있을 때와 같은 맥락)
  - tjqm.png가 [미인식 대기] n초 동안 안 보이면: (945,215) 1회 클릭
  - tjqmznptmxm.png 자체가 안 보이면: 서브퀘스트가 없는 것이므로 메인퀘스트 쪽으로 넘어감
[미인식 대기] n초 입력칸은 gkdl.png 타임아웃과 tjqm.png 타임아웃에 공통으로 적용됩니다
(단, 두 타이머는 서로 별개로 셉니다 - 서브퀘스트 대기 중이라고 메인퀘스트 타이머가 같이
줄어들거나 하지 않습니다).

[레이드 게이트] fpdlem.png(transwhite)가 보이면 - 서브퀘스트(위 [서브퀘스트]) 로직
전체를 이번 턴에 건너뛰고 바로 메인퀘스트(gkdl.png 등) 쪽으로 넘어갑니다. 레이드 중엔
서브퀘스트 판단 자체가 의미가 없어서입니다. fpdlem.png 자체는 클릭 대상이 아닙니다.

[보정 클릭 전 rhkfgh 확인] gkdl.png/dpvlrwlsgod.png 타임아웃으로 (900,150)을 보정
클릭하기 '직전'에 rhkfgh.png를 한 번 더 확인합니다. rhkfgh.png가 떠 있는 상태에서
보정 클릭을 하면 다른 화면으로 넘어가버리기 때문에, 떠 있으면 이번엔 클릭을 건너뛰고
미인식 타이머를 리셋해서 대기시간을 늘립니다 (사라질 때까지 계속 미룸).

[보정 클릭 + 드래그] rhkfgh 확인까지 통과하면 (900,150)을 클릭하고, 곧바로 화면 드래그
((453,346) -> (530,466))도 1회 실행합니다 (막혔을 때 화면을 조금 움직여서 인식이 다시
되게 하기 위함). 이 둘이 '정체판정' 카운트를 공유합니다 - 중간에 다른 이미지가 하나도
안 감지된 채로 이 보정 클릭+드래그가 [정체판정] 횟수만큼 연속되면 텔레그램 알림을
보내고 매크로를 정지합니다.

[매크로 로직] (_zeus_tick, 1초마다 1회)
  1) SIMPLE_CLICK_IMAGES -> OFFSET_CLICK_IMAGES -> CONDITIONAL_CLICK_IMAGES ->
     fpdlswj.png -> wkehdrnao.png -> tmzlfqnr.png 순서로 확인합니다. 이 중 하나라도
     보이면(조건부는 조건까지 만족해야) 그 즉시 클릭(또는 연속 동작)하고 이번 턴은
     끝냅니다. (gkdl.png/dpvlrwlsgod.png가 같이 보이고 있어도 이들이 있으면 무조건
     처리합니다 - "대기 중에도 다른 이미지가 나오면 클릭해야 한다"는 요청 반영)
  1.5) 위가 다 없으면 [서브퀘스트]를 확인합니다. tjqmznptmxm.png가 보이면 이번 턴은
     서브퀘스트만 처리하고 아래 2)/3)(메인퀘스트)은 아예 안 봅니다.
  2) 서브퀘스트도 없는데 gkdl.png 또는 dpvlrwlsgod.png가 보이면 - 대기 (둘 중 하나만
     있어도 대기 - OR 조건)
  3) 위가 다 없고 gkdl.png, dpvlrwlsgod.png도 둘 다 없는 상태(AND 조건 - 둘 다 없어야
     '미인식'으로 취급)가 [미인식 대기 n초] 이상 계속되면, 화면 (900,150) 위치를
     1회 클릭합니다 (막혔을 때 보정용). n초는 GUI에서 직접 입력해 바꿀 수 있습니다
     (기본값 5초).
  - 위 1)~3) 중 하나라도 감지/클릭이 일어나면 '미인식 지속시간' 타이머가 그 시점으로
    리셋됩니다. gkdl.png만 보이는 상태가 계속돼도 "뭔가 인식은 되고 있는 상태"라
    타이머가 리셋됩니다 (즉, n초 타임아웃은 gkdl도 없고 액션 이미지도 없을 때만 셉니다).

  이미지 검색은 image_search를 씁니다. transwhite=True인 이미지는 원본 단계 없이
  image_search.locate_transwhite로 바로 찾습니다. 나머지는
  image_search.locate_smart(원본 -> 실패시 transwhite 순서)를 씁니다.

  클릭은 찾은 위치의 중심(또는 900,150 같은 고정 좌표)에서 x, y를 각각 3~7px
  무작위로 흔든 좌표를 씁니다(사람이 누르는 것처럼 매번 살짝 다른 자리를 누르기
  위함). 다르게 흔들고 싶으면 _click_box_jittered / _click_point_jittered 호출 시
  jitter_min/jitter_max를 따로 넘기면 됩니다.

[클릭 후 마우스 치우기] 클릭(또는 더블클릭)이 끝나면 커서를 게임창(1280x800) 바로
바깥의 (MOUSE_PARK_X, MOUSE_PARK_Y)로 옮깁니다. 커서가 이미지 위에 계속 남아있으면
게임 UI가 호버 상태로 바뀌어서 다음 인식이 꼬일 수 있어서입니다. 더블클릭은 두 번의
클릭 사이에는 치우지 않고(같은 자리를 유지해야 더블클릭으로 인식되므로), 두 클릭이
다 끝난 뒤에만 치웁니다.

[상태 흐름]
  IDLE(정지) --시작--> RUNNING(동작 중) --일시정지--> PAUSED --시작(재개)--> RUNNING
  RUNNING/PAUSED --정지--> IDLE

- 시작을 누르면 별도 스레드(daemon)에서 run_loop()가 돌기 시작합니다.
- 일시정지는 루프 스레드를 죽이지 않고 대기만 시킵니다 (다시 누르면 이어서 진행하며,
  미인식 타이머도 그 시점으로 다시 리셋됩니다 - 정지해뒀던 시간까지 n초에 포함되면 안 되니까요).
- 정지는 루프를 완전히 끝냅니다. 다시 시작하려면 '시작'을 다시 눌러야 합니다.

[클릭 방식]
main.py와 같은 아두이노 프로토콜(M1P = 왼쪽클릭 누름, M1R = 뗌)을 그대로 씁니다.
click_at(x, y)가 먼저 win32api.SetCursorPos로 화면 절대좌표로 커서를 옮긴 뒤,
시리얼로 눌렀다 뗍니다.

[로그 파일 / 정지 스크린샷] 프로그램을 켤 때마다 logs/ 폴더에 세션 로그 파일이 하나
새로 생기고(zeus_log_YYYYMMDD_HHMMSS.txt), 화면 로그창에 찍히는 모든 내용이 그대로
같이 남습니다. '정지'가 될 때는(수동으로 눌렀든, 오류/정체 감지로 자동으로 멈췄든 - on_stop()을
거치는 모든 경우) 화면 전체를 캡처해서 screenshots/ 폴더에도 저장합니다
(stop_YYYYMMDD_HHMMSS.png). 로그 파일과 스크린샷 파일명의 타임스탬프가 같은 순간에
찍히니, 나중에 예측하기 힘든 상황이 생기면 둘을 같이 보면서(필요하면 이 대화에 올려서)
어떤 상황이었는지 확인할 수 있습니다.
"""
import atexit
import ctypes
import sys
import json
import os
import random
import threading
import time

import pyautogui
import serial
try:
    from serial.tools import list_ports
except Exception:
    list_ports = None
import tkinter as tk
from tkinter import scrolledtext, ttk
import win32api
import win32con
import win32gui

import image_search  # noqa: F401  (다음 단계: run_loop 안에서 image_search.click_smart 사용 예정)
from telegram_notifier import TelegramNotifierMixin, DEFAULT_SEND_INTERVAL

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

# [창끄기] gkdl.png 타임아웃으로 보정 클릭(900,150)을 실행하기 '직전'에 처리하는 정리
# 동작 모음입니다. 나중에 항목이 더 추가될 수 있어서 별도로 분리해 뒀습니다.
#   - dlsqpsxhflx.png가 있으면 그 이미지를 클릭
#   - skrkrl.png가 있으면 (1222,70)을 클릭
ZEUS_CHANGKKEUGI1_IMG = 'dlsqpsxhflx.png'
ZEUS_CHANGKKEUGI1_REGION = (1197, 109, 1251, 160)
ZEUS_CHANGKKEUGI2_IMG = 'skrkrl.png'
ZEUS_CHANGKKEUGI2_REGION = (1130, 712, 1198, 789)
ZEUS_CHANGKKEUGI2_CLICK = (1222, 70)

# [정체 감지] 보정 클릭(900,150)이 연속 이 횟수 이상 발생하면(=중간에 아무 진전도 없었으면)
# 텔레그램으로 알리고 매크로를 정지합니다. GUI에서 값을 바꿀 수 있습니다.
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
# ==========================================================
ZEUS_SUBQUEST_GATE_IMG = 'tjqmznptmxm.png'
ZEUS_SUBQUEST_GATE_REGION = (821, 185, 860, 221)
ZEUS_SUBQUEST_CHECK_IMG = 'tjqm.png'
ZEUS_SUBQUEST_CHECK_REGION = (1183, 180, 1200, 243)
ZEUS_SUBQUEST_CLICK = (945, 215)

# fpdlem.png(레이드, transwhite) - 있으면 서브퀘스트(tjqm.png/tjqmznptmxm.png) 관련
# 로직을 이번 턴에 건너뛰고 바로 메인퀘스트(gkdl.png 등) 쪽으로 넘어갑니다. 레이드
# 이미지 자체는 클릭 대상이 아니라 '서브퀘스트를 생략해야 하는지' 확인하는 게이트입니다.
ZEUS_RAID_GATE_IMG = 'fpdlem.png'
ZEUS_RAID_GATE_REGION = (914, 187, 1005, 242)

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


serial_lock = threading.Lock()


class ZeusController(TelegramNotifierMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("제우스 매크로")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{WINDOW_X}+{WINDOW_Y}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)  # 항상 위 (끄고 싶으면 이 줄을 지우면 됩니다)

        # [로그 파일] 프로그램을 켤 때마다 logs/ 폴더에 파일을 하나 새로 만들어서, 화면
        # 로그창에 찍히는 모든 내용을 그대로 같이 남깁니다. 나중에 이 파일을 보면서
        # (필요하면 Claude한테 물어보면서) 어떤 상황이었는지 확인하는 용도입니다.
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except Exception:
            pass
        self._log_file_path = os.path.join(LOG_DIR, f"zeus_log_{time.strftime('%Y%m%d_%H%M%S')}.txt")

        # [설정 불러오기] zeus_config.json에 저장된 값이 있으면 그걸로, 없으면 기본값으로
        # 시작합니다. "저장" 버튼(save_settings)을 누르면 이 self.cfg가 파일에 다시 쓰입니다.
        self.cfg = load_config()

        self.ser = None
        self.port_var = tk.StringVar(value=self.cfg.get("serial_port", PORT))
        self.mouse_pos_var = tk.StringVar(value="X: 0, Y: 0")
        self.timeout_sec_var = tk.StringVar(value=str(self.cfg.get("timeout_sec", DEFAULT_NO_IMAGE_TIMEOUT_SEC)))
        self.tolerance_var = tk.StringVar(value=str(self.cfg.get("tolerance", ZEUS_TOLERANCE)))
        self.transwhite_tolerance_var = tk.StringVar(
            value=str(self.cfg.get("transwhite_tolerance", ZEUS_TRANSWHITE_TOLERANCE)))
        self.stuck_threshold_var = tk.StringVar(
            value=str(self.cfg.get("stuck_threshold", DEFAULT_STUCK_REPEAT_THRESHOLD)))

        # [텔레그램 설정용 GUI 변수] telegram_notifier.py가 tg_{key}_var 이름으로 찾습니다.
        self.tg_bot_token_var = tk.StringVar(value=self.cfg.get("telegram_bot_token", ""))
        self.tg_chat_id_var = tk.StringVar(value=self.cfg.get("telegram_chat_id", ""))
        self.tg_pc_name_var = tk.StringVar(value=self.cfg.get("telegram_pc_name", "1"))
        self.tg_interval_var = tk.StringVar(
            value=str(self.cfg.get("telegram_send_interval", DEFAULT_SEND_INTERVAL)))
        # [정체 알림 이벤트] 'stuck' 하나만 씁니다 (아래 [정체 감지] 참고).
        self.tg_event_enabled_vars = {
            "stuck": tk.BooleanVar(value=bool(self.cfg.get("telegram_event_stuck_enabled", True)))
        }
        self.tg_event_count_vars = {
            "stuck": tk.StringVar(value=str(self.cfg.get("telegram_event_stuck_count", 2)))
        }

        # [미인식 지속시간 타이머] 액션 이미지/gkdl.png가 하나도 안 보이는 상태가
        # 언제부터 이어지고 있는지. run_loop 시작/재개 시점에 초기화됩니다.
        self._last_activity_time = time.time()
        # [정체 감지용] 보정 클릭(900,150)이 '중간에 진전 없이' 몇 번 연속으로 발생했는지.
        self._fallback_click_streak = 0
        # [서브퀘스트용] tjqm.png가 안 보이기 시작한 시각. None이면 아직 안 재는 중.
        self._subquest_wait_start = None

        # [상태] IDLE(정지) / RUNNING(동작중) / PAUSED(일시정지)
        self.state = "IDLE"
        self._loop_thread = None

        self._setup_ui()
        self.connect_serial()
        self._update_mouse_position()
        self.init_telegram()  # 텔레그램 전송용 큐/워커 스레드 시작

        # [필수 창정렬] 켜질 때 게임창 정렬을 1회 실행합니다. 게임이 아직 안 켜져
        # 있으면 실패 로그만 남고, 이후 "🖥 창정렬" 버튼으로 수동으로 다시 하면 됩니다.
        self.position_game_window()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        atexit.register(self.cleanup)

    # ------------------------------------------------------
    # GUI 구성
    # ------------------------------------------------------
    def _setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        tab_macro = tk.Frame(notebook)
        tab_telegram = tk.Frame(notebook)
        notebook.add(tab_macro, text="매크로")
        notebook.add(tab_telegram, text="텔레그램")

        self._setup_macro_tab(tab_macro)
        self._setup_telegram_tab(tab_telegram)

    def _setup_macro_tab(self, parent):
        # 상단: 아두이노 연결 상태(좌) + 마우스 좌표(우)
        frm_top = tk.Frame(parent)
        frm_top.pack(fill="x", padx=5, pady=(5, 0))
        self.lbl_serial = tk.Label(frm_top, text="", font=("", 8, "bold"),
                                    bd=1, relief=tk.FLAT, cursor="hand2", pady=2, anchor="w")
        self.lbl_serial.pack(side="left", fill="x", expand=True)
        self.lbl_serial.bind("<Button-1>", self.retry_serial)
        tk.Label(frm_top, textvariable=self.mouse_pos_var, font=("Consolas", 8),
                 fg="#555555", width=16, anchor="e").pack(side="right")

        # 포트 직접 지정 (자동 인식이 실패했을 때 여기 입력하고 상태 표시줄을 클릭하면 재연결)
        frm_port = tk.Frame(parent)
        frm_port.pack(fill="x", padx=5, pady=(0, 3))
        tk.Label(frm_port, text="포트", font=("", 8)).pack(side="left")
        tk.Entry(frm_port, textvariable=self.port_var, width=8).pack(side="left", padx=4)
        tk.Label(frm_port, text="(자동인식 실패시 직접 입력 후 위 상태줄 클릭)",
                 font=("", 7), fg="#666").pack(side="left")

        # 상태 표시
        self.lbl_state = tk.Label(parent, text="정지됨", font=("", 12, "bold"),
                                   fg="#555", pady=8)
        self.lbl_state.pack(fill="x", padx=5)

        # 미인식 대기 n초 (아무 이미지도 안 보일 때 보정 클릭까지 기다리는 시간)
        frm_timeout = tk.Frame(parent)
        frm_timeout.pack(fill="x", padx=5, pady=(0, 3))
        tk.Label(frm_timeout, text="미인식 대기", font=("", 8)).pack(side="left")
        tk.Entry(frm_timeout, textvariable=self.timeout_sec_var, width=5,
                 justify="center").pack(side="left", padx=4)
        tk.Label(frm_timeout, text=f"초 (넘으면 {FALLBACK_CLICK_X},{FALLBACK_CLICK_Y} 1회 클릭)",
                 font=("", 7), fg="#666").pack(side="left")

        # 오차범위 (tolerance, 일반 / transwhite 각각 따로) - AHK shade variation과 동일 개념
        frm_conf = tk.Frame(parent)
        frm_conf.pack(fill="x", padx=5, pady=(0, 3))
        tk.Label(frm_conf, text="오차범위", font=("", 8)).pack(side="left")
        tk.Label(frm_conf, text="일반", font=("", 7), fg="#666").pack(side="left", padx=(6, 2))
        tk.Entry(frm_conf, textvariable=self.tolerance_var, width=5,
                 justify="center").pack(side="left")
        tk.Label(frm_conf, text="transwhite", font=("", 7), fg="#666").pack(side="left", padx=(8, 2))
        tk.Entry(frm_conf, textvariable=self.transwhite_tolerance_var, width=5,
                 justify="center").pack(side="left")

        # 정체판정 반복 횟수 (n회 이상 연속 보정클릭 -> 텔레그램 알림 + 정지)
        frm_stuck = tk.Frame(parent)
        frm_stuck.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(frm_stuck, text="정체판정", font=("", 8)).pack(side="left")
        tk.Entry(frm_stuck, textvariable=self.stuck_threshold_var, width=5,
                 justify="center").pack(side="left", padx=4)
        tk.Label(frm_stuck, text="회 (보정클릭+드래그 연속되면 텔레그램+정지)",
                 font=("", 7), fg="#666").pack(side="left")

        # 시작 / 일시정지 / 정지
        frm_btn = tk.Frame(parent)
        frm_btn.pack(fill="x", padx=5, pady=(0, 5))
        self.btn_start = tk.Button(frm_btn, text="▶ 시작", command=self.on_start,
                                    bg="#d5f5e3", font=("", 10, "bold"), height=2)
        self.btn_start.pack(side="left", fill="both", expand=True, padx=(0, 2))
        self.btn_pause = tk.Button(frm_btn, text="⏸ 일시정지", command=self.on_pause,
                                    bg="#fdebd0", font=("", 10, "bold"), height=2, state="disabled")
        self.btn_pause.pack(side="left", fill="both", expand=True, padx=2)
        self.btn_stop = tk.Button(frm_btn, text="⏹ 정지", command=self.on_stop,
                                   bg="#f5b7b1", font=("", 10, "bold"), height=2, state="disabled")
        self.btn_stop.pack(side="left", fill="both", expand=True, padx=(2, 0))

        # 도구: 이미지 테스터 + 게임창 정렬 + 설정 저장
        frm_tools = tk.Frame(parent)
        frm_tools.pack(fill="x", padx=5, pady=(0, 5))
        tk.Button(frm_tools, text="🔍 테스터", command=self.open_image_tester,
                  bg="#f4ecf7").pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(frm_tools, text="🖥 창정렬", command=self.position_game_window,
                  bg="#eaf2f8").pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(frm_tools, text="💾 저장", command=self.save_settings,
                  bg="#fef9e7").pack(side="left", fill="x", expand=True, padx=(2, 0))

        # 드래그 테스트 (창정렬 1회 실행 후 드래그 1회 실행)
        tk.Button(parent, text="🧪 드래그 테스트 (창정렬 후 드래그)", command=self.test_drag,
                  bg="#eafaf1").pack(fill="x", padx=5, pady=(0, 5))

        # 로그
        log_frame = tk.LabelFrame(parent, text="로그")
        log_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap="word",
                                                    font=("Consolas", 8),
                                                    bg="#1e1e1e", fg="#eaeaea")
        self.log_text.pack(fill="both", expand=True, padx=3, pady=3)

    def _setup_telegram_tab(self, parent):
        frm_conn = tk.LabelFrame(parent, text="연결 정보")
        frm_conn.pack(fill="x", padx=6, pady=(6, 3))

        row1 = tk.Frame(frm_conn)
        row1.pack(fill="x", padx=5, pady=(5, 2))
        tk.Label(row1, text="봇 토큰", font=("", 8), width=7, anchor="w").pack(side="left")
        tk.Entry(row1, textvariable=self.tg_bot_token_var).pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(frm_conn)
        row2.pack(fill="x", padx=5, pady=2)
        tk.Label(row2, text="채팅 ID", font=("", 8), width=7, anchor="w").pack(side="left")
        tk.Entry(row2, textvariable=self.tg_chat_id_var).pack(side="left", fill="x", expand=True)

        row3 = tk.Frame(frm_conn)
        row3.pack(fill="x", padx=5, pady=2)
        tk.Label(row3, text="PC 이름", font=("", 8), width=7, anchor="w").pack(side="left")
        tk.Entry(row3, textvariable=self.tg_pc_name_var, width=8).pack(side="left")
        tk.Label(row3, text="(메시지 앞에 [n번PC]로 붙습니다)", font=("", 7),
                 fg="#666").pack(side="left", padx=(6, 0))

        row4 = tk.Frame(frm_conn)
        row4.pack(fill="x", padx=5, pady=(2, 5))
        tk.Label(row4, text="전송간격", font=("", 8), width=7, anchor="w").pack(side="left")
        tk.Entry(row4, textvariable=self.tg_interval_var, width=6).pack(side="left")
        tk.Label(row4, text="초 (같은 알림 여러 번 보낼 때 간격)", font=("", 7),
                 fg="#666").pack(side="left", padx=(6, 0))

        tk.Button(frm_conn, text="테스트 전송", command=self.notify_test,
                  bg="#eaf2f8").pack(fill="x", padx=5, pady=(0, 6))

        frm_event = tk.LabelFrame(parent, text="정체 감지 알림")
        frm_event.pack(fill="x", padx=6, pady=3)
        row5 = tk.Frame(frm_event)
        row5.pack(fill="x", padx=5, pady=5)
        tk.Checkbutton(row5, text="정체 감지 시 알림 보내기", font=("", 8),
                       variable=self.tg_event_enabled_vars["stuck"]).pack(side="left")
        row6 = tk.Frame(frm_event)
        row6.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(row6, text="반복 전송", font=("", 7), fg="#666").pack(side="left")
        tk.Entry(row6, textvariable=self.tg_event_count_vars["stuck"], width=5,
                 justify="center").pack(side="left", padx=(3, 4))
        tk.Label(row6, text="회 (같은 알림을 몇 번 보낼지)", font=("", 7),
                 fg="#666").pack(side="left")
        tk.Label(frm_event,
                 text="'정체판정' 회수(매크로 탭)만큼 보정클릭+드래그가 연속되면 여기서 보낸 뒤 정지합니다.",
                 font=("", 7), fg="#666", wraplength=WINDOW_WIDTH - 20,
                 justify="left").pack(fill="x", padx=5, pady=(0, 6))

        tk.Button(parent, text="💾 설정 저장", command=self.save_settings,
                  bg="#fef9e7").pack(fill="x", padx=6, pady=(0, 6))

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        try:
            self.log_text.insert("end", line + "\n")
            self.log_text.see("end")
        except Exception:
            pass  # 창이 닫혔거나 위젯이 아직 없어도 파일 기록은 계속되어야 합니다.
        self._write_log_file(line)

    def _write_log_file(self, line):
        """화면 로그창에 찍히는 모든 줄을 logs/ 폴더의 세션 파일에도 그대로 남깁니다."""
        try:
            with open(self._log_file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass  # 파일 기록이 실패해도 매크로 동작 자체에는 영향이 없어야 합니다.

    # ------------------------------------------------------
    # 마우스 좌표 (100ms마다 갱신, 화면 절대좌표 - 게임창 위치와 무관)
    # ------------------------------------------------------
    def _update_mouse_position(self):
        try:
            x, y = pyautogui.position()
            self.mouse_pos_var.set(f"X: {x}, Y: {y}")
        except Exception:
            pass
        try:
            self.root.after(100, self._update_mouse_position)
        except Exception:
            pass  # 창이 닫힌 경우

    # ------------------------------------------------------
    # 이미지 테스터 (같은 폴더의 region_image_tester.py 재사용)
    # ------------------------------------------------------
    def open_image_tester(self):
        try:
            import region_image_tester
            region_image_tester.open_tester_window(self.root)
            self.log("- 이미지 테스터를 열었습니다")
        except Exception as e:
            self.log(f"- 이미지 테스터를 열지 못했습니다: {e}")

    # ------------------------------------------------------
    # 게임창 정렬 (제목에 GAME_TITLE_PART가 포함된 창을 0,0으로 옮기고 1600x800으로 변경)
    # ------------------------------------------------------
    def position_game_window(self):
        """제목에 GAME_TITLE_PART가 포함된 창을 찾아 (0,0)으로 옮기고 크기를 맞춥니다.
        성공하면 True, 창을 못 찾았거나 이동/크기변경에 실패하면 False를 돌려줍니다."""
        hwnds = []
        win32gui.EnumWindows(
            lambda h, l: l.append(h) if (win32gui.IsWindowVisible(h)
                                          and GAME_TITLE_PART in win32gui.GetWindowText(h)) else None,
            hwnds)
        if not hwnds:
            self.log(f"- 게임 창을 못 찾았습니다 (제목에 '{GAME_TITLE_PART}' 포함된 창이 없음)")
            return False
        hwnd = hwnds[0]
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 최대화/최소화 상태면 먼저 일반 창으로
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, GAME_WINDOW_X, GAME_WINDOW_Y,
                                   GAME_WINDOW_W, GAME_WINDOW_H, win32con.SWP_SHOWWINDOW)
            self.log(f"- 게임창을 ({GAME_WINDOW_X},{GAME_WINDOW_Y})로 이동, "
                     f"{GAME_WINDOW_W}x{GAME_WINDOW_H}로 크기 변경했습니다")
            return True
        except Exception as e:
            self.log(f"- 게임창 이동/크기 변경 실패: {e}")
            # [자주 나오는 원인] winerror 5 = 액세스 거부. 대상 창(게임)이 이 프로그램보다
            # 높은 권한(관리자 등)으로 떠 있으면 Windows가 창 조작 자체를 막습니다(UIPI).
            # 게임을 관리자 권한으로 켜셨다면, 이 매크로도 관리자 권한으로 실행해서 권한을
            # 맞춰야 합니다 (.pyw 파일 우클릭 -> 관리자 권한으로 실행).
            winerror = getattr(e, "winerror", None)
            if winerror is None and getattr(e, "args", None):
                # pywintypes.error는 args가 (winerror, 함수명, 설명) 형태인 경우가 많습니다.
                first_arg = e.args[0]
                if isinstance(first_arg, int):
                    winerror = first_arg
            if winerror == 5 or "액세스가 거부" in str(e) or "access is denied" in str(e).lower():
                self.log("  -> [원인 추정] 권한 차이(winerror 5, 액세스 거부)입니다. 게임이 "
                         "관리자 권한으로 켜져 있으면 이 매크로도 관리자 권한으로 실행해야 "
                         "창을 옮길 수 있습니다 (.pyw 파일을 마우스 우클릭 -> 관리자 권한으로 실행)")
            return False

    def test_drag(self):
        """드래그 테스트 버튼: 게임창 정렬을 1회 실행한 뒤, 미인식 시 쓰는 드래그
        (ZEUS_NO_MATCH_DRAG_START -> END)를 1회 실행해서 좌표/느낌을 확인해볼 수 있습니다."""
        self.log("- 드래그 테스트 시작")
        aligned = self.position_game_window()
        if not aligned:
            self.log("  -> 창정렬에 실패했지만, 좌표 확인을 위해 드래그는 그대로 진행합니다")
        self.log(f"- 드래그 {ZEUS_NO_MATCH_DRAG_START} -> {ZEUS_NO_MATCH_DRAG_END}")
        self.drag_from_to(ZEUS_NO_MATCH_DRAG_START, ZEUS_NO_MATCH_DRAG_END)
        self.log("- 드래그 테스트 종료")

    # ------------------------------------------------------
    # 아두이노 연결
    # ------------------------------------------------------
    def safe_write(self, data):
        """시리얼 데이터 안전 전송. 연결 안 된 상태면 조용히 무시하지 않고 로그로 남깁니다."""
        if not (self.ser and self.ser.is_open):
            self._safe_write_fail_count = getattr(self, '_safe_write_fail_count', 0) + 1
            if self._safe_write_fail_count in (1, 50, 200):  # 도배 방지, 몇 번만 남김
                self.log(f"- [진단] 아두이노 연결이 안 된 상태에서 전송 시도: {data}")
            return
        with serial_lock:
            try:
                self.ser.write((data + '\n').encode('latin-1'))
                self.ser.flush()
            except Exception as e:
                self.log(f"- [진단] 시리얼 전송 실패 ({data}): {e}")

    def connect_serial(self):
        target_port = (self.port_var.get() or "").strip() or PORT
        try:
            self.ser = serial.Serial(target_port, BAUD_RATE, timeout=0.1)
            self.log(f"- 아두이노 연결됨 ({target_port})")
        except Exception as e:
            self.ser = None
            self.log(f"- 아두이노 연결 실패 ({target_port}): {e}")

            # [자동 인식] 지정한 포트로 실패하면, 연결된 장치 중 아두이노로 보이는
            # 포트를 자동으로 찾아 한 번 더 시도합니다. PC마다 포트 번호(COM3, COM4
            # 등)가 다른 문제를 여기서 해결합니다.
            auto_port = find_arduino_port()
            if auto_port and auto_port != target_port:
                self.log(f"- 자동 인식 시도: {auto_port}")
                try:
                    self.ser = serial.Serial(auto_port, BAUD_RATE, timeout=0.1)
                    self.log(f"- 아두이노 연결됨 ({auto_port}) - 자동으로 찾았습니다. "
                             f"'저장' 버튼을 누르면 다음에도 이 포트로 바로 붙습니다")
                    self.port_var.set(auto_port)
                except Exception as e2:
                    self.ser = None
                    self.log(f"- 자동 인식으로도 연결 실패 ({auto_port}): {e2}")

            if not self.is_serial_ready():
                self.log("  -> 포트를 다른 프로그램이 쓰고 있거나, 케이블/드라이버 문제일 수 있습니다")
                self._log_available_ports()
        self.refresh_serial_status()

    def _log_available_ports(self):
        """진단용: 지금 이 컴퓨터에 연결된 시리얼 포트 목록을 로그로 남깁니다.
        여기 나온 포트 이름을 매크로 탭의 '포트' 입력칸에 직접 넣고 재연결하면 됩니다."""
        if list_ports is None:
            self.log("  -> (포트 목록을 확인하려면 pyserial의 list_ports가 필요합니다)")
            return
        try:
            ports = list(list_ports.comports())
        except Exception:
            return
        if not ports:
            self.log("  -> 이 컴퓨터에 연결된 시리얼 포트가 하나도 없습니다")
            return
        self.log("  -> 연결된 포트 목록:")
        for p in ports:
            self.log(f"     {p.device} - {p.description}")

    def is_serial_ready(self):
        return bool(self.ser and self.ser.is_open)

    def refresh_serial_status(self):
        try:
            if self.is_serial_ready():
                actual_port = self.ser.port
                self.lbl_serial.config(text=f"● 아두이노 연결됨 ({actual_port})",
                                        fg="#145a32", bg="#d5f5e3")
            else:
                shown_port = (self.port_var.get() or "").strip() or PORT
                self.lbl_serial.config(text=f"⚠ 아두이노 미연결 ({shown_port}) — 클릭해서 재연결",
                                        fg="#ffffff", bg="#c0392b")
        except Exception:
            pass

    def retry_serial(self, event=None):
        if self.is_serial_ready():
            self.log(f"- 아두이노는 이미 연결되어 있습니다 ({self.ser.port})")
            return
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.log("- 아두이노 재연결 시도")
        self.connect_serial()

    # ------------------------------------------------------
    # 클릭 (화면 절대좌표로 커서 이동 후 아두이노로 클릭)
    # image_search.click_smart(self, 이미지명, region, tolerance)가 이걸 그대로 호출합니다.
    # 클릭이 끝나면 기본적으로 게임창 밖(MOUSE_PARK_X, MOUSE_PARK_Y)으로 커서를 치웁니다.
    # ------------------------------------------------------
    def click_at(self, x, y, hold_sec=0.05, park_after=True):
        try:
            win32api.SetCursorPos((int(x), int(y)))
        except Exception as e:
            self.log(f"- [진단] 커서 이동 실패: {e}")
            return
        time.sleep(0.05)  # 커서가 실제로 옮겨갈 시간을 살짝 줍니다.
        self.safe_write("M1P")
        time.sleep(hold_sec)
        self.safe_write("M1R")
        if park_after:
            # [중요] 시리얼 전송 -> 아두이노가 실제로 버튼을 떼기까지는 약간의 지연이
            # 있습니다. 이 딜레이 없이 바로 커서를 치우면, 실제 릴리즈가 처리되는
            # 시점엔 이미 커서가 다른 곳으로 가 있어서 클릭이 안 먹히거나 엉뚱한
            # 곳을 클릭한 걸로 처리될 수 있습니다. 릴리즈가 확실히 끝난 뒤에 치웁니다.
            time.sleep(0.08)
            self._park_mouse()

    def double_click_at(self, x, y, hold_sec=0.05, gap_sec=DOUBLE_CLICK_GAP_SEC, park_after=True):
        """같은 좌표를 두 번 클릭합니다. 두 클릭 사이에는 마우스를 치우지 않습니다
        (자리를 유지해야 더블클릭으로 인식되므로). gap_sec은 아두이노 디바운스(150ms)보다
        여유 있게 잡아야 두 번째 클릭이 실제로 눌립니다."""
        try:
            win32api.SetCursorPos((int(x), int(y)))
        except Exception as e:
            self.log(f"- [진단] 커서 이동 실패: {e}")
            return
        time.sleep(0.05)
        self.safe_write("M1P")
        time.sleep(hold_sec)
        self.safe_write("M1R")
        time.sleep(gap_sec)
        self.safe_write("M1P")
        time.sleep(hold_sec)
        self.safe_write("M1R")
        if park_after:
            # click_at과 같은 이유로, 두 번째 릴리즈가 실제로 처리될 시간을 준 뒤에 치웁니다.
            time.sleep(0.08)
            self._park_mouse()

    def _park_mouse(self):
        """클릭 후 커서를 게임창(1280x800) 바깥의 안전한 자리로 옮깁니다."""
        try:
            win32api.SetCursorPos((MOUSE_PARK_X, MOUSE_PARK_Y))
        except Exception as e:
            self.log(f"- [진단] 마우스 치우기 실패: {e}")

    def drag_from_to(self, start, end, steps=12, step_delay=0.02, hold_settle=0.05, park_after=True):
        """start 좌표에서 마우스를 누른 채로 end 좌표까지 서서히 이동시켜 드래그합니다
        (화면/지도 이동 등에 씁니다). steps/step_delay로 부드러움과 속도를 조절할 수
        있습니다."""
        sx, sy = start
        ex, ey = end
        try:
            win32api.SetCursorPos((int(sx), int(sy)))
        except Exception as e:
            self.log(f"- [진단] 드래그 시작 위치 이동 실패: {e}")
            return
        time.sleep(0.05)
        self.safe_write("M1P")
        time.sleep(hold_settle)  # 누른 상태가 실제로 적용될 시간을 살짝 줍니다.
        for i in range(1, steps + 1):
            t = i / steps
            cx = sx + (ex - sx) * t
            cy = sy + (ey - sy) * t
            try:
                win32api.SetCursorPos((int(round(cx)), int(round(cy))))
            except Exception:
                pass
            time.sleep(step_delay)
        self.safe_write("M1R")
        if park_after:
            time.sleep(0.08)  # click_at과 같은 이유로, 릴리즈가 실제로 처리될 시간을 준 뒤에 치웁니다.
            self._park_mouse()

    # ------------------------------------------------------
    # 시작 / 일시정지 / 정지
    # ------------------------------------------------------
    def on_start(self):
        if self.state == "RUNNING":
            return
        if self.state == "IDLE":
            self.state = "RUNNING"
            self._last_activity_time = time.time()
            self._fallback_click_streak = 0
            self._subquest_wait_start = None
            self.log("- 시작")
            self._loop_thread = threading.Thread(target=self.run_loop, daemon=True)
            self._loop_thread.start()
        elif self.state == "PAUSED":
            self.state = "RUNNING"
            self._last_activity_time = time.time()  # 정지해있던 시간이 n초에 포함되지 않도록 리셋
            self._fallback_click_streak = 0
            self._subquest_wait_start = None
            self.log("- 재개")
        self._refresh_buttons()

    def on_pause(self):
        if self.state != "RUNNING":
            return
        self.state = "PAUSED"
        self.log("- 일시정지")
        self._refresh_buttons()

    def on_stop(self):
        if self.state == "IDLE":
            return
        self.state = "IDLE"
        self.log("- 정지")
        self._save_stop_screenshot()
        self._refresh_buttons()

    def _save_stop_screenshot(self):
        """정지되는 순간 화면 전체를 캡처해서 screenshots/ 폴더에 남깁니다. 로그 파일과
        같은 시각(파일명의 타임스탬프)이니, 둘을 같이 보면 정지 당시 어떤 상황이었는지
        확인할 수 있습니다."""
        try:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join(SCREENSHOT_DIR, f"stop_{ts}.png")
            img = pyautogui.screenshot()
            img.save(path)
            self.log(f"- 정지 시점 스크린샷 저장: {path}")
        except Exception as e:
            self.log(f"- [진단] 정지 스크린샷 저장 실패: {e}")

    def _refresh_buttons(self):
        label = {"IDLE": "정지됨", "RUNNING": "동작 중", "PAUSED": "일시정지됨"}[self.state]
        color = {"IDLE": "#555", "RUNNING": "#145a32", "PAUSED": "#af601a"}[self.state]
        self.lbl_state.config(text=label, fg=color)

        self.btn_start.config(state="disabled" if self.state == "RUNNING" else "normal",
                               text="▶ 재개" if self.state == "PAUSED" else "▶ 시작")
        self.btn_pause.config(state="normal" if self.state == "RUNNING" else "disabled")
        self.btn_stop.config(state="disabled" if self.state == "IDLE" else "normal")

    # ------------------------------------------------------
    # 실제 매크로 루프
    # ------------------------------------------------------
    def run_loop(self):
        """state가 IDLE이 될 때까지 돕니다. PAUSED면 쉬기만 하고, RUNNING이면 한 바퀴(_zeus_tick) 돕니다."""
        while self.state != "IDLE":
            if self.state == "PAUSED":
                time.sleep(0.2)
                continue

            try:
                self._zeus_tick()
            except Exception as e:
                self.log(f"- [오류] 루프 중 예외: {e}")
                self.root.after(0, self.on_stop)
                break

            time.sleep(LOOP_INTERVAL_SEC)

    def get_no_image_timeout_sec(self):
        try:
            v = float(self.timeout_sec_var.get())
            if v > 0:
                return v
        except Exception:
            pass
        return DEFAULT_NO_IMAGE_TIMEOUT_SEC

    def get_tolerance(self):
        try:
            v = int(float(self.tolerance_var.get()))
            if 0 <= v <= 255:
                return v
        except Exception:
            pass
        return ZEUS_TOLERANCE

    def get_transwhite_tolerance(self):
        try:
            v = int(float(self.transwhite_tolerance_var.get()))
            if 0 <= v <= 255:
                return v
        except Exception:
            pass
        return ZEUS_TRANSWHITE_TOLERANCE

    def get_stuck_repeat_threshold(self):
        try:
            v = int(float(self.stuck_threshold_var.get()))
            if v >= 1:
                return v
        except Exception:
            pass
        return DEFAULT_STUCK_REPEAT_THRESHOLD

    def _mark_activity(self):
        """뭔가 인식되거나 처리됐다는 뜻입니다. 미인식 타이머와 '정체 연속 카운트'를
        같이 리셋합니다 (진짜 진전이 있었을 때만 부릅니다 - rhkfgh로 보류된 경우는
        해당 안 됨)."""
        self._last_activity_time = time.time()
        self._fallback_click_streak = 0

    # ------------------------------------------------------
    # 설정 저장 (매크로 탭 + 텔레그램 탭 값을 전부 zeus_config.json에 저장)
    # ------------------------------------------------------
    def save_settings(self):
        cfg = {
            "serial_port": (self.port_var.get() or "").strip() or PORT,
            "timeout_sec": self.get_no_image_timeout_sec(),
            "tolerance": self.get_tolerance(),
            "transwhite_tolerance": self.get_transwhite_tolerance(),
            "stuck_threshold": self.get_stuck_repeat_threshold(),
            "telegram_bot_token": self.tg_bot_token_var.get(),
            "telegram_chat_id": self.tg_chat_id_var.get(),
            "telegram_pc_name": self.tg_pc_name_var.get(),
            "telegram_send_interval": self._tg_send_interval(),
            "telegram_event_stuck_enabled": bool(self.tg_event_enabled_vars["stuck"].get()),
            "telegram_event_stuck_count": self._tg_event_count("stuck", 2),
        }
        self.cfg = cfg
        if save_config(cfg):
            self.log("- 설정을 저장했습니다 (zeus_config.json) - 다음에 켤 때 이 값으로 시작합니다")
        else:
            self.log("- 설정 저장 실패 (zeus_config.json에 쓸 수 없습니다)")

    def _zeus_tick(self):
        """한 바퀴치 판단 + 클릭.

        순서:
          1) SIMPLE_CLICK_IMAGES / OFFSET_CLICK_IMAGES / CONDITIONAL_CLICK_IMAGES
             (각 리스트 순서대로) / fpdlswj.png / wkehdrnao.png / tmzlfqnr.png - 있으면
             즉시 클릭(연속 동작 이미지는 시퀀스 수행) (gkdl.png/dpvlrwlsgod.png 여부와 무관)
          1.5) 위가 다 없으면 fpdlem.png(레이드) 확인 - 있으면 서브퀘스트 생략. 없으면
               서브퀘스트(tjqmznptmxm.png) 확인. 있으면 이번 턴은 서브퀘스트만 처리하고
               메인퀘스트(2, 3)는 아예 안 봅니다.
          2) 서브퀘스트도 없는데 gkdl.png 또는 dpvlrwlsgod.png가 있으면 - 대기 (OR 조건)
          3) 위가 다 없고 gkdl.png, dpvlrwlsgod.png도 둘 다 없으면(AND 조건) -
             미인식 지속시간을 재서, n초 넘으면 [창끄기] -> rhkfgh 확인 -> (900,150) 보정
             클릭 -> 화면 드래그 순서로 처리하고, 이 보정 클릭+드래그가 연속 [정체판정]회
             이상 나오면 텔레그램 알림 후 정지
        """
        now = time.time()
        tol = self.get_tolerance()
        tw_tol = self.get_transwhite_tolerance()

        # 1) 단순 클릭 이미지들 - 새 이미지 추가는 SIMPLE_CLICK_IMAGES에 한 줄만 넣으면 됩니다.
        for img_name, region, transwhite in SIMPLE_CLICK_IMAGES:
            if transwhite:
                box = image_search.locate_transwhite(img_name, region, tolerance=tw_tol)
            else:
                box = image_search.locate_smart(img_name, region,
                                                 tolerance=tol, transwhite_tolerance=tw_tol)
            if box:
                self._click_box_jittered(box)
                self.log(f"- {img_name} 발견 -> 클릭")
                self._mark_activity()
                return

        # 오프셋 클릭 이미지들 - 새 이미지 추가는 OFFSET_CLICK_IMAGES에 한 줄만 넣으면 됩니다.
        for img_name, region, transwhite, x_off, y_off in OFFSET_CLICK_IMAGES:
            if transwhite:
                box = image_search.locate_transwhite(img_name, region, tolerance=tw_tol)
            else:
                box = image_search.locate_smart(img_name, region,
                                                 tolerance=tol, transwhite_tolerance=tw_tol)
            if box:
                self._click_box_offset(box, x_off, y_off)
                self.log(f"- {img_name} 발견 -> 클릭 (오프셋)")
                self._mark_activity()
                return

        # 조건부 클릭 이미지들 - "다른 이미지가 없을 때만" 클릭. 새 항목은
        # CONDITIONAL_CLICK_IMAGES에 한 줄만 추가하면 됩니다.
        for img_name, region, transwhite, cond_img, cond_region, cond_transwhite \
                in CONDITIONAL_CLICK_IMAGES:
            if cond_transwhite:
                cond_found = image_search.locate_transwhite(cond_img, cond_region, tolerance=tw_tol)
            else:
                cond_found = image_search.locate_smart(cond_img, cond_region,
                                                         tolerance=tol, transwhite_tolerance=tw_tol)
            if cond_found:
                continue  # 조건 이미지가 있으니 이 항목은 건너뛰고 다음 조건부 이미지를 봅니다.

            if transwhite:
                box = image_search.locate_transwhite(img_name, region, tolerance=tw_tol)
            else:
                box = image_search.locate_smart(img_name, region,
                                                 tolerance=tol, transwhite_tolerance=tw_tol)
            if box:
                self._click_box_jittered(box)
                self.log(f"- {img_name} 발견 -> 클릭 ({cond_img} 없음 조건 만족)")
                self._mark_activity()
                return

        # fpdlswj.png - 발견되면 정해진 연속 동작(더블클릭 3번 + 10초 대기)을 수행합니다.
        box = image_search.locate_smart(ZEUS_FPDLSWJ_IMG, ZEUS_FPDLSWJ_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._handle_fpdlswj_sequence(box)
            self._mark_activity()  # 시퀀스가 오래 걸리므로 시간을 다시 잽니다
            return

        # wkehdrnao.png(자동구매) - 발견되면 정해진 연속 동작(고정좌표 6클릭 + 반복클릭)을 수행합니다.
        box = image_search.locate_smart(ZEUS_AUTOBUY_IMG, ZEUS_AUTOBUY_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._handle_autobuy_sequence(box)
            self._mark_activity()
            return

        # tmzlfqnr.png(스킬북) - 발견되면 고정좌표 3클릭 + 창끄기 로직을 수행합니다.
        box = image_search.locate_smart(ZEUS_SKILLBOOK_IMG, ZEUS_SKILLBOOK_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._handle_skillbook_sequence(box, tol, tw_tol)
            self._mark_activity()
            return

        # [레이드 게이트] fpdlem.png(레이드)가 보이면 서브퀘스트(tjqm/tjqmznptmxm) 관련
        # 로직 전체를 이번 턴에 건너뜁니다 - 레이드 중엔 서브퀘스트 판단이 의미가 없어서입니다.
        raid_active = image_search.locate_transwhite(ZEUS_RAID_GATE_IMG, ZEUS_RAID_GATE_REGION,
                                                       tolerance=tw_tol)
        if raid_active:
            self._subquest_wait_start = None  # 나중에 다시 켤 때 오래된 타이머가 안 남게 정리
        else:
            # [서브퀘스트] 메인퀘스트(gkdl.png) 쪽보다 먼저 확인합니다. tjqmznptmxm.png가
            # 보이면 서브퀘스트가 진행 중이라는 뜻이라, 이번 턴은 서브퀘스트만 처리하고
            # 메인퀘스트 쪽(gkdl.png 등)은 아예 확인하지 않습니다.
            if image_search.locate_smart(ZEUS_SUBQUEST_GATE_IMG, ZEUS_SUBQUEST_GATE_REGION,
                                          tolerance=tol, transwhite_tolerance=tw_tol):
                if image_search.locate_smart(ZEUS_SUBQUEST_CHECK_IMG, ZEUS_SUBQUEST_CHECK_REGION,
                                              tolerance=tol, transwhite_tolerance=tw_tol):
                    self.log("- tjqm 발견 - 서브퀘스트 대기")
                    self._subquest_wait_start = None  # 다음에 또 안 보이면 처음부터 다시 잽니다.
                    self._mark_activity()
                    return

                # tjqm.png가 안 보입니다 - 언제부터 안 보였는지 재서 n초 넘으면 보정 클릭.
                if self._subquest_wait_start is None:
                    self._subquest_wait_start = now
                timeout = self.get_no_image_timeout_sec()  # gkdl.png와 같은 입력칸(n초)을 공유합니다.
                elapsed_sub = now - self._subquest_wait_start
                if elapsed_sub >= timeout:
                    self.log(f"- tjqm 미인식 {timeout:.1f}초 -> 서브퀘스트 보정 클릭 "
                             f"{ZEUS_SUBQUEST_CLICK}")
                    self._click_point_jittered(*ZEUS_SUBQUEST_CLICK)
                    self._subquest_wait_start = now  # 매 턴마다 계속 클릭하지 않도록 리셋
                    self._mark_activity()
                # 아직 n초가 안 지났으면 이번 턴은 그냥 대기 (메인퀘스트로 안 넘어감)
                return

            # tjqmznptmxm.png 자체가 안 보이면 서브퀘스트가 없는 것이므로 타이머만 정리합니다.
            self._subquest_wait_start = None

        # (raid_active였거나, 서브퀘스트가 없었으면) 메인퀘스트(gkdl.png 등) 쪽으로 진행합니다.

        # 2) gkdl.png 또는 dpvlrwlsgod.png - 액션 이미지가 전부 없을 때만 확인.
        #    둘 중 하나라도 있으면 대기 (클릭 안 함). 둘 다 없어야 3)의 미인식으로 취급합니다.
        if image_search.locate_smart(ZEUS_WAIT_IMG, ZEUS_WAIT_REGION,
                                      tolerance=tol, transwhite_tolerance=tw_tol):
            self.log("- gkdl 발견 - 대기")
            self._mark_activity()
            return

        if image_search.locate_smart(ZEUS_WAIT2_IMG, ZEUS_WAIT2_REGION,
                                      tolerance=tol, transwhite_tolerance=tw_tol):
            self.log("- dpvlrwlsgod 발견 - 대기")
            self._mark_activity()
            return

        # 3) 여기까지 왔다는 건 아무것도 안 보인다는 뜻입니다. n초 넘게 지속되면 보정 클릭.
        timeout = self.get_no_image_timeout_sec()
        elapsed = now - self._last_activity_time
        if elapsed >= timeout:
            # [창끄기] 보정 클릭 직전에 처리해야 하는 정리 동작들 (나중에 항목이 늘어날 수 있음)
            self._perform_chang_kkeugi(tol, tw_tol)

            # [클릭 직전 확인] rhkfgh.png가 떠 있는 상태에서 (900,150)을 클릭하면 다른
            # 화면으로 넘어가버리므로, 클릭 바로 직전에 한 번 더 확인합니다. 떠 있으면
            # 이번엔 클릭을 건너뛰고 타이머를 리셋해서 대기시간을 늘립니다 (사라질 때까지
            # 계속 미룸). 이 경우는 '진짜 진전'이 아니라서 정체 카운트는 건드리지 않습니다.
            if image_search.locate_smart(ZEUS_RHKFGH_IMG, ZEUS_RHKFGH_REGION,
                                          tolerance=tol, transwhite_tolerance=tw_tol):
                self.log("- rhkfgh 발견 -> 보정 클릭 보류, 대기시간 연장")
                self._last_activity_time = time.time()
                return

            self.log(f"- {timeout:.1f}초간 아무 이미지도 인식 안 됨 -> 보정 클릭 "
                     f"({FALLBACK_CLICK_X},{FALLBACK_CLICK_Y})")
            self._click_point_jittered(FALLBACK_CLICK_X, FALLBACK_CLICK_Y)

            self.log(f"- 이어서 화면 드래그 {ZEUS_NO_MATCH_DRAG_START} -> {ZEUS_NO_MATCH_DRAG_END}")
            self.drag_from_to(ZEUS_NO_MATCH_DRAG_START, ZEUS_NO_MATCH_DRAG_END)

            self._last_activity_time = time.time()  # 매 턴마다 계속 반복하지 않도록 리셋

            # [정체 감지] 이 보정 클릭+드래그가 '중간에 진전 없이' 연속으로 몇 번째인지 셉니다.
            # 다른 이미지가 하나라도 감지되면(_mark_activity) 이 카운트는 0으로 돌아갑니다.
            self._fallback_click_streak += 1
            threshold = self.get_stuck_repeat_threshold()
            if self._fallback_click_streak >= threshold:
                msg = (f"제우스 매크로가 정체된 것 같습니다 (보정 클릭+드래그가 "
                       f"{self._fallback_click_streak}회 연속 발생). 매크로를 정지합니다.")
                self.log(f"- [경고] {msg}")
                self.notify_event("stuck", msg, once=False)
                self.root.after(0, self.on_stop)
                return

    def _perform_chang_kkeugi(self, tol, tw_tol):
        """'창끄기' - 보정 클릭(gkdl 타임아웃) 실행 직전에 처리하는 정리 동작 모음입니다.
        나중에 항목이 더 추가될 수 있어서 별도 함수로 분리해 뒀습니다. (지금은 2개)"""
        box = image_search.locate_smart(ZEUS_CHANGKKEUGI1_IMG, ZEUS_CHANGKKEUGI1_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._click_box_jittered(box)
            self.log("- [창끄기] dlsqpsxhflx 발견 -> 클릭")

        box2 = image_search.locate_smart(ZEUS_CHANGKKEUGI2_IMG, ZEUS_CHANGKKEUGI2_REGION,
                                          tolerance=tol, transwhite_tolerance=tw_tol)
        if box2:
            self._click_point_jittered(*ZEUS_CHANGKKEUGI2_CLICK)
            self.log(f"- [창끄기] skrkrl 발견 -> {ZEUS_CHANGKKEUGI2_CLICK} 클릭")

    def _handle_autobuy_sequence(self, box):
        """wkehdrnao.png(자동구매) 발견 시 정해진 순서를 한 번에 수행합니다:
          1~6) 고정 좌표 6곳을 순서대로 1회씩 클릭
          7) ghkausdlstlr.png(화면인식)가 보일 때까지 (50,65)를 딜레이를 두고 반복 클릭
        [가정] 반복 클릭 사이 딜레이(ZEUS_AUTOBUY_REPEAT_DELAY_SEC)와 최대 반복 횟수
        (ZEUS_AUTOBUY_REPEAT_MAX)는 지정해주신 값이 없어서 1초/30회로 임의로 잡았습니다."""
        self.log("- wkehdrnao(자동구매) 발견 -> 연속 동작 시작")
        for i, (x, y) in enumerate(ZEUS_AUTOBUY_CLICKS, 1):
            self._click_point_jittered(x, y)
            self.log(f"  {i}) ({x},{y}) 클릭 완료")

        tol = self.get_tolerance()
        tw_tol = self.get_transwhite_tolerance()
        self.log(f"  - ghkausdlstlr 인식될 때까지 {ZEUS_AUTOBUY_REPEAT_CLICK} 반복 클릭 시작")
        attempts = 0
        while self.state != "IDLE":
            found = image_search.locate_smart(ZEUS_AUTOBUY_WAIT_IMG, ZEUS_AUTOBUY_WAIT_REGION,
                                               tolerance=tol, transwhite_tolerance=tw_tol)
            if found:
                self.log(f"  - ghkausdlstlr 인식됨 (반복 {attempts}회 만에 완료)")
                break
            attempts += 1
            if attempts > ZEUS_AUTOBUY_REPEAT_MAX:
                self.log(f"  ⚠ ghkausdlstlr을 {ZEUS_AUTOBUY_REPEAT_MAX}번 반복해도 못 찾아 "
                         f"반복을 중단했습니다")
                break
            self._click_point_jittered(*ZEUS_AUTOBUY_REPEAT_CLICK)
            self._sleep_interruptible(ZEUS_AUTOBUY_REPEAT_DELAY_SEC)
        self.log("- wkehdrnao(자동구매) 연속 동작 종료")

    def _handle_skillbook_sequence(self, box, tol, tw_tol):
        """tmzlfqnr.png(스킬북) 발견 시 정해진 순서를 한 번에 수행합니다:
          1~3) 고정 좌표 3곳을 순서대로 1회씩 클릭
          4) 창끄기 로직 실행 (_perform_chang_kkeugi)"""
        self.log("- tmzlfqnr(스킬북) 발견 -> 연속 동작 시작")
        for i, (x, y) in enumerate(ZEUS_SKILLBOOK_CLICKS, 1):
            self._click_point_jittered(x, y)
            self.log(f"  {i}) ({x},{y}) 클릭 완료")

        self._perform_chang_kkeugi(tol, tw_tol)
        self.log("- tmzlfqnr(스킬북) 연속 동작 종료")

    def _click_point_jittered(self, x, y, jitter_min=CLICK_JITTER_MIN, jitter_max=CLICK_JITTER_MAX):
        """지정한 좌표에서 x, y를 각각 무작위로 살짝 흔들어서 클릭합니다."""
        dx = random.randint(jitter_min, jitter_max) * random.choice((-1, 1))
        dy = random.randint(jitter_min, jitter_max) * random.choice((-1, 1))
        self.click_at(x + dx, y + dy)

    def _click_box_jittered(self, box, jitter_min=CLICK_JITTER_MIN, jitter_max=CLICK_JITTER_MAX):
        """찾은 위치의 중심을 기준으로 x, y를 각각 무작위로 살짝 흔들어서 클릭합니다.
        (같은 자리만 반복해서 클릭하지 않도록 하기 위함)"""
        cx = box.left + box.width // 2
        cy = box.top + box.height // 2
        self._click_point_jittered(cx, cy, jitter_min, jitter_max)

    def _click_box_offset(self, box, x_offset_range, y_offset_range):
        """찾은 위치의 왼쪽위(left, top)를 기준으로, x/y 각각 지정된 범위만큼 '한 방향으로만'
        더해서 클릭합니다. (_click_box_jittered와 다르게 중앙 기준 대칭 흔들림이 아니라
        방향이 있는 오프셋 - 예: xbxhfldjf.png처럼 이미지 안의 특정 위치를 눌러야 할 때)
        x_offset_range/y_offset_range: (min, max) - 이 범위 안에서 무작위로 더할 값을 고릅니다."""
        dx = random.randint(x_offset_range[0], x_offset_range[1])
        dy = random.randint(y_offset_range[0], y_offset_range[1])
        self.click_at(box.left + dx, box.top + dy)

    def _double_click_point_jittered(self, x, y, jitter_min=CLICK_JITTER_MIN, jitter_max=CLICK_JITTER_MAX):
        """지정한 좌표에서 x, y를 각각 무작위로 살짝 흔들어서 더블클릭합니다."""
        dx = random.randint(jitter_min, jitter_max) * random.choice((-1, 1))
        dy = random.randint(jitter_min, jitter_max) * random.choice((-1, 1))
        self.double_click_at(x + dx, y + dy)

    def _double_click_box_jittered(self, box, jitter_min=CLICK_JITTER_MIN, jitter_max=CLICK_JITTER_MAX):
        """찾은 위치의 중심을 기준으로 x, y를 각각 무작위로 살짝 흔들어서 더블클릭합니다."""
        cx = box.left + box.width // 2
        cy = box.top + box.height // 2
        self._double_click_point_jittered(cx, cy, jitter_min, jitter_max)

    def _sleep_interruptible(self, total_seconds, chunk=0.5):
        """total_seconds만큼 쉬되, 그 사이 '정지' 버튼이 눌리면(state가 IDLE이 되면)
        바로 멈춥니다. 10초처럼 긴 대기를 한 번에 sleep하면 정지 버튼이 안 먹는 것처럼
        보일 수 있어서 잘게 쪼개서 쉽니다."""
        remaining = total_seconds
        while remaining > 0 and self.state != "IDLE":
            t = min(chunk, remaining)
            time.sleep(t)
            remaining -= t

    def _handle_fpdlswj_sequence(self, box):
        """fpdlswj.png 발견 시 정해진 순서를 한 번에 수행합니다 (이 전체를 하나의 '행동'으로
        취급 - 도중에 다른 이미지 판단 없이 순서대로 실행됩니다):
          1) fpdlswj.png 위치 더블클릭
          2) (1065,735) 더블클릭
          3) (740,500) 더블클릭
          4) 10초 대기
        매 클릭 뒤에는 (더블클릭 자체가 끝난 뒤에) 마우스를 게임창 밖으로 치웁니다."""
        self.log("- fpdlswj 발견 -> 연속 동작 시작")

        self._double_click_box_jittered(box)
        self.log("  1) 이미지 위치 더블클릭 완료")

        self._double_click_point_jittered(*ZEUS_FPDLSWJ_STEP2)
        self.log(f"  2) {ZEUS_FPDLSWJ_STEP2} 더블클릭 완료")

        self._double_click_point_jittered(*ZEUS_FPDLSWJ_STEP3)
        self.log(f"  3) {ZEUS_FPDLSWJ_STEP3} 더블클릭 완료")

        self.log(f"  4) {ZEUS_FPDLSWJ_WAIT_SEC:.0f}초 대기")
        self._sleep_interruptible(ZEUS_FPDLSWJ_WAIT_SEC)
        self.log("- fpdlswj 연속 동작 종료")

    # ------------------------------------------------------
    # 종료 정리
    # ------------------------------------------------------
    def _on_close(self):
        self.cleanup()
        self.root.destroy()

    def cleanup(self):
        self.state = "IDLE"
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass


def is_admin():
    """지금 관리자 권한으로 돌고 있는지 확인합니다. 확인 자체가 안 되면(윈도우가
    아니거나 등) False로 봅니다."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    """관리자 권한이 아니면, 관리자 권한으로 자기 자신을 다시 실행합니다 (UAC 권한
    요청 창이 뜹니다). 성공적으로 새 프로세스를 띄웠으면 지금 프로세스는 바로
    종료합니다(True 반환). 이미 관리자 권한이거나, 사용자가 UAC 창에서 취소했거나,
    관리자 권한 요청 자체에 실패하면 아무것도 안 하고 넘어갑니다(False 반환) -
    이 경우 게임창 정렬처럼 관리자 권한이 필요한 기능만 못 쓸 수 있고, 나머지
    (이미지 인식/클릭/텔레그램 등)는 그대로 잘 동작합니다."""
    if is_admin():
        return False
    try:
        script_path = os.path.abspath(sys.argv[0])
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
        work_dir = os.path.dirname(script_path)
        # ShellExecuteW의 반환값이 32보다 크면 새 프로세스를 성공적으로 띄운 것입니다.
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script_path}" {params}'.strip(), work_dir, 1)
        if ret > 32:
            return True
    except Exception:
        pass
    return False


def main():
    # [관리자 권한 자동 요청] 게임창 정렬(SetWindowPos)은 게임이 관리자 권한으로 떠
    # 있으면 이 프로그램도 관리자 권한이어야 동작합니다. .pyw 파일은 우클릭 메뉴에
    # "관리자 권한으로 실행"이 아예 안 보이는 경우가 있어서, 여기서 직접 요청합니다.
    if relaunch_as_admin():
        return  # 관리자 권한으로 새 창이 떴으니, 지금 이 프로세스는 조용히 종료합니다.

    root = tk.Tk()
    app = ZeusController(root)
    app.log(f"- 관리자 권한: {'예' if is_admin() else '아니오 (게임창 정렬이 안 될 수 있습니다)'}")
    root.mainloop()


if __name__ == "__main__":
    main()