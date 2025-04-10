import mediapipe as mp
import cv2
import numpy as np
import itertools
import serial
import time
from time import sleep

# 初始化 
ser = serial.Serial('COM3', 9600) 

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# 生成所有 64 種可能的手勢（6 位：5 根手指 + 6,9,10 號座標角度）
gesture_combinations = list(itertools.product([0, 1], repeat=6))
gesture_dict = {tuple(gesture): i + 1 for i, gesture in enumerate(gesture_combinations)}

# 初始化手勢 [大拇指, 食指, 中指, 無名指, 小指, 6-9-10角度]
current_locations = [[0], [0], [0], [0], [0], [0]]  # 初始化所有 current_location
hand_gesture = [0, 0, 0, 0, 0, 0]  # 增加第六位代表 6,9,10 角度
last_gesture_number = -1
last_send_time = 0
send_interval = 0.5  # 設置間隔為 0.5 秒
joint_list = [[4, 3, 2], [8, 7, 6], [12, 11, 10], [16, 15, 14], [20, 19, 18]]  # 大拇指、食指、中指、無名指、小指

def handle_joint(joint, angle, current_location, joint_id, joint_index, angle_limit=170):
    global hand_gesture
    if 0 < angle <= angle_limit:
        if current_location[0] == 0:
            current_location[0] = 1
            hand_gesture[joint_index] = 1  
    else:
        if current_location[0] == 1:
            current_location[0] = 0
            hand_gesture[joint_index] = 0  

# 定義每個手指的關節，並按照 [大拇指, 食指, 中指, 無名指, 小指] 順序
joints = {
    (4, 3, 2): (current_locations[0], 5, 160, 0),   # 大拇指
    (8, 7, 6): (current_locations[1], 1, 170, 1),   # 食指
    (12, 11, 10): (current_locations[2], 2, 170, 2), # 中指
    (16, 15, 14): (current_locations[3], 3, 170, 3), # 無名指
    (20, 19, 18): (current_locations[4], 4, 165, 4)  # 小指
}

def process_all_joints(joint, angle):
    for joint_key, (current_location, joint_id, angle_limit, joint_index) in joints.items():
        if joint == list(joint_key):
            handle_joint(joint, angle, current_location, joint_id, joint_index, angle_limit)
            break

def draw_finger_angles(image, results, joint_list):
    global hand_gesture, last_gesture_number, last_send_time
    for hand in results.multi_hand_landmarks:
        for joint in joint_list:
            a = np.array([hand.landmark[joint[0]].x, hand.landmark[joint[0]].y])
            b = np.array([hand.landmark[joint[1]].x, hand.landmark[joint[1]].y])
            c = np.array([hand.landmark[joint[2]].x, hand.landmark[joint[2]].y])
            radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
                a[1] - b[1], a[0] - b[0]
            )
            angle = np.abs(radians * 180.0 / np.pi)

            if angle > 180.0:
                angle = 360 - angle

            cv2.putText(
                image,
                str(round(angle, 2)),
                tuple(np.multiply(b, [640, 480]).astype(int)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            
            process_all_joints(joint, angle)

        # 將當前的手勢轉換為元組，然後查找對應的編號
        gesture_tuple = tuple(hand_gesture)
        gesture_number = gesture_dict.get(gesture_tuple, -1)
        gesture_text = f"Gesture: {hand_gesture} | Number: {gesture_number}"
        cv2.putText(
            image,
            gesture_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        # 發送手勢編號給 Arduino（只在手勢變化且超過0.5秒後發送）
        current_time = time.time()
        if gesture_number != -1 and gesture_number != last_gesture_number and (current_time - last_send_time > send_interval):
            ser.write(f"{gesture_number}\n".encode())  # 發送手勢編號
            print(f"Sent Gesture Number: {gesture_number}")
            last_gesture_number = gesture_number  # 更新最後的手勢編號
            last_send_time = current_time  # 更新上次發送時間

    return image

#開闔
def draw_finger_angle_6_9_10(image, hand):
    global last_send_time, hand_gesture
    
    a = np.array([hand.landmark[6].x, hand.landmark[6].y])
    b = np.array([hand.landmark[9].x, hand.landmark[9].y])
    c = np.array([hand.landmark[10].x, hand.landmark[10].y])
    
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    
    if angle > 180.0:
        angle = 360 - angle

    
    cv2.putText(
        image,
        str(round(angle, 2)),  
        tuple(np.multiply(b, [640, 480]).astype(int)),  
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),  
        2,
        cv2.LINE_AA,
    )

    
    if angle < 35:
        hand_gesture[5] = 1  
    else:
        hand_gesture[5] = 0 
def get_label(index, hand, results):
    output = None
    for idx, classification in enumerate(results.multi_handedness):
        if classification.classification[0].index == index:
            label = classification.classification[0].label
            score = classification.classification[0].score
            text = "{} {}".format(label, round(score, 2))

            coords = tuple(
                np.multiply(
                    np.array(
                        (
                            hand.landmark[mp_hands.HandLandmark.WRIST].x,
                            hand.landmark[mp_hands.HandLandmark.WRIST].y,
                        )
                    ),
                    [960, 650],
                ).astype(int)
            )

            output = text, coords

    return output

cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        ret, frame = cap.read()

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for num, hand in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(
                    image,
                    hand,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(
                        color=(121, 22, 76), thickness=2, circle_radius=4
                    ),
                    mp_drawing.DrawingSpec(
                        color=(250, 44, 250), thickness=2, circle_radius=2
                    ),
                )

                if get_label(num, hand, results):
                    text, coord = get_label(num, hand, results)
                    cv2.putText(
                        image,
                        text,
                        coord,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

                # 顯示角度並更新狀態
                draw_finger_angle_6_9_10(image, hand)

            # 偵測手勢
            image = draw_finger_angles(image, results, joint_list)

        cv2.imshow("Hand Tracking", image)

        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
