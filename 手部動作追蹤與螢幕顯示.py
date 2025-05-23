import mediapipe as mp
import cv2
import numpy as np

# 初始化 MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# 定義關節列表：大拇指、食指、中指、無名指、小指
joint_list = [[4, 3, 2], [8, 7, 6], [12, 11, 10], [16, 15, 14], [20, 19, 18]]

def draw_finger_angles(image, results, joint_list):
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
    return image

def draw_finger_angle_6_9_10(image, hand):

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
                    mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2),
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

                draw_finger_angle_6_9_10(image, hand)

            image = draw_finger_angles(image, results, joint_list)

        cv2.imshow("Hand Tracking", image)

        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
