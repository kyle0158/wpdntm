"""
[제우스 매크로 - GUI / 연결 / 클릭 실행부]
tkinter GUI, 아두이노 시리얼 연결, 실제 클릭/드래그를 물리적으로 실행하는 부분,
그리고 시작/일시정지/정지 같은 생명주기를 담당합니다.

"무엇을 언제 클릭할지" 판단하는 로직은 zeus_macro_logic.py의 MacroLogicMixin에 있고,
이미지/좌표 등 설정값은 zeus_constants.py에 있습니다. 이 세 파일 + telegram_notifier.py
+ image_search.py + region_image_tester.py가 세트로 같은 폴더에 있어야 합니다.

화면 구성:
  [상단]  아두이노 연결 상태(좌, 클릭하면 재연결) + 마우스 좌표(우, 화면 절대좌표, 100ms 갱신)
  [포트]  아두이노 포트 직접 입력 (자동인식 실패 시)
  [상태]  정지됨 / 동작 중 / 일시정지됨
  [설정]  미인식 대기 n초 / 오차범위(일반, transwhite) / 정체판정 반복횟수
  [버튼]  시작 / 일시정지 / 정지
  [도구]  이미지 테스터 열기 / 게임창 정렬 / 설정 저장 / 드래그 테스트
  [로그]  진행 상황

이 GUI 창 자체는 항상 위에 떠 있고(-topmost), 켜지면 화면 좌표 (1620, 0)에 자동으로
위치합니다. 게임창을 (0,0)에 1280x800으로 맞춰두면 딱 옆에 붙습니다.

[게임창 정렬] 제목에 "제우스: 오만의 신"이 포함된 창을 찾아서 (0,0)으로 옮기고
1280x800 크기로 바꿉니다. 프로그램을 켜면 이 정렬을 1회 자동으로(필수로) 실행합니다 -
게임을 먼저 켜둔 상태에서 이 매크로를 실행해야 정상적으로 맞춰집니다.

[드래그 테스트 버튼] 게임창 정렬을 1회 실행한 뒤, 미인식 시 쓰는 드래그
((453,346) -> (530,466))를 1회 실행해봅니다. 좌표/속도가 맞는지 확인하는 용도입니다.

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

[매크로 로직 개요] (전체 판단 순서는 zeus_macro_logic.py의 _zeus_tick 참고)
  0) 사냥중(anfdir0ro/anfdiron 중 하나라도 있을 때)에만 hp.png 확인, 없으면 귀환로직
  1) SIMPLE_CLICK_IMAGES -> OFFSET_CLICK_IMAGES -> CONDITIONAL_CLICK_IMAGES ->
     fpdlswj/wkehdrnao(자동구매)/tmzlfqnr(스킬북)/anfdir0ro(물약구매)/
     angksdmlxkq5cmd(무한의탑) 순으로 확인,
     있으면 즉시 처리
  1.5) 서브퀘스트(tjqmznptmxm/tjqm, NORMAL/RAID 두 영역 직접 순서대로 탐색)
  2) gkdl/dpvlrwlsgod 있으면 대기
  3) 다 없으면 미인식 타이머 -> n초 넘으면 창끄기 -> rhkfgh 확인 -> 보정클릭+드래그,
     연속 [정체판정]회 넘으면 텔레그램+정지
새 이미지를 추가하려면 zeus_constants.py의 리스트에 한 줄만 추가하면 됩니다 (자세한
설명은 그 파일 맨 위 docstring 참고).
"""
import atexit
import ctypes
import sys
import os
import random
import threading
import time

import pyautogui
import serial
import tkinter as tk
from tkinter import scrolledtext, ttk
import win32api
import win32con
import win32gui

import image_search
from telegram_notifier import TelegramNotifierMixin, DEFAULT_SEND_INTERVAL
from zeus_macro_logic import MacroLogicMixin
from zeus_constants import (
    list_ports, find_arduino_port,
    PORT, BAUD_RATE,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_X, WINDOW_Y,
    GAME_TITLE_PART, GAME_WINDOW_X, GAME_WINDOW_Y, GAME_WINDOW_W, GAME_WINDOW_H,
    LOOP_INTERVAL_SEC,
    ZEUS_TOLERANCE, ZEUS_TRANSWHITE_TOLERANCE, DEFAULT_STUCK_REPEAT_THRESHOLD,
    DEFAULT_NO_IMAGE_TIMEOUT_SEC, FALLBACK_CLICK_X, FALLBACK_CLICK_Y,
    ZEUS_NO_MATCH_DRAG_START, ZEUS_NO_MATCH_DRAG_END,
    CLICK_JITTER_MIN, CLICK_JITTER_MAX,
    MOUSE_PARK_X, MOUSE_PARK_Y, DOUBLE_CLICK_GAP_SEC,
    LOG_DIR, SCREENSHOT_DIR,
    load_config, save_config,
)

serial_lock = threading.Lock()


class ZeusController(MacroLogicMixin, TelegramNotifierMixin):
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

        frm_event = tk.LabelFrame(parent, text="자동 정지 알림")
        frm_event.pack(fill="x", padx=6, pady=3)
        row5 = tk.Frame(frm_event)
        row5.pack(fill="x", padx=5, pady=5)
        tk.Checkbutton(row5, text="자동 정지 시 알림 보내기", font=("", 8),
                       variable=self.tg_event_enabled_vars["stuck"]).pack(side="left")
        row6 = tk.Frame(frm_event)
        row6.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(row6, text="반복 전송", font=("", 7), fg="#666").pack(side="left")
        tk.Entry(row6, textvariable=self.tg_event_count_vars["stuck"], width=5,
                 justify="center").pack(side="left", padx=(3, 4))
        tk.Label(row6, text="회 (같은 알림을 몇 번 보낼지)", font=("", 7),
                 fg="#666").pack(side="left")
        tk.Label(frm_event,
                 text="정체(보정클릭+드래그 연속), HP 30초 미확인, 잡화상점 30초 미오픈 - "
                      "이 셋 중 하나라도 발생하면 여기서 보낸 뒤 정지합니다.",
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