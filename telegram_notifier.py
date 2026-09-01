"""
[텔레그램 알림] 알림 전송을 담당하는 모듈입니다.

핵심 설계:
- 전송은 반드시 별도 스레드(워커)에서 처리합니다. 인터넷이 끊기거나 텔레그램 서버가 느려도
  매크로/스케줄 동작이 절대 멈추지 않아야 하기 때문입니다. notify()는 큐에 넣고 즉시 반환합니다.
- 이벤트별로 '몇 번 보낼지'를 설정할 수 있고, 각 전송 사이 간격(기본 2.5초)을 둡니다.
- 한 번 감지한 상황은 지정 횟수만 보내고 더 보내지 않습니다. 같은 상황이 화면에 계속
  떠 있어도 재발송하지 않습니다. 상황이 해소되면(clear 호출) 다시 보낼 수 있게 풀립니다.

TelegramNotifierMixin은 IntegratedController가 상속해서 self.notify_event(...) 형태로 씁니다.
"""
import queue
import threading
import time

try:
    import requests
except Exception:      # requests가 없어도 프로그램 자체는 돌아가야 합니다.
    requests = None

# 알림 항목 정의: 키 -> (화면에 보일 이름, 기본 사용 여부, 기본 전송 횟수)
# 여기에 항목을 추가하면 GUI 체크박스/입력칸도 자동으로 같이 늘어납니다.
NOTIFY_EVENTS = [
    ("death",         "사망 감지",              True, 2),
    ("daeva",         "데바인증 감지",           True, 2),
    ("gold_full",     "골드 가득(캐릭터 완료)",   True, 1),
    ("char_switch",   "캐릭터 전환",             True, 1),
    ("all_done",      "모든 캐릭터 완료",         True, 1),
    ("error_stop",    "오류로 프로그램 정지",      True, 1),
    ("epqk_detect",   "특정 화면 감지 (epqk)",    True, 1),
]

DEFAULT_SEND_INTERVAL = 2.5   # 같은 알림을 여러 번 보낼 때의 간격(초)


class TelegramNotifierMixin:
    def init_telegram(self):
        """텔레그램 전송용 큐와 워커 스레드를 준비합니다. __init__에서 한 번 부릅니다."""
        self._tg_queue = queue.Queue()
        self._tg_sent_events = set()   # 이미 보낸(그리고 아직 해소되지 않은) 이벤트 키
        self._tg_worker = threading.Thread(target=self._telegram_worker, daemon=True)
        self._tg_worker.start()

    # ------------------------------------------------------
    # 설정 읽기
    # ------------------------------------------------------
    def _tg_get(self, key, default=""):
        """GUI 입력칸 값을 안전하게 읽습니다. 위젯이 아직 없으면 저장된 설정을 씁니다."""
        var = getattr(self, f"tg_{key}_var", None)
        if var is not None:
            try:
                return var.get()
            except Exception:
                pass
        return self.cfg.get(f"telegram_{key}", default)

    def telegram_ready(self):
        """봇 토큰과 채팅 ID가 모두 채워져 있어야 보낼 수 있습니다."""
        return bool(str(self._tg_get("bot_token")).strip() and str(self._tg_get("chat_id")).strip())

    def _tg_event_enabled(self, event_key):
        var = getattr(self, "tg_event_enabled_vars", {}).get(event_key)
        if var is not None:
            try:
                return bool(var.get())
            except Exception:
                pass
        return bool(self.cfg.get(f"telegram_event_{event_key}_enabled", True))

    def _tg_event_count(self, event_key, default=1):
        var = getattr(self, "tg_event_count_vars", {}).get(event_key)
        raw = None
        if var is not None:
            try:
                raw = var.get()
            except Exception:
                raw = None
        if raw is None:
            raw = self.cfg.get(f"telegram_event_{event_key}_count", default)
        try:
            n = int(float(raw))
            return max(1, min(20, n))   # 실수로 큰 값을 넣어도 20번까지만 보냅니다.
        except Exception:
            return default

    def _tg_send_interval(self):
        raw = None
        var = getattr(self, "tg_interval_var", None)
        if var is not None:
            try:
                raw = var.get()
            except Exception:
                raw = None
        if raw is None:
            raw = self.cfg.get("telegram_send_interval", DEFAULT_SEND_INTERVAL)
        try:
            v = float(raw)
            return v if v > 0 else DEFAULT_SEND_INTERVAL
        except Exception:
            return DEFAULT_SEND_INTERVAL

    # ------------------------------------------------------
    # 알림 요청 (매크로/스케줄 쪽에서 부르는 진입점)
    # ------------------------------------------------------
    def notify_event(self, event_key, message, once=True):
        """알림을 큐에 넣고 곧바로 돌아옵니다. 실제 전송은 워커 스레드가 합니다.

        once=True (기본): 같은 이벤트는 상황이 해소(clear_event)되기 전까지 한 번만 보냅니다.
                          사망 화면이 계속 떠 있어도 알림이 도배되지 않게 하기 위함입니다.
        once=False: 부를 때마다 보냅니다. (캐릭터 전환처럼 매번 새로 발생하는 일회성 사건)"""
        if not self._tg_event_enabled(event_key):
            return
        if once:
            if event_key in self._tg_sent_events:
                return
            self._tg_sent_events.add(event_key)

        if not self.telegram_ready():
            self.log(f"- [텔레그램] 토큰/채팅ID가 비어 있어 보내지 못했습니다 ({event_key})")
            return

        count = self._tg_event_count(event_key)
        self._tg_queue.put((event_key, message, count))

    def clear_event(self, event_key):
        """상황이 해소되었음을 알립니다. 다음에 같은 일이 생기면 다시 알림을 보냅니다."""
        self._tg_sent_events.discard(event_key)

    def notify_test(self):
        """테스트 버튼용. 설정이 제대로 됐는지 즉시 확인합니다. (횟수 1회, 중복 방지 없음)"""
        if not self.telegram_ready():
            self.log("- [텔레그램] 봇 토큰과 채팅 ID를 먼저 입력해 주세요")
            return
        self._tg_queue.put(("__test__", "테스트 메시지입니다. 연결이 정상입니다.", 1))
        self.log("- [텔레그램] 테스트 메시지를 전송 대기열에 넣었습니다")

    # ------------------------------------------------------
    # 전송 워커
    # ------------------------------------------------------
    def _telegram_worker(self):
        """큐에서 꺼내 실제로 전송합니다. 이 스레드가 느려져도 본 동작에는 영향이 없습니다."""
        while True:
            try:
                event_key, message, count = self._tg_queue.get()
            except Exception:
                time.sleep(1.0)
                continue

            interval = self._tg_send_interval()
            for i in range(count):
                ok = self._telegram_send(message)
                if i == 0:
                    if ok:
                        self.log(f"- [텔레그램] 전송: {message} ({count}회 예정)")
                    else:
                        self.log(f"- [텔레그램] 전송 실패: {message}")
                        break   # 첫 시도부터 실패하면 나머지도 실패할 가능성이 높습니다.
                if i < count - 1:
                    time.sleep(interval)

    def _telegram_send(self, message):
        """텔레그램 봇 API로 메시지 한 건을 보냅니다. 성공하면 True."""
        if requests is None:
            self.log("- [텔레그램] requests 모듈이 없습니다 (pip install requests)")
            return False
        token = str(self._tg_get("bot_token")).strip()
        chat_id = str(self._tg_get("chat_id")).strip()
        pc_name = str(self._tg_get("pc_name", "1")).strip() or "1"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = requests.get(url, params={"chat_id": chat_id,
                                             "text": f"[{pc_name}번PC] {message}"}, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False