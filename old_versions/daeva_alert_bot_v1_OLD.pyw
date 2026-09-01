import tkinter as tk
from tkinter import scrolledtext, messagebox
from PIL import Image, ImageTk
import threading
import pyautogui
import time
import requests
import psutil
import os
import pygetwindow as gw
from datetime import datetime

# ==========================================================
# 1. [설정 및 환경 변수]
# ==========================
BOT_TOKEN = ''  # [정리] 실제 토큰이 하드코딩되어 있어 삭제했습니다. 아래 안내 참고.
CHAT_ID = ''
PC_NAME = 'PC-32'
CONFIDENCE_LEVEL = 0.9
CHECK_INTERVAL_MSG = 10      
CHECK_INTERVAL_FIX = 10800   

BG_IMAGE_PATH = "dragonball_bg.png"
NORMAL_GAMES = ["VAMPIR", "RF ONLINE NEXT"]
AION_GAME = "AION2"

AION_W, AION_H = 650, 400  
WIN_W, WIN_H = 409, 269     
COLUMNS = 3
START_X, START_Y = 0, 0

TARGETS = [
    {"file": "death.png", "msg": "아이온- 사망"},
    {"file": "gold.png", "msg": "아이온- 골드가득"},
    {"file": "death2.png", "msg": "아이온- 사망"},
]

class DragonballIntegratedBot:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MONITOR - {PC_NAME}")
        self.root.geometry("300x450") 
        self.root.resizable(False, False)
        self.root.configure(bg="#000000")
        
        self.lock = threading.Lock() 
        self.notified_states = {target["file"]: False for target in TARGETS}
        self.last_sent_time = {} 

        # 종료 예약 관련 변수
        self.reservation_active = False

        self.setup_gui()
        
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        threading.Thread(target=self.auto_fix_loop, daemon=True).start()

    def setup_gui(self):
        self.img_h = 180
        self.canvas = tk.Canvas(self.root, width=300, height=self.img_h, highlightthickness=0, bg="#000000")
        self.canvas.pack(side=tk.TOP, fill=tk.X)
        
        try:
            if os.path.exists(BG_IMAGE_PATH):
                img = Image.open(BG_IMAGE_PATH)
                resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
                self.bg_img = img.resize((300, self.img_h), resample_filter)
                self.bg_photo = ImageTk.PhotoImage(self.bg_img)
                self.canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)
            else:
                self.canvas.create_text(150, 90, text="DRAGONBALL BOT", fill="white")
        except:
            self.canvas.create_text(150, 90, text="GUI LOAD ERROR", fill="red")

        # FIX 버튼 (기존)
        self.change_btn = tk.Button(self.root, text="FIX", command=self.execute_fix_all, 
                                   bg="#333333", fg="#FFFFFF", font=("Arial", 7, "bold"), 
                                   width=4, bd=1, relief=tk.RAISED, cursor="hand2")
        self.canvas.create_window(295, 175, window=self.change_btn, anchor=tk.SE)

        # [추가] EXIT 버튼 (종료 예약 팝업 호출)
        self.exit_popup_btn = tk.Button(self.root, text="EXIT", command=self.open_exit_setup, 
                                   bg="#AA0000", fg="#FFFFFF", font=("Arial", 7, "bold"), 
                                   width=4, bd=1, relief=tk.RAISED, cursor="hand2")
        self.canvas.create_window(255, 175, window=self.exit_popup_btn, anchor=tk.SE)

        log_frame = tk.Frame(self.root, bg="#000000")
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, bg="#000000", fg="#00FF41", 
                                                 font=("Consolas", 9), bd=0, highlightthickness=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log("🚀 시스템 가동 준비 완료")

    # ---------------------------------------------------------
    # [새로운 기능: 게임 종료 예약 팝업]
    # ---------------------------------------------------------
    def open_exit_setup(self):
        """별도의 종료 설정 창(Toplevel)을 띄웁니다."""
        self.popup = tk.Toplevel(self.root)
        self.popup.title("종료 예약")
        self.popup.geometry("250x200")
        self.popup.attributes("-topmost", True)
        self.popup.configure(bg="#1a1a1a")

        tk.Label(self.popup, text="[ 게임 자동 종료 설정 ]", fg="white", bg="#1a1a1a", font=("Arial", 9, "bold")).pack(pady=10)
        
        # 입력 필드
        f1 = tk.Frame(self.popup, bg="#1a1a1a")
        f1.pack()
        tk.Label(f1, text="대상:", fg="white", bg="#1a1a1a").grid(row=0, column=0)
        self.game_entry = tk.Entry(f1, width=15)
        self.game_entry.grid(row=0, column=1, padx=5, pady=2)
        self.game_entry.insert(0, "AION2.exe")

        tk.Label(f1, text="시간:", fg="white", bg="#1a1a1a").grid(row=1, column=0)
        self.time_entry = tk.Entry(f1, width=15)
        self.time_entry.grid(row=1, column=1, padx=5, pady=2)
        self.time_entry.insert(0, "04:45")

        self.pop_status = tk.Label(self.popup, text="대기 중", fg="gray", bg="#1a1a1a", font=("Arial", 8))
        self.pop_status.pack(pady=5)

        # 버튼
        btn_f = tk.Frame(self.popup, bg="#1a1a1a")
        btn_f.pack(pady=5)
        tk.Button(btn_f, text="예약", width=8, command=self.start_exit_reservation).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="즉시종료", width=8, bg="#ff9999", command=self.instant_kill).pack(side=tk.LEFT, padx=5)

    def start_exit_reservation(self):
        target_time = self.time_entry.get().strip()
        self.reservation_active = True
        self.pop_status.config(text=f"{target_time} 예약됨", fg="#00FF41")
        self.log(f"⏰ 종료 예약 설정: {self.game_entry.get()} @ {target_time}")
        threading.Thread(target=self.exit_monitor_loop, args=(target_time,), daemon=True).start()

    def exit_monitor_loop(self, target_time):
        while self.reservation_active:
            now = datetime.now().strftime("%H:%M")
            if now == target_time:
                success = self.kill_process()
                if success:
                    self.log(f"✅ 예약 종료 성공: {target_time}")
                    self.send_telegram(f"예약 종료 완료: {self.game_entry.get()}")
                self.reservation_active = False
                break
            time.sleep(10)

    def instant_kill(self):
        if self.kill_process():
            self.log(f"⚡ 즉시 종료 실행 완료")
            messagebox.showinfo("성공", "프로세스를 종료했습니다.")
        else:
            messagebox.showwarning("실패", "프로세스를 찾지 못했습니다.")

    def kill_process(self):
        target = self.game_entry.get().strip().lower()
        found = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == target:
                    proc.kill()
                    found = True
            except: continue
        return found

    # ---------------------------------------------------------
    # [기존 드래곤볼 봇 기능]
    # ---------------------------------------------------------
    def log(self, message):
        now = datetime.now().strftime("[%H:%M]")
        full_msg = f"{now} {message}\n"
        self.root.after(0, self._append_log, full_msg)

    def _append_log(self, full_msg):
        self.log_area.insert(tk.END, full_msg)
        self.log_area.see(tk.END)

    def send_telegram_once(self, event_key, message):
        now = time.time()
        if event_key in self.last_sent_time:
            if now - self.last_sent_time[event_key] < 5:
                return
        self.last_sent_time[event_key] = now
        threading.Thread(target=self.send_telegram, args=(message,), daemon=True).start()

    def send_telegram(self, message):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.get(url, params={"chat_id": CHAT_ID, "text": f"[{PC_NAME}] {message}"}, timeout=5)
        except:
            pass

    def execute_fix_all(self, is_silent=False):
        try:
            aion_wins = gw.getWindowsWithTitle(AION_GAME)
            for win in aion_wins:
                try:
                    if win.isMinimized: win.restore()
                    win.resizeTo(AION_W, AION_H)
                    win.moveTo(START_X, START_Y)
                except: pass

            normal_count = 0
            for title in NORMAL_GAMES:
                wins = gw.getWindowsWithTitle(title)
                for win in wins:
                    try:
                        if win.isMinimized: win.restore()
                        row, col = normal_count // COLUMNS, normal_count % COLUMNS
                        win.resizeTo(WIN_W, WIN_H)
                        win.moveTo(START_X + (col * WIN_W), START_Y + (row * WIN_H))
                        normal_count += 1
                    except: pass
            
            if not is_silent: self.log(f"✅ 정렬 완료 (AION + {normal_count})")
        except: self.log("⚠️ 정렬 오류")

    def auto_fix_loop(self):
        while True:
            time.sleep(CHECK_INTERVAL_FIX)
            self.execute_fix_all(is_silent=True)

    def monitor_loop(self):
        self.log("🔍 이미지 모니터링 시작")
        while True:
            try:
                for target in TARGETS:
                    img_file = target["file"]
                    if not os.path.exists(img_file): continue
                    try:
                        loc = pyautogui.locateOnScreen(img_file, confidence=CONFIDENCE_LEVEL)
                        if loc:
                            if not self.notified_states.get(img_file, False):
                                self.notified_states[img_file] = True 
                                self.log(f"🔔 감지: {target['msg']}")
                                self.send_telegram_once(img_file, target['msg'])
                        else:
                            if self.notified_states.get(img_file, False):
                                self.notified_states[img_file] = False
                                self.log(f"🟢 해제: {target['msg']} 종료")
                    except Exception: 
                        if self.notified_states.get(img_file, False):
                            self.notified_states[img_file] = False
                
            except Exception as e:
                self.log(f"🚨 시스템 오류: {str(e)[:25]}")
            time.sleep(CHECK_INTERVAL_MSG)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    root = tk.Tk()
    app = DragonballIntegratedBot(root)
    root.mainloop()
