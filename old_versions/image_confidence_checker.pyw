import sys
import subprocess
import os
import time
import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image
import pyautogui
import requests
from datetime import datetime
import numpy as np

# --- [라이브러리 체크 및 설치] ---
def install_libs():
    libs = ['opencv-python', 'pyautogui', 'pillow', 'requests', 'numpy']
    for lib in libs:
        try:
            if lib == 'opencv-python': import cv2
            else: __import__(lib.replace('-', '_'))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_libs()
import cv2

# --- [설정] ---
PC_NAME = 'PC-25'
CONFIDENCE_LEVEL = 0.7  # 70% 이상이면 감지
CHECK_INTERVAL = 3      # 체크 주기 (초)

TARGETS = [
    {"file": "death.png", "msg": "아이온- 사망"},
    {"file": "gold.png", "msg": "아이온- 골드가득"},
    {"file": "death2.png", "msg": "아이온- 사망"},
    {"file": "map_pin.png", "msg": "아이온- 맵핀"},
    {"file": "success.png", "msg": "추출성공"},
    {"file": "daeva.png", "msg": "아이온- 인증"},
    {"file": "pickup.png", "msg": "아이온- 줍기"},
]

class DragonballBotV3:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MONITOR - {PC_NAME}")
        self.root.geometry("350x520") # 로그 가독성을 위해 가로폭 살짝 키움
        self.root.configure(bg="#000000")
        self.notified_states = {t["file"]: False for t in TARGETS}
        
        # GUI 구성
        self.log_area = scrolledtext.ScrolledText(self.root, bg="#000000", fg="#00FF41", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log("🚀 모니터링 가동 (일치율 상세 표시 모드)")
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def log(self, message):
        now = datetime.now().strftime("[%H:%M:%S]")
        self.root.after(0, lambda: self.log_area.insert(tk.END, f"{now} {message}\n"))
        self.root.after(0, lambda: self.log_area.see(tk.END))

    def monitor_loop(self):
        while True:
            try:
                # 1. 화면 캡처 및 변환
                screen_pil = pyautogui.screenshot().convert('RGB')
                screen_cv = cv2.cvtColor(np.array(screen_pil), cv2.COLOR_RGB2BGR)
                
                for target in TARGETS:
                    img_path = target["file"]
                    if not os.path.exists(img_path): continue
                    
                    try:
                        # 2. 대상 이미지 로드
                        template_pil = Image.open(img_path).convert('RGB')
                        template_cv = cv2.cvtColor(np.array(template_pil), cv2.COLOR_RGB2BGR)
                        
                        # 3. 매칭 수행
                        res = cv2.matchTemplate(screen_cv, template_cv, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        
                        match_rate = int(max_val * 100)
                        
                        # [핵심] 감지 성공 시
                        if max_val >= CONFIDENCE_LEVEL:
                            if not self.notified_states[img_path]:
                                self.notified_states[img_path] = True
                                self.log(f"🎯 [감지] {target['msg']} (일치율: {match_rate}%)")
                        
                        # [핵심] 감지 상태였다가 해제될 시
                        else:
                            if self.notified_states[img_path]:
                                self.notified_states[img_path] = False
                                self.log(f"🟢 [해제] {target['msg']} (현재: {match_rate}%)")
                                
                    except Exception as e:
                        self.log(f"❌ {img_path} 분석실패: {str(e)[:20]}")
                        
            except Exception as e:
                self.log(f"🚨 화면캡처 오류: {str(e)[:20]}")
            
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 경로 설정 (실행 파일 위치 기준)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    root = tk.Tk()
    app = DragonballBotV3(root)
    root.mainloop()
