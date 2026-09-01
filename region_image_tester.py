"""
[이미지 서치 테스터]
- 화면에서 드래그로 검색 영역(x1,y1,x2,y2)을 지정합니다.
- 드래그로 캡처하거나 파일에서 불러와서 찾을 이미지를 지정합니다.
- 오차범위(tolerance, AHK ImageSearch의 shade variation과 동일한 개념)를 지정한 뒤
  "테스트 시작"으로, 그 영역 안에서 이미지를 찾습니다. 원본으로 못 찾으면(체크박스가
  켜져 있을 때) 흰 배경을 무시하는 transwhite 방식으로 한 번 더 찾습니다.
  여러 개가 발견되면 전부 표시하고 각각의 좌표를 로그로 남깁니다.
- 검색은 image_search 모듈(픽셀 값을 직접 비교하는 AHK 스타일 매칭)을 씁니다 -
  "명암 패턴이 비슷한가"가 아니라 "실제 색이 비슷한가"를 봅니다.
- 설정(영역/이미지경로/오차범위)은 저장 버튼으로 tester_config.json에 저장되고,
  다음 실행 시 그대로 불러옵니다.

[좌표 기준] 여기서 다루는 모든 좌표는 '화면 절대좌표'입니다. 모니터 좌상단이 (0,0)이며
게임 창 위치와 무관합니다. main.py의 캐릭터 전환/키나 체크 등도 같은 기준을 씁니다.

main.py의 '이미지 테스터' 버튼으로 열 수도 있고, 이 파일을 직접 실행해도 됩니다.
"""
import ctypes
import json
import os

import tkinter as tk
from tkinter import filedialog

import pyautogui
from PIL import Image, ImageTk

try:
    import image_search
    _IMAGE_SEARCH_AVAILABLE = True
    _IMAGE_SEARCH_IMPORT_ERROR = None
except Exception as _e:
    image_search = None
    _IMAGE_SEARCH_AVAILABLE = False
    _IMAGE_SEARCH_IMPORT_ERROR = str(_e)

# [DPI 설정] 디스플레이 배율에 따른 좌표 오차를 방지합니다. (본체 main.py와 동일)
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "tester_config.json")
TEMP_CAPTURE_PATH = os.path.join(BASE_DIR, "_tester_temp_capture.png")

# [창 크기/위치] 창의 좌상단 모서리가 (WINDOW_X, WINDOW_Y)에 오도록 배치합니다.
WINDOW_WIDTH = 330      # 폭이 좁거나 넓으면 이 숫자만 바꾸면 됩니다.
WINDOW_HEIGHT = 640
WINDOW_X = 1350         # 창 좌상단 X 좌표
WINDOW_Y = 225          # 창 좌상단 Y 좌표

MAX_MATCHES = 30        # 한 번에 표시/기록할 최대 인식 개수 (너무 많으면 로그가 넘칩니다)
BOX_DURATION = 3.0      # 인식 위치 빨간 박스가 화면에 머무는 시간(초)
BOX_BORDER = 3          # 빨간 테두리 두께(px)

DEFAULT_CONFIG = {
    "region": [0, 0, 300, 300],   # [x1, y1, x2, y2] - 화면 절대좌표
    "image_path": "",             # 마지막으로 저장/불러온 이미지 파일 경로
    "tolerance": 15,              # 오차범위 (AHK shade variation과 동일한 개념, 0~255)
    "show_boxes": True,           # 인식 위치를 화면에 표시할지
    "always_on_top": True,        # 창을 항상 최상단에 유지할지 (끄기 전까지 유지)
    "use_transwhite": True,       # 원본으로 못 찾으면 흰배경 투명(transwhite) 방식으로 재시도할지
    "transwhite_tolerance": 15,   # transwhite 단계의 오차범위
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k in DEFAULT_CONFIG:
                if k in saved:
                    cfg[k] = saved[k]
    except Exception:
        pass  # 설정 파일이 깨져 있어도 기본값으로 정상 실행되어야 합니다.
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def show_match_box(parent, x, y, w, h, duration=BOX_DURATION, color="red"):
    """지정한 화면 좌표에 '색깔 테두리'만 잠깐 띄웁니다. (기본 빨강 = 원본 검색,
    테스터에서는 transwhite로 찾은 결과를 파랑으로 구분해서 표시합니다)

    창 가운데를 도려내서(SetWindowRgn) 테두리만 남기므로, 안쪽은 게임 화면이 그대로 보이고
    마우스 클릭도 통과합니다. (debug_overlay.py와 같은 방식이며, 테스터는 단독 실행도
    가능해야 하므로 여기에 따로 구현해 두었습니다)"""
    try:
        overlay = tk.Toplevel(parent)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)

        pad = 3
        ow, oh = w + pad * 2, h + pad * 2
        overlay.geometry(f"{ow}x{oh}+{x - pad}+{y - pad}")
        overlay.configure(bg=color)
        tk.Canvas(overlay, width=ow, height=oh, bg=color,
                  highlightthickness=0, bd=0).pack(fill="both", expand=True)
        overlay.update_idletasks()

        gdi32, user32 = ctypes.windll.gdi32, ctypes.windll.user32
        gdi32.CreateRectRgn.restype = ctypes.c_void_p
        gdi32.CreateRectRgn.argtypes = [ctypes.c_int] * 4
        gdi32.CombineRgn.argtypes = [ctypes.c_void_p] * 3 + [ctypes.c_int]
        gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
        user32.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
        user32.GetAncestor.restype = ctypes.c_void_p
        user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]

        hwnd_top = user32.GetAncestor(overlay.winfo_id(), 2) or overlay.winfo_id()
        outer = gdi32.CreateRectRgn(0, 0, ow, oh)
        inner = gdi32.CreateRectRgn(BOX_BORDER, BOX_BORDER, ow - BOX_BORDER, oh - BOX_BORDER)
        gdi32.CombineRgn(outer, outer, inner, 4)   # RGN_DIFF
        user32.SetWindowRgn(hwnd_top, outer, True)
        gdi32.DeleteObject(inner)

        overlay.after(max(50, int(duration * 1000)), overlay.destroy)
    except Exception:
        pass


class RegionSelector:
    """화면 전체에 반투명 오버레이를 띄우고, 마우스 드래그로 사각형 영역을 선택하게 합니다.

    선택이 끝나면 on_done(region)을 호출합니다. region은 (x1, y1, x2, y2) 화면 절대좌표
    튜플이고, ESC로 취소하면 None을 넘깁니다."""

    def __init__(self, parent, on_done):
        self.on_done = on_done
        self.start = None
        self.rect_id = None

        screen_w, screen_h = pyautogui.size()

        self.top = tk.Toplevel(parent)
        self.top.overrideredirect(True)
        self.top.geometry(f"{screen_w}x{screen_h}+0+0")
        self.top.attributes("-topmost", True)
        self.top.attributes("-alpha", 0.25)
        self.top.configure(bg="black", cursor="crosshair")

        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.top.bind("<Escape>", lambda e: self._cancel())

        tk.Label(self.top, text="드래그해서 영역을 선택하세요  (ESC: 취소)",
                 fg="white", bg="black", font=("", 13, "bold")).place(relx=0.5, rely=0.03, anchor="n")

        self.top.focus_force()

    def _on_press(self, event):
        self.start = (event.x, event.y)
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                     outline="#ff3b3b", width=2)

    def _on_drag(self, event):
        if self.rect_id is None or self.start is None:
            return
        x0, y0 = self.start
        self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def _on_release(self, event):
        if self.start is None:
            self._cancel()
            return
        x0, y0 = self.start
        x1, y1 = event.x, event.y
        left, top = int(min(x0, x1)), int(min(y0, y1))
        right, bottom = int(max(x0, x1)), int(max(y0, y1))
        self.top.destroy()
        # 오버레이가 화면에서 완전히 사라진 뒤에 콜백을 실행합니다 (스크린샷을 찍는 경우 대비).
        self.canvas.after(150, lambda: self.on_done((left, top, right, bottom)))

    def _cancel(self):
        self.top.destroy()
        self.canvas.after(100, lambda: self.on_done(None))


class TesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 서치 테스터")
        # 창의 좌상단 모서리를 (WINDOW_X, WINDOW_Y)에 맞춥니다.
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{WINDOW_X}+{WINDOW_Y}")
        self.root.minsize(WINDOW_WIDTH, 540)

        self.cfg = load_config()
        self.region = list(self.cfg["region"])
        self.image_path = self.cfg["image_path"]
        self.captured_image = None   # PIL Image (미리보기/테스트용). 저장 전에도 테스트는 가능합니다.
        self.preview_photo = None    # PhotoImage 참조 유지용 (안 잡아두면 GC로 사라짐)

        self.tolerance_var = tk.StringVar(value=str(self.cfg["tolerance"]))
        self.show_boxes_var = tk.BooleanVar(value=bool(self.cfg["show_boxes"]))
        self.always_on_top_var = tk.BooleanVar(value=bool(self.cfg.get("always_on_top", True)))
        self.use_transwhite_var = tk.BooleanVar(value=bool(self.cfg.get("use_transwhite", True)))
        self.transwhite_tolerance_var = tk.StringVar(value=str(self.cfg.get("transwhite_tolerance", 15)))
        self.mouse_pos_var = tk.StringVar(value="X: 0, Y: 0")

        self._setup_ui()
        self._refresh_region_label()
        self._update_mouse_position()
        # [항상 위] 창을 켤 때 저장된 상태(기본값: 켬)를 바로 적용합니다.
        # 이후로는 체크박스를 끄기 전까지 계속 최상단을 유지합니다.
        self.apply_always_on_top()

        # 저장된 이미지 경로가 있으면 시작할 때 미리보기로 불러옵니다.
        if self.image_path and os.path.exists(self.image_path):
            try:
                self.captured_image = Image.open(self.image_path)
            except Exception:
                self.captured_image = None
        self._refresh_image_preview()

    # ------------------------------------------------------
    # GUI 구성
    # ------------------------------------------------------
    def _setup_ui(self):
        # 상단: 마우스 좌표 (화면 절대좌표, 게임창과 무관)
        frm_head = tk.Frame(self.root)
        frm_head.pack(fill="x", padx=6, pady=(4, 0))
        tk.Checkbutton(frm_head, text="📌 항상 위", variable=self.always_on_top_var,
                       command=self.apply_always_on_top, font=("", 8)).pack(side="left")
        tk.Label(frm_head, textvariable=self.mouse_pos_var, font=("Consolas", 9, "bold"),
                 fg="#333").pack(side="right")

        frm_head2 = tk.Frame(self.root)
        frm_head2.pack(fill="x", padx=6, pady=(0, 0))
        tk.Label(frm_head2, text="화면 절대좌표", font=("", 7), fg="#888").pack(side="right")

        # 1. 검색 영역
        frm_region = tk.LabelFrame(self.root, text="1. 검색 영역 (드래그로 지정)")
        frm_region.pack(fill="x", padx=6, pady=(4, 3))
        tk.Button(frm_region, text="🖱 범위 설정", command=self.start_region_select,
                  bg="#eaf2f8").pack(fill="x", padx=5, pady=(5, 2))
        tk.Label(frm_region, text="x1,y1,x2,y2  (선택해서 복사 가능)",
                 font=("", 7), fg="#666").pack(anchor="w", padx=5)
        self.region_entry = tk.Entry(frm_region, justify="center", font=("Consolas", 9))
        self.region_entry.pack(fill="x", padx=5, pady=(1, 5))

        # 2. 찾을 이미지
        frm_img = tk.LabelFrame(self.root, text="2. 찾을 이미지")
        frm_img.pack(fill="x", padx=6, pady=3)
        btn_row = tk.Frame(frm_img)
        btn_row.pack(fill="x", padx=5, pady=(5, 2))
        tk.Button(btn_row, text="📷 드래그 캡처", command=self.start_image_select,
                  bg="#eaf2f8").pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(btn_row, text="📂 파일 불러오기", command=self.load_image_from_file,
                  bg="#eaf2f8").pack(side="left", fill="x", expand=True, padx=(2, 0))

        self.preview_label = tk.Label(frm_img, text="(아직 이미지 없음)", bg="#1e1e1e", fg="#888",
                                       height=6)
        self.preview_label.pack(fill="x", padx=5, pady=2)

        tk.Button(frm_img, text="💾 이미지 저장 (다른 이름으로)", command=self.save_image_as,
                  bg="#fdebd0").pack(fill="x", padx=5, pady=(0, 2))
        self.image_path_label = tk.Label(frm_img, text="경로: (없음)", anchor="w", fg="#555",
                                          font=("", 7), wraplength=WINDOW_WIDTH - 30, justify="left")
        self.image_path_label.pack(fill="x", padx=5, pady=(0, 5))

        # 3. 오차범위 (tolerance, AHK shade variation과 동일한 개념) + 인식 위치 표시
        frm_conf = tk.LabelFrame(self.root, text="3. 오차범위 (tolerance, 0~255)")
        frm_conf.pack(fill="x", padx=6, pady=3)
        row = tk.Frame(frm_conf)
        row.pack(fill="x", padx=5, pady=5)
        tk.Entry(row, textvariable=self.tolerance_var, width=6, justify="center").pack(side="left")
        tk.Label(row, text="기본 15 (0=완전동일, 클수록 너그러움)", font=("", 7),
                 fg="#666").pack(side="left", padx=4)
        tk.Checkbutton(row, text="인식 위치 표시", variable=self.show_boxes_var,
                       font=("", 8)).pack(side="right")

        # 4. 흰배경 투명 (transwhite) - 원본으로 못 찾으면 흰색을 무시하고 한 번 더 찾습니다.
        frm_tw = tk.LabelFrame(self.root, text="4. 흰배경 투명 (transwhite)")
        frm_tw.pack(fill="x", padx=6, pady=3)
        row_tw = tk.Frame(frm_tw)
        row_tw.pack(fill="x", padx=5, pady=(5, 2))
        tk.Checkbutton(row_tw, text="원본으로 못 찾으면 재시도", variable=self.use_transwhite_var,
                       font=("", 8)).pack(side="left")
        row_tw2 = tk.Frame(frm_tw)
        row_tw2.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(row_tw2, text="오차범위", font=("", 7), fg="#666").pack(side="left")
        tk.Entry(row_tw2, textvariable=self.transwhite_tolerance_var, width=6,
                 justify="center").pack(side="left", padx=(3, 4))
        tk.Label(row_tw2, text="기본 15 (파란 테두리로 표시됨)", font=("", 7),
                 fg="#3498db").pack(side="left")
        if not _IMAGE_SEARCH_AVAILABLE:
            tk.Label(frm_tw, text=f"⚠ image_search 모듈을 못 불러왔습니다: {_IMAGE_SEARCH_IMPORT_ERROR}",
                     font=("", 7), fg="#c0392b", wraplength=WINDOW_WIDTH - 20,
                     justify="left").pack(fill="x", padx=5, pady=(0, 4))

        # 실행 / 저장
        frm_run = tk.Frame(self.root)
        frm_run.pack(fill="x", padx=6, pady=5)
        tk.Button(frm_run, text="▶ 테스트 시작", command=self.run_test,
                  bg="#d5f5e3", font=("", 9, "bold"), height=2).pack(side="left", fill="both", expand=True, padx=(0, 2))
        tk.Button(frm_run, text="💾 설정 저장", command=self.save_settings,
                  bg="#fdebd0", font=("", 9, "bold"), height=2).pack(side="left", fill="both", expand=True, padx=(2, 0))

        # 로그
        frm_log = tk.LabelFrame(self.root, text="로그")
        frm_log.pack(fill="both", expand=True, padx=6, pady=(3, 6))
        self.log_text = tk.Text(frm_log, height=7, wrap="word", font=("Consolas", 8))
        self.log_text.pack(fill="both", expand=True, padx=3, pady=3)

    # ------------------------------------------------------
    # 마우스 좌표 표시
    # ------------------------------------------------------
    def _update_mouse_position(self):
        """화면 절대좌표 기준으로 마우스 위치를 100ms마다 갱신합니다."""
        try:
            x, y = pyautogui.position()
            self.mouse_pos_var.set(f"X: {x}, Y: {y}")
        except Exception:
            pass
        try:
            self.root.after(100, self._update_mouse_position)
        except Exception:
            pass   # 창이 닫힌 경우

    # ------------------------------------------------------
    # 항상 위 (체크박스를 끄기 전까지 유지됩니다)
    # ------------------------------------------------------
    def apply_always_on_top(self):
        try:
            self.root.attributes("-topmost", bool(self.always_on_top_var.get()))
        except Exception:
            pass

    # ------------------------------------------------------
    # 로그
    # ------------------------------------------------------
    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    # ------------------------------------------------------
    # 영역 선택
    # ------------------------------------------------------
    def start_region_select(self):
        self.root.withdraw()
        RegionSelector(self.root, self._on_region_selected)

    def _on_region_selected(self, region):
        self.root.deiconify()
        if region is None:
            self.log("- 영역 선택 취소됨")
            return
        self.region = list(region)
        self._refresh_region_label()
        x1, y1, x2, y2 = self.region
        self.log(f"- 영역 선택됨: {x1},{y1},{x2},{y2}  (크기 {x2-x1}x{y2-y1})")

    def _refresh_region_label(self):
        x1, y1, x2, y2 = self.region
        self.region_entry.delete(0, "end")
        self.region_entry.insert(0, f"{x1},{y1},{x2},{y2}")

    # ------------------------------------------------------
    # 이미지 지정 (드래그 캡처 / 파일 불러오기 / 저장)
    # ------------------------------------------------------
    def start_image_select(self):
        self.root.withdraw()
        RegionSelector(self.root, self._on_image_region_selected)

    def _on_image_region_selected(self, region):
        self.root.deiconify()
        if region is None:
            self.log("- 이미지 캡처 취소됨")
            return
        x1, y1, x2, y2 = region
        w, h = x2 - x1, y2 - y1
        if w < 2 or h < 2:
            self.log("- 캡처 영역이 너무 작습니다. 다시 시도해 주세요")
            return
        try:
            img = pyautogui.screenshot(region=(x1, y1, w, h))
        except Exception as e:
            self.log(f"- 캡처 실패: {e}")
            return
        self.captured_image = img
        self.image_path = ""  # 새로 캡처한 이미지는 저장 전까지 경로가 없습니다.
        self.log(f"- 이미지 캡처됨 ({w}x{h}px) - 저장하려면 '이미지 저장' 버튼을 누르세요")
        self._refresh_image_preview()

    def load_image_from_file(self):
        path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[("이미지 파일", "*.png *.jpg *.jpeg *.bmp"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path)
        except Exception as e:
            self.log(f"- 이미지 불러오기 실패: {e}")
            return
        self.captured_image = img
        self.image_path = path
        self.log(f"- 이미지 불러옴: {os.path.basename(path)}")
        self._refresh_image_preview()

    def save_image_as(self):
        if self.captured_image is None:
            self.log("- 저장할 이미지가 없습니다 (먼저 이미지를 지정하세요)")
            return
        path = filedialog.asksaveasfilename(
            title="이미지 저장", defaultextension=".png",
            filetypes=[("PNG 파일", "*.png")])
        if not path:
            return
        try:
            self.captured_image.save(path)
        except Exception as e:
            self.log(f"- 이미지 저장 실패: {e}")
            return
        self.image_path = path
        self.log(f"- 이미지 저장됨: {path}")
        self._refresh_image_preview()

    def _refresh_image_preview(self):
        if self.captured_image is None:
            self.preview_label.config(image="", text="(아직 이미지 없음)")
            self.image_path_label.config(text="경로: (없음)")
            return
        thumb = self.captured_image.copy()
        thumb.thumbnail((WINDOW_WIDTH - 40, 110))
        self.preview_photo = ImageTk.PhotoImage(thumb)
        self.preview_label.config(image=self.preview_photo, text="")
        if self.image_path:
            self.image_path_label.config(text=f"경로: {self.image_path}")
        else:
            self.image_path_label.config(text="경로: (아직 저장 안 됨 - 캡처만 된 상태)")

    # ------------------------------------------------------
    # 오차범위 (tolerance)
    # ------------------------------------------------------
    def get_tolerance(self):
        try:
            v = int(float(self.tolerance_var.get()))
            if 0 <= v <= 255:
                return v
        except Exception:
            pass
        return self.cfg.get("tolerance", 15)

    def get_transwhite_tolerance(self):
        try:
            v = int(float(self.transwhite_tolerance_var.get()))
            if 0 <= v <= 255:
                return v
        except Exception:
            pass
        return self.cfg.get("transwhite_tolerance", 15)

    # ------------------------------------------------------
    # 테스트 실행
    # ------------------------------------------------------
    def run_test(self):
        x1, y1, x2, y2 = self.region
        w, h = x2 - x1, y2 - y1
        if w <= 0 or h <= 0:
            self.log("- 검색 영역이 올바르지 않습니다. 먼저 범위를 설정하세요")
            return

        if not _IMAGE_SEARCH_AVAILABLE:
            self.log(f"- 검색 불가: image_search 모듈을 못 불러왔습니다 ({_IMAGE_SEARCH_IMPORT_ERROR})")
            return

        tol = self.get_tolerance()

        # 찾을 이미지: 저장된 파일이 있으면 그걸 쓰고, 없으면 캡처해 둔 이미지를 임시 파일로 잠깐 저장해서 씁니다.
        temp_used = False
        search_path = self.image_path
        if not search_path or not os.path.exists(search_path):
            if self.captured_image is None:
                self.log("- 찾을 이미지가 없습니다. 먼저 이미지를 지정하세요")
                return
            self.captured_image.save(TEMP_CAPTURE_PATH)
            search_path = TEMP_CAPTURE_PATH
            temp_used = True

        # 템플릿이 검색 영역보다 크면 원리상 절대 못 찾습니다. 미리 알려 줍니다.
        try:
            with Image.open(search_path) as im:
                iw, ih = im.size
            if iw > w or ih > h:
                self.log(f"  ⚠ 템플릿({iw}x{ih})이 검색영역({w}x{h})보다 큽니다 -> 절대 못 찾습니다")
        except Exception:
            pass

        self.log(f"- 테스트 시작 (영역 {x1},{y1},{x2},{y2} / 오차범위 {tol})")
        try:
            matches = image_search.locate_all(search_path, (x1, y1, x2, y2), tolerance=tol)
        except Exception as e:
            matches = []
            self.log(f"  ⚠ 검색 중 오류: {e}")

        if temp_used and os.path.exists(TEMP_CAPTURE_PATH) and matches:
            pass  # 아래 transwhite 재시도에서 같은 임시파일을 또 쓸 수 있으니 여기선 안 지웁니다.

        if matches:
            if len(matches) > MAX_MATCHES:
                self.log(f"  (인식이 {len(matches)}개로 너무 많아 앞의 {MAX_MATCHES}개만 표시합니다)")
                matches = matches[:MAX_MATCHES]
            self.log(f"  ✅ [원본] {len(matches)}개 인식됨")
            for i, box in enumerate(matches, 1):
                cx, cy = box.left + box.width // 2, box.top + box.height // 2
                self.log(f"   {i}) 위치=({box.left},{box.top}) "
                         f"크기={box.width}x{box.height} 중심=({cx},{cy})")
                if self.show_boxes_var.get():
                    show_match_box(self.root, box.left, box.top, box.width, box.height, color="red")
        else:
            self.log("  ❌ [원본] 못 찾음")

            # [흰배경 투명 재시도] 원본으로 못 찾았고, 체크박스가 켜져 있으면 시도합니다.
            # 배경을 하얗게 만들어 캡처한 이미지(예: 아이콘만 있고 배경은 흰색)는 게임 화면의
            # 실제 배경색과 달라서 원본 검색으로는 거의 못 찾습니다 - 이럴 때 씁니다.
            if self.use_transwhite_var.get():
                tw_tol = self.get_transwhite_tolerance()
                self.log(f"- [transwhite] 흰배경 투명 방식으로 재시도 (오차범위 {tw_tol})")
                try:
                    tw_matches = image_search.locate_all(search_path, (x1, y1, x2, y2),
                                                           tolerance=tw_tol, transwhite=True)
                except Exception as e:
                    tw_matches = []
                    self.log(f"  ⚠ transwhite 검색 중 오류: {e}")

                if tw_matches:
                    if len(tw_matches) > MAX_MATCHES:
                        self.log(f"  (인식이 {len(tw_matches)}개로 너무 많아 앞의 {MAX_MATCHES}개만 표시합니다)")
                        tw_matches = tw_matches[:MAX_MATCHES]
                    self.log(f"  ✅ [transwhite] {len(tw_matches)}개 인식됨")
                    for i, box in enumerate(tw_matches, 1):
                        cx, cy = box.left + box.width // 2, box.top + box.height // 2
                        self.log(f"   {i}) 위치=({box.left},{box.top}) "
                                 f"크기={box.width}x{box.height} 중심=({cx},{cy})")
                        if self.show_boxes_var.get():
                            show_match_box(self.root, box.left, box.top, box.width, box.height,
                                           color="#3498db")
                else:
                    self.log("  ❌ [transwhite] 못 찾음")

        if temp_used and os.path.exists(TEMP_CAPTURE_PATH):
            try: os.remove(TEMP_CAPTURE_PATH)
            except Exception: pass

    # ------------------------------------------------------
    # 설정 저장
    # ------------------------------------------------------
    def save_settings(self):
        cfg = {
            "region": self.region,
            "image_path": self.image_path,
            "tolerance": self.get_tolerance(),
            "show_boxes": bool(self.show_boxes_var.get()),
            "always_on_top": bool(self.always_on_top_var.get()),
            "use_transwhite": bool(self.use_transwhite_var.get()),
            "transwhite_tolerance": self.get_transwhite_tolerance(),
        }
        self.cfg = cfg
        if save_config(cfg):
            self.log("- 설정을 저장했습니다 (tester_config.json)")
        else:
            self.log("- 설정 저장 실패 (tester_config.json에 쓸 수 없습니다)")


# 이미 열려 있는 테스터 창을 기억해 두고, 두 번 열리지 않게 합니다.
_open_window = None


def open_tester_window(parent=None):
    """테스터 창을 엽니다.

    parent를 주면 그 창에 딸린 Toplevel로 열립니다 (main.py의 '이미지 테스터' 버튼용).
    parent가 없으면 이 파일을 단독 실행한 경우이므로 독립 창으로 엽니다."""
    global _open_window
    if parent is not None:
        # 이미 열려 있으면 새로 만들지 않고 앞으로 가져옵니다.
        if _open_window is not None:
            try:
                if _open_window.winfo_exists():
                    _open_window.lift()
                    _open_window.focus_force()
                    return _open_window
            except Exception:
                pass
        win = tk.Toplevel(parent)
        _open_window = win
    else:
        win = tk.Tk()
    TesterApp(win)
    return win


if __name__ == "__main__":
    window = open_tester_window()
    window.mainloop()