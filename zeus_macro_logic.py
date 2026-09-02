"""
[제우스 매크로 - 판단/행동 로직]
"1초마다 무엇을 확인하고 무엇을 할지" 결정하는 로직만 모아둔 파일입니다
(MacroLogicMixin). zeus_gui.py의 ZeusController가 이 Mixin을 상속해서 씁니다.

이 파일의 메서드들은 self.log, self.state, self.root, self._click_point_jittered,
self._click_box_jittered, self._click_box_offset, self._double_click_point_jittered,
self._double_click_box_jittered, self._sleep_interruptible, self.drag_from_to,
self.notify_event(TelegramNotifierMixin), self.on_stop 등이 실제로 조합되는 쪽
(ZeusController)에 이미 있다고 가정합니다 - 이 파일 혼자서는 동작하지 않습니다.

핵심 진입점은 _zeus_tick()이며, 나머지는 전부 _zeus_tick이 상황에 따라 부르는
개별 핸들러(_handle_*)와 헬퍼(_perform_*, get_*)입니다.
"""
import time

import image_search
from zeus_constants import (
    SIMPLE_CLICK_IMAGES, OFFSET_CLICK_IMAGES, CONDITIONAL_CLICK_IMAGES,
    ZEUS_HP_IMG, ZEUS_HP_REGION,
    ZEUS_RETURN_CLICK1, ZEUS_RETURN_CLICK2, ZEUS_RETURN_REPEAT, ZEUS_RETURN_REPEAT_GAP_SEC,
    ZEUS_HP_RECHECK_INTERVAL_SEC, ZEUS_HP_RECHECK_MAX_SEC,
    ZEUS_POTION_TRIGGER_IMG, ZEUS_POTION_TRIGGER_REGION, ZEUS_POTION_CONFIRM_WAIT_SEC,
    ZEUS_GROCERY_BUTTON_IMG, ZEUS_GROCERY_BUTTON_REGION,
    ZEUS_SHOP_OPEN_CHECK_IMG, ZEUS_SHOP_OPEN_CHECK_REGION,
    ZEUS_SHOP_OPEN_MAX_WAIT_SEC, ZEUS_SHOP_OPEN_POLL_SEC,
    ZEUS_POTION_CLICKS, ZEUS_POTION_DOUBLE_CLICK, ZEUS_POTION_LAST_CLICK,
    ZEUS_POTION_CLICK_DELAY_SEC, ZEUS_POTION_VERIFY_WAIT_SEC,
    ZEUS_POTION_VERIFY_IMG, ZEUS_POTION_VERIFY_REGION,
    ZEUS_TOWER_TRIGGER_IMG, ZEUS_TOWER_TRIGGER_REGION,
    ZEUS_TOWER_CLICK1, ZEUS_TOWER_CLICK2, ZEUS_TOWER_CLICK_DELAY_SEC,
    ZEUS_TOWER_SCREEN_IMG, ZEUS_TOWER_SCREEN_REGION,
    ZEUS_TOWER_OBSTACLE_IMG, ZEUS_TOWER_OBSTACLE_REGION, ZEUS_TOWER_OBSTACLE_POLL_SEC,
    ZEUS_TOWER_ENTER_CLICK,
    ZEUS_TOWER_EXIT_IMG1, ZEUS_TOWER_EXIT_IMG2, ZEUS_TOWER_EXIT_REGION, ZEUS_TOWER_EXIT_POLL_SEC,
    ZEUS_TOWER_FINISH_CLICK, ZEUS_TOWER_FINISH_GAP_SEC,
    ZEUS_FPDLSWJ_IMG, ZEUS_FPDLSWJ_REGION, ZEUS_FPDLSWJ_STEP2, ZEUS_FPDLSWJ_STEP3,
    ZEUS_FPDLSWJ_WAIT_SEC,
    ZEUS_AUTOBUY_IMG, ZEUS_AUTOBUY_REGION, ZEUS_AUTOBUY_CLICKS,
    ZEUS_AUTOBUY_WAIT_IMG, ZEUS_AUTOBUY_WAIT_REGION, ZEUS_AUTOBUY_REPEAT_CLICK,
    ZEUS_AUTOBUY_REPEAT_DELAY_SEC, ZEUS_AUTOBUY_REPEAT_MAX,
    ZEUS_SKILLBOOK_IMG, ZEUS_SKILLBOOK_REGION, ZEUS_SKILLBOOK_CLICKS,
    ZEUS_RAID_GATE_IMG, ZEUS_RAID_GATE_REGION,
    ZEUS_TOWER_TRIGGER_IMG, ZEUS_TOWER_TRIGGER_REGION,
    ZEUS_TOWER_STEP1, ZEUS_TOWER_STEP2,
    ZEUS_TOWER_SCREEN_IMG, ZEUS_TOWER_SCREEN_REGION,
    ZEUS_TOWER_POPUP_IMG, ZEUS_TOWER_POPUP_REGION, ZEUS_TOWER_POPUP_RECHECK_DELAY_SEC,
    ZEUS_TOWER_ENTER_CLICK,
    ZEUS_TOWER_EXIT_CHECK1_IMG, ZEUS_TOWER_EXIT_CHECK1_REGION,
    ZEUS_TOWER_EXIT_CHECK2_IMG, ZEUS_TOWER_EXIT_CHECK2_REGION, ZEUS_TOWER_EXIT_POLL_SEC,
    ZEUS_TOWER_FINISH_CLICK,
    ZEUS_SUBQUEST_GATE_IMG, ZEUS_SUBQUEST_GATE_REGION_NORMAL, ZEUS_SUBQUEST_GATE_REGION_RAID,
    ZEUS_SUBQUEST_CHECK_IMG, ZEUS_SUBQUEST_CHECK_REGION_NORMAL, ZEUS_SUBQUEST_CHECK_REGION_RAID,
    ZEUS_SUBQUEST_CLICK_NORMAL, ZEUS_SUBQUEST_CLICK_RAID,
    ZEUS_WAIT_IMG, ZEUS_WAIT_REGION, ZEUS_WAIT2_IMG, ZEUS_WAIT2_REGION,
    ZEUS_RHKFGH_IMG, ZEUS_RHKFGH_REGION,
    ZEUS_CHANGKKEUGI1_IMG, ZEUS_CHANGKKEUGI1_REGION,
    ZEUS_CHANGKKEUGI2_IMG, ZEUS_CHANGKKEUGI2_REGION, ZEUS_CHANGKKEUGI2_CLICK,
    ZEUS_NO_MATCH_DRAG_START, ZEUS_NO_MATCH_DRAG_END,
    FALLBACK_CLICK_X, FALLBACK_CLICK_Y, DEFAULT_NO_IMAGE_TIMEOUT_SEC,
    ZEUS_TOLERANCE, ZEUS_TRANSWHITE_TOLERANCE, DEFAULT_STUCK_REPEAT_THRESHOLD,
)


class MacroLogicMixin:
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

    def _zeus_tick(self):
        """한 바퀴치 판단 + 클릭.

        순서:
          0) anfdir0ro.png/anfdiron.png 중 하나라도 있을 때(=사냥중)만 hp.png 확인,
             없으면 귀환로직부터 처리 (최우선 안전 체크. 로딩 중엔 건너뜀)
          1) SIMPLE_CLICK_IMAGES / OFFSET_CLICK_IMAGES / CONDITIONAL_CLICK_IMAGES
             (각 리스트 순서대로) / fpdlswj.png / wkehdrnao.png / tmzlfqnr.png /
             anfdir0ro.png(물약구매) / angksdmlxkq5cmd.png(무한의탑) - 있으면 즉시
             클릭(연속 동작 이미지는 시퀀스 수행)
             (gkdl.png/dpvlrwlsgod.png 여부와 무관)
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

        # 0) [최우선 안전 체크] anfdir0ro.png / anfdiron.png 중 하나라도 있을 때만
        # (=사냥중일 때만) hp.png를 확인합니다. 화면 로딩 중에는 둘 다 안 보여서 hp.png도
        # 당연히 안 보이는데, 이걸 그냥 "hp 없음"으로 오판하면 안 되기 때문입니다.
        hunting_now = (
            image_search.locate_smart(ZEUS_POTION_TRIGGER_IMG, ZEUS_POTION_TRIGGER_REGION,
                                       tolerance=tol, transwhite_tolerance=tw_tol)
            or image_search.locate_smart(ZEUS_POTION_VERIFY_IMG, ZEUS_POTION_VERIFY_REGION,
                                          tolerance=tol, transwhite_tolerance=tw_tol)
        )
        if hunting_now:
            # hp.png가 정상적으로 보일 때는(대부분의 경우) 아무것도 안 하고 그냥 통과합니다 -
            # 여기서 활동 타이머를 건드리지 않아야 미인식 타임아웃 로직이 정상 작동합니다.
            hp_found = image_search.locate_smart(ZEUS_HP_IMG, ZEUS_HP_REGION,
                                                  tolerance=tol, transwhite_tolerance=tw_tol)
            if not hp_found:
                self._handle_hp_missing_sequence()
                return

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

        # anfdir0ro.png(물약구매 트리거) - 바로 발동하지 않고, 발견되면 4초 뒤에
        # 한 번 더 확인해서 그때도 여전히 보여야 물약구매 로직을 시작합니다
        # (순간적으로 지나가는 오탐 방지).
        box = image_search.locate_smart(ZEUS_POTION_TRIGGER_IMG, ZEUS_POTION_TRIGGER_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self.log(f"- anfdir0ro 발견 -> {ZEUS_POTION_CONFIRM_WAIT_SEC:.0f}초 후 재확인")
            self._sleep_interruptible(ZEUS_POTION_CONFIRM_WAIT_SEC)
            if self.state == "IDLE":
                return
            box2 = image_search.locate_smart(ZEUS_POTION_TRIGGER_IMG, ZEUS_POTION_TRIGGER_REGION,
                                              tolerance=tol, transwhite_tolerance=tw_tol)
            if box2:
                self._handle_potion_purchase_sequence()
                self._mark_activity()
                return
            else:
                self.log("- anfdir0ro 재확인 실패 - 물약구매 취소, 계속 진행")
                now = time.time()  # 4초를 대기했으니, 이후 타임아웃 계산을 위해 시각을 다시 잽니다.

        # angksdmlxkq5cmd.png(무한의 탑 트리거) - 발견되면 무한의 탑 로직 전체를 수행합니다.
        box = image_search.locate_smart(ZEUS_TOWER_TRIGGER_IMG, ZEUS_TOWER_TRIGGER_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._handle_tower_sequence()
            self._mark_activity()
            return

        # [레이드 게이트] fpdlem.png(레이드) 여부에 따라 서브퀘스트(tjqm/tjqmznptmxm)를
        # 검색할 영역만 바꿉니다 (로직 자체는 그대로 - 생략하지 않습니다). 레이드 중엔
        # 화면 배치가 달라져서 같은 이미지가 다른 위치에 나타나기 때문입니다.
        raid_active = image_search.locate_transwhite(ZEUS_RAID_GATE_IMG, ZEUS_RAID_GATE_REGION,
                                                       tolerance=tw_tol)
        gate_region = ZEUS_SUBQUEST_GATE_REGION_RAID if raid_active else ZEUS_SUBQUEST_GATE_REGION_NORMAL
        check_region = ZEUS_SUBQUEST_CHECK_REGION_RAID if raid_active else ZEUS_SUBQUEST_CHECK_REGION_NORMAL
        subquest_click = ZEUS_SUBQUEST_CLICK_RAID if raid_active else ZEUS_SUBQUEST_CLICK_NORMAL

        # [서브퀘스트] 메인퀘스트(gkdl.png) 쪽보다 먼저 확인합니다. tjqmznptmxm.png가
        # 보이면 서브퀘스트가 진행 중이라는 뜻이라, 이번 턴은 서브퀘스트만 처리하고
        # 메인퀘스트 쪽(gkdl.png 등)은 아예 확인하지 않습니다.
        if image_search.locate_smart(ZEUS_SUBQUEST_GATE_IMG, gate_region,
                                      tolerance=tol, transwhite_tolerance=tw_tol):
            if image_search.locate_smart(ZEUS_SUBQUEST_CHECK_IMG, check_region,
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
                         f"{subquest_click}")
                self._click_point_jittered(*subquest_click)
                self._subquest_wait_start = now  # 매 턴마다 계속 클릭하지 않도록 리셋
                self._mark_activity()
            # 아직 n초가 안 지났으면 이번 턴은 그냥 대기 (메인퀘스트로 안 넘어감)
            return

        # tjqmznptmxm.png 자체가 안 보이면 서브퀘스트가 없는 것이므로 타이머만 정리합니다.
        self._subquest_wait_start = None

        # (서브퀘스트가 없었으면) 메인퀘스트(gkdl.png 등) 쪽으로 진행합니다.

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

    def _perform_return_logic(self):
        """귀환로직: (45,195) -> (682,515) 클릭 쌍을 ZEUS_RETURN_REPEAT회 빠르게
        반복합니다. hp.png 미확인 시, 그리고 물약구매 로직 시작할 때 재사용합니다."""
        self.log("- 귀환로직 수행")
        for i in range(ZEUS_RETURN_REPEAT):
            self._click_point_jittered(*ZEUS_RETURN_CLICK1)
            self._click_point_jittered(*ZEUS_RETURN_CLICK2)
            if i < ZEUS_RETURN_REPEAT - 1:
                time.sleep(ZEUS_RETURN_REPEAT_GAP_SEC)

    def _handle_hp_missing_sequence(self):
        """hp.png가 안 보일 때: 귀환로직 -> 10초 대기 -> wkqghkqjxms.png(잡화버튼) 확인을
        최대 30초까지 반복합니다. wkqghkqjxms.png가 보이면 귀환이 잘 된 것으로 판단하고
        정상 흐름으로 복귀합니다. 그래도 안 보이면 텔레그램 알림 후 정지합니다."""
        self.log("- hp 미확인 -> 귀환로직 시작")
        self._perform_return_logic()

        tol = self.get_tolerance()
        tw_tol = self.get_transwhite_tolerance()
        elapsed = 0.0
        while elapsed < ZEUS_HP_RECHECK_MAX_SEC and self.state != "IDLE":
            self._sleep_interruptible(ZEUS_HP_RECHECK_INTERVAL_SEC)
            elapsed += ZEUS_HP_RECHECK_INTERVAL_SEC
            if self.state == "IDLE":
                return
            found = image_search.locate_smart(ZEUS_GROCERY_BUTTON_IMG, ZEUS_GROCERY_BUTTON_REGION,
                                               tolerance=tol, transwhite_tolerance=tw_tol)
            if found:
                self.log(f"- wkqghkqjxms 확인됨 ({elapsed:.0f}초 경과) - 귀환 성공, 정상 흐름으로 복귀")
                self._mark_activity()
                return
            self.log(f"- wkqghkqjxms 여전히 안 보임 ({elapsed:.0f}초 경과)")

        if self.state == "IDLE":
            return
        msg = f"귀환 후 {ZEUS_HP_RECHECK_MAX_SEC:.0f}초 동안 wkqghkqjxms.png가 확인되지 않았습니다. 매크로를 정지합니다."
        self.log(f"- [경고] {msg}")
        self.notify_event("stuck", msg, once=False)
        self.root.after(0, self.on_stop)

    def _handle_potion_purchase_sequence(self):
        """anfdir0ro.png 발견 시 물약구매 전체 흐름을 수행합니다:
          1) 귀환로직 수행 (_perform_return_logic 재사용)
          2) 10초 대기
          3) 잡화버튼(wkqghkqjxms.png) 클릭
          4) 잡화상점 열림(wkehdrnao.png) 확인 - 최대 30초, 안 열리면 텔레그램+정지
          5) 열렸으면 고정좌표 클릭 4단계(마지막 직전은 더블클릭)
          6) 3초 대기 후 anfdiron.png로 구매 성공 여부 확인 (실패해도 경고 로그만, 정지 안 함)
        """
        self.log("- anfdir0ro 발견 -> 물약구매 로직 시작")
        self._perform_return_logic()

        self.log("- 10초 대기")
        self._sleep_interruptible(10.0)
        if self.state == "IDLE":
            return

        tol = self.get_tolerance()
        tw_tol = self.get_transwhite_tolerance()

        box = image_search.locate_smart(ZEUS_GROCERY_BUTTON_IMG, ZEUS_GROCERY_BUTTON_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._click_box_jittered(box)
            self.log("- 잡화버튼(wkqghkqjxms) 클릭")
        else:
            self.log("- ⚠ 잡화버튼(wkqghkqjxms)을 못 찾았습니다 - 그래도 상점이 열리는지는 계속 확인합니다")

        # [잡화상점 열림 확인] wkehdrnao.png가 보일 때까지 최대 30초 대기.
        elapsed = 0.0
        shop_open = False
        while elapsed < ZEUS_SHOP_OPEN_MAX_WAIT_SEC and self.state != "IDLE":
            found = image_search.locate_smart(ZEUS_SHOP_OPEN_CHECK_IMG, ZEUS_SHOP_OPEN_CHECK_REGION,
                                               tolerance=tol, transwhite_tolerance=tw_tol)
            if found:
                shop_open = True
                break
            self._sleep_interruptible(ZEUS_SHOP_OPEN_POLL_SEC)
            elapsed += ZEUS_SHOP_OPEN_POLL_SEC

        if self.state == "IDLE":
            return

        if not shop_open:
            msg = (f"잡화상점이 {ZEUS_SHOP_OPEN_MAX_WAIT_SEC:.0f}초 동안 열리지 않았습니다. "
                   f"매크로를 정지합니다.")
            self.log(f"- [경고] {msg}")
            self.notify_event("stuck", msg, once=False)
            self.root.after(0, self.on_stop)
            return

        self.log("- 잡화상점 열림 확인됨 - 물약구매 클릭 시작")
        for x, y in ZEUS_POTION_CLICKS:
            self._click_point_jittered(x, y)
            self.log(f"  ({x},{y}) 클릭 완료")
            self._sleep_interruptible(ZEUS_POTION_CLICK_DELAY_SEC)
        self._double_click_point_jittered(*ZEUS_POTION_DOUBLE_CLICK)
        self.log(f"  {ZEUS_POTION_DOUBLE_CLICK} 더블클릭 완료")
        self._sleep_interruptible(ZEUS_POTION_CLICK_DELAY_SEC)
        self._click_point_jittered(*ZEUS_POTION_LAST_CLICK)
        self.log(f"  {ZEUS_POTION_LAST_CLICK} 클릭 완료")

        self.log(f"- {ZEUS_POTION_VERIFY_WAIT_SEC:.0f}초 대기 후 구매 확인")
        self._sleep_interruptible(ZEUS_POTION_VERIFY_WAIT_SEC)
        if self.state == "IDLE":
            return

        verified = image_search.locate_smart(ZEUS_POTION_VERIFY_IMG, ZEUS_POTION_VERIFY_REGION,
                                              tolerance=tol, transwhite_tolerance=tw_tol)
        if verified:
            self.log("- anfdiron 확인됨 - 물약구매 정상 완료")
        else:
            self.log("- ⚠ anfdiron을 못 찾았습니다 - 물약구매가 제대로 안 됐을 수 있습니다 "
                     "(일단 정상 흐름으로 계속 진행합니다)")
        self.log("- 물약구매 로직 종료")

    def _handle_tower_sequence(self):
        """angksdmlxkq5cmd.png 발견 시 '무한의 탑' 전체 흐름을 수행합니다:
          1) (1225,65) 클릭 -> 2초 대기 -> (885,665) 클릭 -> 2초 대기 (탑 화면 진입)
          2) dusthrwlsgodcpzm.png가 있으면 좌상단 클릭하고 사라질 때까지 반복
          3) dlqwkd.png 클릭 -> 2초 대기 -> (733,500) 클릭 (입장 완료)
          4) dpvlrznptmxm.png 또는 tjqmznptmxm.png가 보일 때까지 대기 (일반필드 복귀 확인)
          5) (1000,160) 더블클릭 -> 2초 대기 -> 다시 더블클릭 (종료)
        """
        self.log("- angksdmlxkq5cmd 발견 -> 무한의 탑 로직 시작")
        tol = self.get_tolerance()
        tw_tol = self.get_transwhite_tolerance()

        self._click_point_jittered(*ZEUS_TOWER_CLICK1)
        self.log(f"  {ZEUS_TOWER_CLICK1} 클릭 완료")
        self._sleep_interruptible(ZEUS_TOWER_CLICK_DELAY_SEC)
        if self.state == "IDLE":
            return

        self._click_point_jittered(*ZEUS_TOWER_CLICK2)
        self.log(f"  {ZEUS_TOWER_CLICK2} 클릭 완료")
        self._sleep_interruptible(ZEUS_TOWER_CLICK_DELAY_SEC)
        if self.state == "IDLE":
            return

        # [장애물 제거] dusthrwlsgodcpzm.png가 있으면 좌상단을 클릭(자동으로 마우스도
        # 치워짐)하고, 사라질 때까지 반복해서 재확인합니다.
        while self.state != "IDLE":
            box = image_search.locate_smart(ZEUS_TOWER_OBSTACLE_IMG, ZEUS_TOWER_OBSTACLE_REGION,
                                             tolerance=tol, transwhite_tolerance=tw_tol)
            if not box:
                break
            self._click_point_jittered(box.left, box.top)
            self.log("- dusthrwlsgodcpzm 발견 -> 좌상단 클릭")
            self._sleep_interruptible(ZEUS_TOWER_OBSTACLE_POLL_SEC)
        if self.state == "IDLE":
            return

        # [입장] dlqwkd.png 클릭 -> 2초 대기 -> (733,500) 클릭
        box = image_search.locate_smart(ZEUS_TOWER_SCREEN_IMG, ZEUS_TOWER_SCREEN_REGION,
                                         tolerance=tol, transwhite_tolerance=tw_tol)
        if box:
            self._click_box_jittered(box)
            self.log("- dlqwkd 클릭")
        else:
            self.log("- ⚠ dlqwkd을 못 찾았습니다 - 그래도 입장 클릭은 진행합니다")
        self._sleep_interruptible(ZEUS_TOWER_CLICK_DELAY_SEC)
        if self.state == "IDLE":
            return
        self._click_point_jittered(*ZEUS_TOWER_ENTER_CLICK)
        self.log(f"- {ZEUS_TOWER_ENTER_CLICK} 클릭 -> 입장 완료")

        # [퇴장 대기] dpvlrznptmxm.png 또는 tjqmznptmxm.png가 보일 때까지 대기합니다.
        # 탑 체류시간이 정해져 있지 않아서, 정지 버튼이 눌릴 때까지 계속 확인합니다.
        self.log("- 무한의 탑 진행 중 - 일반필드 복귀 대기")
        while self.state != "IDLE":
            found = (image_search.locate_smart(ZEUS_TOWER_EXIT_IMG1, ZEUS_TOWER_EXIT_REGION,
                                                tolerance=tol, transwhite_tolerance=tw_tol)
                     or image_search.locate_smart(ZEUS_TOWER_EXIT_IMG2, ZEUS_TOWER_EXIT_REGION,
                                                   tolerance=tol, transwhite_tolerance=tw_tol))
            if found:
                break
            self._sleep_interruptible(ZEUS_TOWER_EXIT_POLL_SEC)
        if self.state == "IDLE":
            return

        self.log("- 일반필드 복귀 확인됨 - 마무리 더블클릭 시작")
        self._double_click_point_jittered(*ZEUS_TOWER_FINISH_CLICK)
        self._sleep_interruptible(ZEUS_TOWER_FINISH_GAP_SEC)
        if self.state == "IDLE":
            return
        self._double_click_point_jittered(*ZEUS_TOWER_FINISH_CLICK)
        self.log("- 무한의 탑 로직 종료")

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