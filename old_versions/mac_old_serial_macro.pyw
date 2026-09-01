import serial
import time
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import pyautogui

# 설정
PORT = 'COM3'
BAUD_RATE = 9600

class MacroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Macro Controller")
        
        # 창의 최소 크기를 설정 (이보다 작아지면 구성이 깨지므로 제한)
        self.root.minsize(300, 250)
        self.root.geometry("300x300")
        
        self.active = False
        self.ser = None
        self.monitor_thread = None
        self.last_date = None  

        # --- GUI 구성 (유동적 레이아웃 설정) ---
        # 상단 상태 라벨
        self.status_label = tk.Label(root, text="상태: 연결 대기 중", fg="blue", font=("Arial", 11, "bold"))
        self.status_label.pack(pady=5, fill=tk.X)

        # 중간 로그 영역 (창 크기에 따라 늘어남)
        # expand=True, fill=tk.BOTH 설정을 통해 사이즈 조절 시 같이 커짐
        self.log_frame = tk.Frame(root)
        self.log_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self.log_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(self.log_frame, height=8, width=40, yscrollcommand=self.scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.log_text.yview)

        # 하단 버튼 영역 (가로로 꽉 차게 설정)
        self.btn_start = tk.Button(root, text="시작 (START)", command=self.start_macro, 
                                   bg="lightgreen", height=2)
        self.btn_start.pack(pady=2, padx=10, fill=tk.X)

        self.btn_stop = tk.Button(root, text="중지 (STOP)", command=self.stop_macro, 
                                  bg="lightcoral", height=2)
        self.btn_stop.pack(pady=5, padx=10, fill=tk.X)

        # 시리얼 연결 시도
        self.connect_serial()

    def log(self, message):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("[%H:%M]")
        
        if self.last_date != current_date:
            date_line = f"\n--- [{current_date}] ---\n"
            self.log_text.insert(tk.END, date_line)
            self.save_to_file(date_line)
            self.last_date = current_date

        full_msg = f"{timestamp} {message}\n"
        self.log_text.insert(tk.END, full_msg)
        self.log_text.see(tk.END)
        self.save_to_file(full_msg)

    def save_to_file(self, content):
        try:
            with open("macro_history.txt", "a", encoding="utf-8") as f:
                f.write(content)
        except:
            pass

    def connect_serial(self):
        try:
            if self.ser:
                self.ser.close()
            self.ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
            time.sleep(2) 
            self.log(f"포트 {PORT} 연결 성공!")
            self.status_label.config(text=f"상태: {PORT} 연결됨", fg="green")
        except Exception as e:
            self.log(f"연결 실패: {e}")
            self.status_label.config(text="상태: 연결 실패", fg="red")

    def check_death_loop(self):
        while self.active:
            try:
                death_location = pyautogui.locateOnScreen('death.png', confidence=0.8)
                if death_location:
                    self.log("!!! 죽음 감지됨 !!!")
                    self.root.after(0, self.stop_macro)
                    break 
            except Exception:
                pass
            time.sleep(1.5)

    def start_macro(self):
        if self.active:
            self.log("이미 매크로 실행 중")
            return
        if not self.ser or not self.ser.is_open:
            self.connect_serial()
            if not self.ser or not self.ser.is_open: return

        self.active = True
        try:
            self.ser.write(b'A')
            self.log(">> 매크로 시작")
            self.status_label.config(text="상태: 실행 중 (감시중)", fg="red")
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self.check_death_loop, daemon=True)
                self.monitor_thread.start()
        except Exception as e:
            self.log(f"에러: {e}")
            self.active = False

    def stop_macro(self):
        if not self.active: return
        self.active = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.write(b'S')
            self.log(">> 매크로 중지")
            self.status_label.config(text=f"상태: {PORT} 연결됨", fg="green")
        except Exception as e:
            self.log(f"중지 에러: {e}")

    def on_closing(self):
        self.active = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'S')
                self.ser.close()
            except: pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
