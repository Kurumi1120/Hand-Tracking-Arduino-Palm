import itertools
import serial
import time
import numpy as np
# 初始化
ser = serial.Serial('COM3', 9600)

gesture_combinations = list(itertools.product([0, 1], repeat=6))
gesture_dict = {tuple(gesture): i + 1 for i, gesture in enumerate(gesture_combinations)}

current_locations = [[0], [0], [0], [0], [0], [0]]  
hand_gesture = [0, 0, 0, 0, 0, 0]  
last_gesture_number = -1
last_send_time = 0
send_interval = 0.5  # 傳送間隔 0.5 秒

# 定義關節
joint_list = [[4, 3, 2], [8, 7, 6], [12, 11, 10], [16, 15, 14], [20, 19, 18]]

# 處理關節角度並更新手勢狀態
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

# 定義每個手指的關節與參數
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

# 處理手指角度並傳送手勢編號
def process_finger_angles(results):
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
            # 更新手指狀態
            process_all_joints(joint, angle)
   
        a = np.array([hand.landmark[6].x, hand.landmark[6].y])
        b = np.array([hand.landmark[9].x, hand.landmark[9].y])
        c = np.array([hand.landmark[10].x, hand.landmark[10].y])
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        if angle < 35:
            hand_gesture[5] = 1
        else:
            hand_gesture[5] = 0

        # 將手勢轉為編號並傳送
        gesture_tuple = tuple(hand_gesture)
        gesture_number = gesture_dict.get(gesture_tuple, -1)

        current_time = time.time()
        if gesture_number != -1 and gesture_number != last_gesture_number and (current_time - last_send_time > send_interval):
.Concurrent            ser.write(f"{gesture_number}\n".encode())
            print(f"Sent Gesture Number: {gesture_number}")
            last_gesture_number = gesture_number
            last_send_time = current_time
