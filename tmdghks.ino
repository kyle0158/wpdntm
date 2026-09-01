#include <Keyboard.h>
#include <Mouse.h>

// [구조체 정의] 각 매크로 단계의 키, 누르는 시간, 대기 시간 설정
struct MacroStep {
  char key;
  int pressTime;
  int waitTime;
};

// [스킬 사이클] t와 r 키가 포함된 공격 시퀀스
MacroStep sequence[] = {
  {'1', 80, 100}, {'5', 50, 50}, {'5', 50, 50},
  {'1', 70, 60},  {'1', 80, 80},   {'t', 80, 80},
  {'t', 50, 50},  {'r', 50, 50},   {'r', 50, 75},
  {'t', 50, 80}, {'r', 80, 80}, {'t', 80, 85}, {'r', 80, 85}, {'f', 100, 100}
};

const int totalSteps = sizeof(sequence) / sizeof(sequence[0]);
int currentStep = 0;
unsigned long stepTimer = 0;
bool isKeyHeld = false;

unsigned long lastCommTime = 0;
unsigned long lastLeftPress = 0;  
unsigned long lastRightPress = 0; 
bool isRunningMacro = false;
bool isDungeonMode = false;
bool isMoving = false;
unsigned long moveEndTime = 0;

// [기능 활성화 변수] 파이썬 UI의 체크박스 상태와 동기화됨
bool useTSkill = true; 
bool useRSkill = true; 

void setup() {
  Serial.begin(115200); // 파이썬과 통신 속도 일치
  Keyboard.begin();
  Mouse.begin();
  randomSeed(analogRead(0));
  lastCommTime = millis();
}

// [초기화] 모든 입력 상태를 해제하고 변수 리셋
void releaseAllControls() {
  isRunningMacro = false;
  isMoving = false; 
  currentStep = 0;
  isKeyHeld = false;
  Keyboard.releaseAll();
  Mouse.release(MOUSE_LEFT);
  Mouse.release(MOUSE_RIGHT);
}

void loop() {
  unsigned long now = millis();

  // [안전장치] 2초 이상 파이썬에서 신호(Heartbeat 등)가 없으면 정지
  if (now - lastCommTime > 2000) {
    releaseAllControls();
    lastCommTime = now;
  }

  while (Serial.available() > 0) {
    lastCommTime = now;
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) continue;

    // 1. 마우스 휠 제어 (화면 확대)
    if (input.startsWith("MW:")) {
      for(int i=0; i<20; i++) {
        Mouse.move(0, 0, -1);
        delay(15);
      }
      continue;
    }

    // 2. 마우스 상대 이동 제어 (화면 회전)
    if (input.startsWith("MOVE:")) {
      int firstColon = input.indexOf(':');
      int secondColon = input.indexOf(':', firstColon + 1);
      if (firstColon != -1 && secondColon != -1) {
        int moveX = input.substring(firstColon + 1, secondColon).toInt();
        int moveY = input.substring(secondColon + 1).toInt();
        Mouse.move(moveX, moveY, 0);
      }
      continue;
    }

    // 3. [핵심] T/R 스킬 활성화/비활성화 상태 업데이트
    if (input == "TON") { useTSkill = true; continue; }
    else if (input == "TOFF") { useTSkill = false; continue; }
    else if (input == "RON") { useRSkill = true; continue; }
    else if (input == "ROFF") { useRSkill = false; continue; }

    char header = input[0];

    // 4. 개별 키보드 입력 처리 (KPx: Press, KRx: Release)
    if (header == 'K' && input.length() >= 3) {
      char act = input[1];
      char key = input[2];
      uint8_t targetKey = (uint8_t)key;
      
      if (key == 1) targetKey = KEY_UP_ARROW;
      else if (key == 2) targetKey = KEY_DOWN_ARROW;
      else if (key == 3) targetKey = KEY_LEFT_ARROW;
      else if (key == 4) targetKey = KEY_RIGHT_ARROW;
      else if (key == '_') targetKey = ' ';
      else if (key == 'L') targetKey = KEY_LEFT_SHIFT;
      else if (key == 'T') targetKey = KEY_TAB;
      else if (key == 'E') targetKey = KEY_ESC;   // [추가] ESC - 캐릭터 전환 루틴에서 사용

      if (act == 'P') Keyboard.press(targetKey);
      else if (act == 'R') Keyboard.release(targetKey);
    } 
    // 5. 마우스 클릭 처리
    else if (header == 'M' && input.length() >= 3) {
      char btn = input[1];
      char act = input[2];
      if (btn == '1') {
        if (act == 'P') { if (now - lastLeftPress > 150) { Mouse.press(MOUSE_LEFT); lastLeftPress = now; } } 
        else Mouse.release(MOUSE_LEFT);
      } 
      else if (btn == '2') {
        if (act == 'P') { if (now - lastRightPress > 150) { Mouse.press(MOUSE_RIGHT); lastRightPress = now; } } 
        else Mouse.release(MOUSE_RIGHT);
      }
    }
    else {
      if (header == 'A') { isRunningMacro = true; isDungeonMode = false; stepTimer = now; }
      else if (header == 'D') { isRunningMacro = true; isDungeonMode = true; stepTimer = now; }
      else if (header == 'F') { releaseAllControls(); }
    }
  }

  // 매크로 실행 중일 때만 동작
  if (isRunningMacro) handleMacro(now);

  // 캐릭터 미세 이동 제어
  if (isMoving && now >= moveEndTime) {
    Keyboard.release('w'); Keyboard.release('s');
    Keyboard.release('a'); Keyboard.release('d');
    isMoving = false;
  }
}

// [매크로 처리 로직]
void handleMacro(unsigned long now) {
  char currentKey = sequence[currentStep].key;

  // [핵심 수정] 현재 키가 't'나 'r'인데 비활성화 상태라면 해당 단계를 스킵함
  if ((currentKey == 't' && !useTSkill) || (currentKey == 'r' && !useRSkill)) {
    currentStep++;
    if (currentStep >= totalSteps) currentStep = 0;
    stepTimer = now; 
    return;
  }

  // 키 누르기 및 떼기 타이밍 제어
  if (!isKeyHeld) {
    if (now - stepTimer >= (unsigned long)sequence[currentStep].waitTime) {
      Keyboard.press(sequence[currentStep].key);
      stepTimer = now;
      isKeyHeld = true;
    }
  } else {
    if (now - stepTimer >= (unsigned long)sequence[currentStep].pressTime) {
      Keyboard.release(sequence[currentStep].key);
      stepTimer = now;
      isKeyHeld = false;
      currentStep++;

      // 시퀀스 한 바퀴 완료 시 처리
      if (currentStep >= totalSteps) {
        currentStep = 0;
        // 필드 모드(이동o)일 때만 무작위 이동 추가
        if (!isDungeonMode && !isMoving) { 
           char moveKeys[] = {'w', 's', 'a', 'd'};
           Keyboard.press(moveKeys[random(0, 4)]);
           moveEndTime = now + 80; 
           isMoving = true;
        }
      }
    }
  }
}