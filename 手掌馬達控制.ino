#include <Servo.h>

// 伺服馬達宣告
Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;
Servo servo7;

// 變數
int gestureNumber = 0;
int lastGestureNumber = -1;
unsigned long lastGestureTime = 0;
const unsigned long timeoutDuration = 1000; // 超時時間 1 秒
bool servosDetached = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) { }

  Serial.flush();
  attachAllServos();
  Serial.println("Arduino is ready");
}

void loop() {
  if (Serial.available() > 0) {
    String inputStr = Serial.readStringUntil('\n');
    inputStr.trim();

    if (inputStr.length() > 0) {
      int newGestureNumber = inputStr.toInt();
      if (newGestureNumber >= 0 && newGestureNumber < 64) {
        gestureNumber = newGestureNumber;
        Serial.print("Received Gesture Number: ");
        Serial.println(gestureNumber);

        if (gestureNumber != lastGestureNumber) {
          if (servosDetached) {
            attachAllServos();
          }
          updateServos(gestureNumber);
          lastGestureNumber = gestureNumber;
          lastGestureTime = millis();
        }
      } else {
        Serial.println("Invalid gesture number received.");
      }
    }
  }

  if (millis() - lastGestureTime > timeoutDuration && !servosDetached) {
    stopAllServos();
  }
}

void updateServos(int gesture) {
  thumbServo.write((gesture & 0x20) ? 180 : 0);    // 第 5 位 (大拇指)
  indexServo.write((gesture & 0x10) ? 0 : 180);    // 第 4 位 (食指)
  middleServo.write((gesture & 0x08) ? 180 : 0);   // 第 3 位 (中指)
  ringServo.write((gesture & 0x04) ? 180 : 0);     // 第 2 位 (無名指)
  pinkyServo.write((gesture & 0x02) ? 180 : 0);    // 第 1 位 (小指)
  servo7.write((gesture & 0x01) ? 110 : 85);       // 第 0 位 (額外動作)
}

void stopAllServos() {
  thumbServo.detach();
  indexServo.detach();
  middleServo.detach();
  ringServo.detach();
  pinkyServo.detach();
  servo7.detach();
  servosDetached = true;
  Serial.println("Servos stopped due to inactivity.");
}

// 重新連接
void attachAllServos() {
  thumbServo.attach(13);
  indexServo.attach(9);
  middleServo.attach(10);
  ringServo.attach(11);
  pinkyServo.attach(12);
  servo7.attach(7);
  servosDetached = false;
  Serial.println("Servos re-attached.");
}
