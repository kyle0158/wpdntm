# 아이온2 매크로 - 폴더 정리 내역

## 이번에 한 일 (폴더/파일 정리만, 기능 개선은 아직 안 함)

### 1. 메인 코드 2개 (이름만 바꿈, 로직은 원본과 동일 + 경로만 수정)
- `aion2_controller.pyw` (원래 `gostop.pyw`)
  → 실제 메인 매크로: 아두이노 키입력, 가방정리/맵이동 UI클릭, 스케줄(사냥→퇴장), 화면회전, 이미지감지 정지, 캡처툴 연동
- `daeva_alert_bot.pyw` (원래 `DBZ.pyw`)
  → 창 정렬 + 사망/골드풀/데바인증 감지 → 텔레그램 알림 전용 (요청하신 대로 아직 메인과 분리 유지)

**바뀐 부분(경로만)**
- 이미지 참조 폴더를 `images/` 하나로 통일 (`captured_images` 폴더 의존 제거)
- 공백이 있던 파일명 `menu Select-character.png` → `menu_select_character.png` 로 변경 (경로 문제 방지)
- `daeva_alert_bot.pyw`의 이미지 경로를 `images/` 기준으로 수정

### 2. `images/` — 코드가 실제로 쓰는 이미지만 모음
death.png, death2.png, gold.png, daeva.png, map_pin.png, kibelisk.png, move.png,
menu.png, charselect.png, menu_select_character.png, kinabar.png, kina.png, dragonball_bg.png

### 3. `old_versions/` — 지금 코드로 대체된 구버전 (실행 대상 아님, 참고용 백업)
- `mac_old_serial_macro.pyw` (원래 `mac.pyw`) — aion2_controller.pyw 기능에 이미 포함된 초기 버전
- `image_confidence_checker.pyw` (원래 `#이미지인식율확인.pyw`) — 인식률 튜닝용 디버그 도구
- `daeva_alert_bot_v1_OLD.pyw` (원래 `#드래곤볼GUI.pyw`) — daeva_alert_bot.pyw 이전 버전

  ⚠️ **보안 참고**: 이 파일 원본에는 실제 텔레그램 BOT_TOKEN과 CHAT_ID가 그대로 하드코딩되어 있었습니다.
  여기 백업본에서는 지웠지만, **혹시 그 토큰을 지금도 쓰신다면 텔레그램 봇 토큰을 재발급(BotFather에서 /revoke)** 하시는 걸 권장드려요.

### 4. `unused_images_backup/` — 코드에서 안 쓰는 이미지 (확인 후 진짜 삭제해도 되는 것들)
alert.png, deba_alert.png, debug_screen.png, gold_full_backup.png, if.png,
inven_btn1/2.png, map_pin2.png, noname.png, pickup.png, potion.png, q2.png,
shockrelief.png, success.png, u.png, img_1~4.png, 'q_full.png

### 5. 완전히 제외한 것 (원본 zip에는 있었지만 여기엔 없음)
- `captool.py`, `testtest_cap.py` — 캡처 툴 (요청하신 대로 제외. 코드에서 없어도 정상 동작하도록 이미 예외처리 되어 있어서 손 안 댔습니다)
- `__pycache__/`, 빈 폴더(`actions/`, `testtest_cap/`)
- `error_log.txt`, `log_history.txt`, `macro_history.txt` — 실행하면 다시 쌓이는 로그
- `captured_images.zip`, `captured_images (2).zip` — 중복 백업

## 아직 안 한 것 (다음 단계)
- `config.py` 분리 (지금은 `main.pyw` 안에 나머지 상수들이 그대로 있음 — 자주 바꾸지 않는 값들은 아직 안 옮김)
- GUI 탭 구조로 재설계
- (나중에) daeva_alert_bot을 메인 GUI에 통합

---

## main.pyw 개선 내역 (2차 작업)

1. **마우스 좌표 표시**: 우측 상단에 모니터 화면 기준 절대좌표(X, Y)를 100ms마다 갱신해서 보여줍니다.
2. **화면 회전 값 입력 가능**: 기존엔 읽기전용(400 고정)이었는데, 이제 값과 반복 간격(초)을 직접 입력할 수 있습니다.
3. **회전 테스트 = 지속 반복 토글**: 버튼을 누르면 (AION2 창 활성화 → 회전 1회)를 설정한 간격마다 계속 반복합니다. 다시 누르거나 프로그램을 종료하면 멈춥니다.
4. **스킬매크로(F9) 간격 공개 + 입력 가능**:
   - 기존 값: F키는 15~20초 사이 랜덤, Q키 재입력은 90~150초 사이 랜덤 (매크로 탐지 회피 목적으로 추정)
   - 이 랜덤범위를 유지하면서 최소/최대값을 GUI에서 직접 입력할 수 있게 바꿨습니다.
5. **스케줄(Del) 사냥시간**: 콤보박스(1/40/55분 중 선택) → 직접 숫자 입력(분)으로 변경
6. **캡처 툴 GUI 제거**: "📷 캡처 툴" 버튼과 관련 코드(`open_capture_tool`, `import captool` 등)를 완전히 삭제했습니다.
7. **그 외 로직은 그대로 유지** (가방정리/맵이동/스케줄 실행 흐름 등 손대지 않음)
8. **GUI 창 크기**: 가로(320)는 그대로, 세로는 새 입력칸들이 들어갈 자리가 필요해서 520→**600**으로 늘렸습니다. (요청하신 크기 유지 원칙과 살짝 어긋나는 부분이라 별도로 말씀드립니다 — 너무 빡빡하면 다시 줄이거나 스크롤 영역으로 바꿀 수 있어요)
9. **내부 배치**: 기존 스타일(라벨프레임 + 버튼) 유지하면서 새 입력 섹션만 추가/교체
10. **설정 저장/불러오기**: "💾 설정 저장" 버튼 → `config.json`에 저장. 프로그램을 다시 켜면 저장된 값을 자동으로 불러옵니다. (파일이 없거나 손상되어도 기본값으로 정상 실행)
11. **화면회전 체크박스**: "사용" 체크박스가 꺼져 있으면 회전 테스트 버튼을 눌러도 로그에 안내만 남고 동작하지 않습니다. 체크박스를 끄면 반복 중이던 테스트도 즉시 멈춥니다.

### 저장되는 설정값 (`config.json`)
`rotation_enabled`, `rotation_amount`, `rotation_interval_sec`, `f_press_min/max`, `q_repress_min/max`, `schedule_minutes`

### 파일명 변경
`aion2_controller.pyw` → **`main.pyw`** (콘솔창 없이 실행되도록 `.pyw` 확장자 유지 — `.py`로 바꾸면 실행 시 검은 cmd 창이 함께 뜹니다)

