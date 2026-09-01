"""
[이미지 서치 - AHK ImageSearch 방식(픽셀 직접비교)]

오토핫키의 ImageSearch / *TransWhite와 최대한 비슷하게, "패턴(명암 모양)이 비슷한가"가
아니라 "픽셀 색상이 실제로 비슷한가"를 직접 비교합니다.

[왜 다시 짰나]
예전 버전은 pyautogui.locateOnScreen(confidence=...)을 썼는데, 이건 내부적으로
cv2.matchTemplate을 정규화된 상관관계(TM_CCOEFF_NORMED 등) 방식으로 계산합니다.
이 방식은 "색이 실제로 같은가"가 아니라 "밝고 어두운 패턴의 배치가 비슷한가"를 보기
때문에, 그림판으로 봤을 때 색이 확연히 다른 두 이미지도 점수가 높게 나와 같다고
오판하는 경우가 있었습니다. AHK의 ImageSearch는 픽셀 값을 직접 비교하기 때문에 이런
문제가 훨씬 적습니다. 이 모듈은 그 방식을 재현합니다.

[알고리즘]
1) cv2.matchTemplate(TM_SQDIFF)로 "픽셀 값 차이의 제곱합"이 작은 후보 위치들을
   빠르게 추려냅니다. TM_SQDIFF는 정규화하지 않은 순수 차이값이라, 색이 다르면 그대로
   값이 커집니다 (패턴만 비슷해도 점수가 잘 나오는 정규화 상관관계와 다른 지점).
   - "모든 비교대상 픽셀이 tolerance 안에 들어오는" 진짜 매치는 절대 넘을 수 없는
     차이 제곱합의 상한선이 수학적으로 정해지므로(채널당 최대 tolerance^2), 그
     상한선 이하인 후보는 절대 놓치지 않습니다.
2) 그 후보들만 실제로 픽셀 하나하나를 RGB 채널별로 비교해서, 전부 tolerance
   (오차범위) 안에 들어오는지 엄격하게 검증합니다. 검증을 통과한 것만 '찾음'으로
   인정합니다.

[tolerance] AHK의 shade variation(*n)과 같은 의미입니다 (0~255).
  0    = 완전히 같은 색만 인정 (오탐은 거의 없지만, 화면 압축/안티에일리어싱 때문에
         멀쩡한 이미지도 못 찾을 수 있음)
  숫자가 커질수록 색 차이를 더 너그럽게 봐줍니다 (오탐 가능성도 같이 커짐)
  보통 10~30 사이에서 시작해서 조정하는 걸 추천합니다.

[transwhite] 흰색(또는 거의 흰색) 픽셀을 비교 대상에서 제외합니다. 흰 배경으로
캡처해둔 이미지(예: 아이콘만 있고 배경은 흰색)에 씁니다 - AHK의 *TransWhite와 동일한
개념입니다.

[사용법]
    import image_search

    box = image_search.locate_smart('a.png', region=(x1,y1,x2,y2), tolerance=15)
    box = image_search.locate_transwhite('b.png', region=(x1,y1,x2,y2), tolerance=15)
    boxes = image_search.locate_all('c.png', region=(x1,y1,x2,y2), tolerance=15)  # 여러 개
"""
import cv2
import numpy as np
import pyautogui

from image_lookup import resolve_image

# [흰색 판정 기준] transwhite에서 그레이스케일 값이 이 값 이상이면 흰색으로 보고
# 비교 대상에서 뺍니다 (0~255).
WHITE_THRESHOLD = 240

# [기본 오차범위] AHK의 shade variation과 같은 의미 (0~255, RGB 채널별 허용 오차).
DEFAULT_TOLERANCE = 15


class MatchBox:
    """pyautogui의 Box와 같은 모양(left, top, width, height)으로 맞춰 둔 결과 객체."""
    __slots__ = ("left", "top", "width", "height")

    def __init__(self, left, top, width, height):
        self.left, self.top, self.width, self.height = left, top, width, height

    def __iter__(self):
        return iter((self.left, self.top, self.width, self.height))

    def __repr__(self):
        return f"MatchBox(left={self.left}, top={self.top}, width={self.width}, height={self.height})"


# ==========================================================
# 내부 구현
# ==========================================================
def _white_mask(template_bgr):
    """흰색(거의 흰색 포함) 픽셀 위치를 False(무시)로, 나머지를 True(비교 대상)로 돌려줍니다."""
    gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    return gray < WHITE_THRESHOLD


def _load_template(image_name_or_path):
    """이미지명/경로 -> (실제경로, BGR 배열). 못 찾으면 (None, None)."""
    path = resolve_image(image_name_or_path)
    if not path:
        return None, None
    template_bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    return path, template_bgr


def _grab_region(region):
    """region=(x1,y1,x2,y2) 화면 절대좌표를 캡처해서 BGR 배열로 돌려줍니다."""
    x1, y1, x2, y2 = region
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return None
    try:
        screenshot = pyautogui.screenshot(region=(x1, y1, w, h))
    except Exception:
        return None
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def _find_matches(template_bgr, mask, haystack_bgr, tolerance, max_matches=None):
    """실제 매칭 엔진.

    mask: (th, tw) bool 배열 - True인 픽셀만 비교합니다. None이면 전부 비교합니다.
    max_matches: None이면 전부, 1이면 가장 그럴듯한 것 하나만 찾고 멈춥니다.
    반환: [(x, y), ...] - haystack 안에서의 왼쪽위 좌표 목록 (오차가 작은 순서).
    """
    th, tw = template_bgr.shape[:2]
    H, W = haystack_bgr.shape[:2]
    if th > H or tw > W or th == 0 or tw == 0:
        return []

    if mask is None:
        mask = np.ones((th, tw), dtype=bool)
    if not mask.any():
        return []  # 비교할 픽셀이 하나도 없음 (예: 템플릿 전체가 흰색인데 transwhite 요청)

    mask_u8 = mask.astype(np.uint8) * 255
    mask_cv = cv2.merge([mask_u8, mask_u8, mask_u8])
    try:
        sqdiff = cv2.matchTemplate(haystack_bgr, template_bgr, cv2.TM_SQDIFF, mask=mask_cv)
    except Exception:
        return []

    # [핵심] 비교대상 픽셀이 전부 tolerance 안에 들어오는 '진짜 매치'는 차이 제곱합이
    # 이 상한선을 절대 넘을 수 없습니다 (채널당 최대 오차가 tolerance일 때가 최댓값).
    # 이 상한선으로 후보를 걸러내면 진짜 매치를 놓치는 일은 없습니다.
    valid_count = int(mask.sum())
    max_possible = valid_count * 3 * (float(tolerance) ** 2)

    ys, xs = np.where(sqdiff <= max_possible + 1e-3)
    if ys.size == 0:
        return []
    order = np.argsort(sqdiff[ys, xs])  # 오차가 작은(더 그럴듯한) 순서로 검증
    ys, xs = ys[order], xs[order]

    tmpl_i = template_bgr.astype(np.int16)
    results = []
    for y, x in zip(ys.tolist(), xs.tolist()):
        sub = haystack_bgr[y:y + th, x:x + tw].astype(np.int16)
        diff = np.abs(sub - tmpl_i)                  # (th, tw, 3)
        within = np.all(diff <= tolerance, axis=2)     # (th, tw)
        if (within | ~mask).all():                     # 무시할 픽셀은 항상 통과 취급
            results.append((x, y))
            if max_matches is not None and len(results) >= max_matches:
                break
    return results


def _dedupe_boxes(boxes):
    """중심이 서로 가까운(템플릿 크기의 절반 이내) 결과를 하나로 합칩니다.
    같은 대상을 놓고 1px씩 밀린 매치가 여러 개 나오는 걸 방지합니다."""
    kept = []
    for b in boxes:
        cx, cy = b.left + b.width / 2, b.top + b.height / 2
        dup = False
        for k in kept:
            kcx, kcy = k.left + k.width / 2, k.top + k.height / 2
            if abs(cx - kcx) < max(b.width, 1) / 2 and abs(cy - kcy) < max(b.height, 1) / 2:
                dup = True
                break
        if not dup:
            kept.append(b)
    return kept


# ==========================================================
# 공개 API
# ==========================================================
def locate_transwhite(image_name_or_path, region, tolerance=DEFAULT_TOLERANCE):
    """흰 배경을 무시하고 픽셀 단위로 비교해서 찾습니다 (AHK의 *TransWhite와 동일한 개념).
    반환: MatchBox 또는 못 찾으면 None."""
    _path, template_bgr = _load_template(image_name_or_path)
    if template_bgr is None:
        return None
    haystack_bgr = _grab_region(region)
    if haystack_bgr is None:
        return None

    th, tw = template_bgr.shape[:2]
    x1, y1 = region[0], region[1]
    mask = _white_mask(template_bgr)
    matches = _find_matches(template_bgr, mask, haystack_bgr, tolerance, max_matches=1)
    if not matches:
        return None
    x, y = matches[0]
    return MatchBox(x1 + x, y1 + y, tw, th)


def locate_smart(image_name, region, tolerance=DEFAULT_TOLERANCE, transwhite_tolerance=None):
    """이미지 1개를 (1단계: 전체 픽셀 비교 -> 2단계: 흰배경 무시 비교) 순서로 찾습니다.

    tolerance: 1단계(전체 비교) 오차범위.
    transwhite_tolerance: 2단계(흰배경 무시) 오차범위. 생략하면 tolerance와 같은 값을 씁니다.
    반환: MatchBox 또는 둘 다 실패하면 None.
    """
    if transwhite_tolerance is None:
        transwhite_tolerance = tolerance

    _path, template_bgr = _load_template(image_name)
    if template_bgr is None:
        return None
    haystack_bgr = _grab_region(region)
    if haystack_bgr is None:
        return None

    th, tw = template_bgr.shape[:2]
    x1, y1 = region[0], region[1]

    # 1단계: 흰색 포함 전체 픽셀 비교
    matches = _find_matches(template_bgr, None, haystack_bgr, tolerance, max_matches=1)
    if matches:
        x, y = matches[0]
        return MatchBox(x1 + x, y1 + y, tw, th)

    # 2단계: 흰 배경 무시하고 재시도 (같은 스크린샷을 재사용해서 한 번 더 캡처하지 않습니다)
    mask = _white_mask(template_bgr)
    matches = _find_matches(template_bgr, mask, haystack_bgr, transwhite_tolerance, max_matches=1)
    if not matches:
        return None
    x, y = matches[0]
    return MatchBox(x1 + x, y1 + y, tw, th)


def locate_all(image_name, region, tolerance=DEFAULT_TOLERANCE, transwhite=False, max_matches=None):
    """region 안에서 이미지의 모든 위치를 찾습니다 (이미지테스터처럼 여러 개를 다 보고
    싶을 때 씁니다). transwhite=True면 흰 배경을 무시하고 비교합니다.
    반환: MatchBox 리스트 (오차가 작은 순서, 중복 제거됨)."""
    _path, template_bgr = _load_template(image_name)
    if template_bgr is None:
        return []
    haystack_bgr = _grab_region(region)
    if haystack_bgr is None:
        return []

    th, tw = template_bgr.shape[:2]
    x1, y1 = region[0], region[1]
    mask = _white_mask(template_bgr) if transwhite else None
    matches = _find_matches(template_bgr, mask, haystack_bgr, tolerance, max_matches=max_matches)
    boxes = [MatchBox(x1 + x, y1 + y, tw, th) for x, y in matches]
    return _dedupe_boxes(boxes)


def click_smart(controller, image_name, region, tolerance=DEFAULT_TOLERANCE,
                 transwhite_tolerance=None, offset=(0, 0)):
    """locate_smart로 찾은 뒤, 찾았으면 중심 좌표를 클릭까지 합니다.

    controller: click_at(x, y)를 갖고 있는 객체 (예: zeus_gui.ZeusController).
    offset: 중심 좌표에서 더 옮겨서 클릭하고 싶을 때 (dx, dy).
    반환: 찾아서 클릭했으면 True, 못 찾았으면 False.
    """
    box = locate_smart(image_name, region, tolerance, transwhite_tolerance)
    if not box:
        return False
    cx = box.left + box.width // 2 + offset[0]
    cy = box.top + box.height // 2 + offset[1]
    controller.click_at(cx, cy)
    return True