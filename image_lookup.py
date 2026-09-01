"""
이미지 파일 경로 찾기 + 핵심 감지 이미지 상수.

main.pyw(상시 감시), schedule_routine.py(스케줄), hunt_return_routine.py(사냥터 복귀)가
공통으로 이 모듈을 씁니다. 순환 임포트를 피하려고 따로 뺐습니다.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# [이미지 검색 폴더] 이미지 파일을 아래 순서대로 찾습니다.
# 기본적으로 images/ 폴더에서 찾고, 없으면 프로그램 폴더 바로 밑도 확인합니다.
IMAGE_DIRS = [
    os.path.join(BASE_DIR, "images"),
    BASE_DIR,  # 혹시 images/ 밖에 이미지를 두는 경우를 위한 대비용
]

# [핵심 감지 이미지] 상시 감시(main.pyw의 check_stop_images)와 사냥터 복귀가 씁니다.
MAP_PIN_IMG = 'map_pin.png'
DEAD_IMG_1, DEAD_IMG_2, CHECK_IMG, GOLD_FULL_IMG = 'death.png', 'death2.png', 'daeva.png', 'gold.png'
# [주의] 골드 가득 판정은 이제 여기가 아니라 schedule_routine.py의 GOLD_FULL_TARGETS에서
# 정합니다 (100aks.png / gold.png / gold1.png 중 하나라도 보이면 가득으로 판정).
# 아래 두 값은 옛 이름이라 남겨두었을 뿐, 실제 판정에는 쓰이지 않습니다.
GOLD_FULL_CONFIDENCE = 0.85
CONFIDENCE_LEVEL = 0.9

_image_path_cache = {}


def resolve_image(name):
    """이미지 이름으로 실제 파일 경로를 찾아 돌려줍니다. 못 찾으면 None.
    IMAGE_DIRS를 순서대로 뒤지고, 하위 폴더까지 훑습니다."""
    if not name:
        return None
    if name in _image_path_cache:
        cached = _image_path_cache[name]
        # 파일이 지워졌을 수도 있으니 캐시를 쓰기 전에 한 번 확인합니다.
        if cached and os.path.exists(cached):
            return cached
        _image_path_cache.pop(name, None)

    if os.path.isabs(name):
        return name if os.path.exists(name) else None

    for folder in IMAGE_DIRS:
        direct = os.path.join(folder, name)
        if os.path.exists(direct):
            _image_path_cache[name] = direct
            return direct

    # 캡처 툴이 하위 폴더로 정리해 두는 경우가 있어 한 번 더 훑습니다.
    for folder in IMAGE_DIRS[1:]:
        if not os.path.isdir(folder):
            continue
        for root_dir, _dirs, files in os.walk(folder):
            if name in files:
                found = os.path.join(root_dir, name)
                _image_path_cache[name] = found
                return found
    return None

# ==========================================================
# [거래소 이미지별 임계값] GUI 거래소 탭에서 각각 따로 입력할 수 있습니다.
# (설정키, 이미지파일, 기본 임계값, 화면에 보일 이름)
# 여기에 줄을 추가하면 설정 키와 GUI 입력칸이 자동으로 같이 늘어납니다.
# [주의] config_store.py가 이 값을 읽습니다. pyautogui 등 무거운 모듈에 기대지 않도록
#        정의는 반드시 이 파일(의존성 없는 모듈)에 둡니다.
# ==========================================================
MARKET_IMAGE_THRESHOLDS = [
    ("enter",  'wjdtks.png',     0.85, "거래소 진입 확인"),
    ("equip",  'wkdql.png',      0.98, "거래가능 장비"),
    ("sell",   'vksaocnlth.png', 0.85, "판매창(판매취소)"),
    ("fee",    'aks.png',        0.85, "수수료 '만'"),
    ("oneday", '1dlf.png',       0.85, "1일 이상 미판매"),
    ("full",   '1010.png',       0.85, "등록 가득(10/10)"),
]

# ==========================================================
# [로그 상세도] 화면 로그창에 어디까지 보여줄지 정하는 등급입니다.
# 숫자가 클수록 더 자세한 내용입니다. 파일(error_log.txt)에는 등급과 무관하게 항상 다 남습니다.
# [주의] config_store.py가 이 값을 읽으므로, 무거운 모듈에 기대지 않도록 여기에 둡니다.
# ==========================================================
LOG_SIMPLE = 0   # 간단 - 시작/완료/캐릭터 전환/오류처럼 '결과'만
LOG_NORMAL = 1   # 보통 - 각 단계 진행 상황 (기본값)
LOG_DETAIL = 2   # 상세 - 클릭 좌표, 유사도 점수, 이미지 검색 결과까지 (문제 생겼을 때만)

LOG_LEVEL_LABELS = [
    (LOG_SIMPLE, "간단", "결과만 (오래 돌릴 때)"),
    (LOG_NORMAL, "보통", "각 단계 진행 상황"),
    (LOG_DETAIL, "상세", "클릭 좌표·유사도까지 (문제 추적용)"),
]
# ==========================================================
# [화면 감지 알림] 스킬매크로(F9) 또는 스케줄(Del)이 켜져 있는 동안, 이 영역에서
# 이 이미지가 보이는지 주기적으로 확인합니다. 보이면 텔레그램으로 알립니다.
# ==========================================================
EPQK_WATCH_REGION = (408, 130, 853, 458)   # (x1, y1, x2, y2) - 화면 절대좌표
EPQK_WATCH_IMG = 'epqk.png'
EPQK_WATCH_INTERVAL = 5.0                  # 확인 간격(초)