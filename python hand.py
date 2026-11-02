import cv2
import serial
import time
import numpy as np
from collections import deque
from cvzone.HandTrackingModule import HandDetector


SERIAL_PORT = "COM9"
BAUD_RATE = 115200

CAMERA_INDEX = 0

DETECTION_CONFIDENCE = 0.75
SMOOTHING_FRAMES = 5

SEND_INTERVAL = 0.04

WRIST_ANGLE_RANGE = 35



SERVO_OPEN = {
    "THUMB": 180,
    "INDEX": 0,
    "MIDDLE": 180,
    "RING": 0,
    "PINKY": 180,
    "WRIST": -180      # Full LEFT
}

SERVO_CLOSED = {
    "THUMB": -360,
    "INDEX": 420,
    "MIDDLE": -90,
    "RING": 420,
    "PINKY": -120,
    "WRIST": 360    # Full RIGHT
}


ser = None

try:

    ser = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=0.1,
        write_timeout=0.1
    )

    time.sleep(2)

    print("------------------------------------------")
    print("ESP32 CONNECTED")
    print("PORT:", SERIAL_PORT)
    print("BAUD:", BAUD_RATE)
    print("------------------------------------------")

except Exception as e:

    print("Serial connection failed:")
    print(e)

    print("Running without ESP32.")



cap = cv2.VideoCapture(CAMERA_INDEX)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():

    print("ERROR: Camera could not be opened.")
    exit()



detector = HandDetector(
    detectionCon=DETECTION_CONFIDENCE,
    maxHands=1
)


FINGERS = {

    "THUMB":  [1, 2, 3, 4],

    "INDEX":  [5, 6, 7, 8],

    "MIDDLE": [9, 10, 11, 12],

    "RING":   [13, 14, 15, 16],

    "PINKY":  [17, 18, 19, 20]
}


history = {

    "THUMB": deque(maxlen=SMOOTHING_FRAMES),

    "INDEX": deque(maxlen=SMOOTHING_FRAMES),

    "MIDDLE": deque(maxlen=SMOOTHING_FRAMES),

    "RING": deque(maxlen=SMOOTHING_FRAMES),

    "PINKY": deque(maxlen=SMOOTHING_FRAMES),

    "WRIST": deque(maxlen=SMOOTHING_FRAMES)
}



def calculate_angle(a, b, c):


    a = np.array(a[:2], dtype=float)
    b = np.array(b[:2], dtype=float)
    c = np.array(c[:2], dtype=float)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba == 0 or norm_bc == 0:

        return 180.0

    cosine = np.dot(
        ba,
        bc
    ) / (
        norm_ba * norm_bc
    )

    cosine = np.clip(
        cosine,
        -1.0,
        1.0
    )

    return np.degrees(
        np.arccos(cosine)
    )



def calculate_finger_curl(lmList, finger):

    points = FINGERS[finger]

    p1, p2, p3, p4 = points


    pip_angle = calculate_angle(
        lmList[p1],
        lmList[p2],
        lmList[p3]
    )

    dip_angle = calculate_angle(
        lmList[p2],
        lmList[p3],
        lmList[p4]
    )


    if finger == "THUMB":

        mcp_angle = calculate_angle(
            lmList[0],
            lmList[p2],
            lmList[p3]
        )

    else:

        mcp_angle = calculate_angle(
            lmList[0],
            lmList[p1],
            lmList[p2]
        )


    mcp_bend = 180 - mcp_angle
    pip_bend = 180 - pip_angle
    dip_bend = 180 - dip_angle


    curl = (
        mcp_bend * 0.20 +
        pip_bend * 0.50 +
        dip_bend * 0.30
    )


    curl = np.clip(
        curl,
        0,
        180
    )


    return curl, mcp_angle, pip_angle, dip_angle

def calculate_wrist_angle(lmList):


    wrist = lmList[0]
    middle_mcp = lmList[9]

    dx = middle_mcp[0] - wrist[0]
    dy = middle_mcp[1] - wrist[1]


    angle = np.degrees(
        np.arctan2(dx, -dy)
    )


    angle = np.clip(
        angle,
        -WRIST_ANGLE_RANGE,
        WRIST_ANGLE_RANGE
    )

    angle = (angle / WRIST_ANGLE_RANGE) * 90


    angle = angle + 90

    return angle



def map_to_servo(curl, finger):

    output = np.interp(
        curl,
        [0, 180],
        [
            SERVO_OPEN[finger],
            SERVO_CLOSED[finger]
        ]
    )

    return int(
        np.clip(
            output,
            0,
            180
        )
    )


def smooth_value(finger, value):

    history[finger].append(
        value
    )

    return int(
        round(
            np.mean(
                history[finger]
            )
        )
    )



last_send_time = 0


def send_servos(values):

    global last_send_time

    now = time.time()

    if now - last_send_time < SEND_INTERVAL:

        return

    last_send_time = now


    message = ",".join(
        str(int(x))
        for x in values
    )

    message += "\n"


    if ser and ser.is_open:

        try:

            ser.write(
                message.encode("utf-8")
            )

        except Exception as e:

            print(
                "Serial error:",
                e
            )

# SKELETON


def draw_hand_skeleton(img, lmList):

    connections = [

        # Thumb
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),

        # Index
        (0, 5),
        (5, 6),
        (6, 7),
        (7, 8),

        # Middle
        (0, 9),
        (9, 10),
        (10, 11),
        (11, 12),

        # Ring
        (0, 13),
        (13, 14),
        (14, 15),
        (15, 16),

        # Pinky
        (0, 17),
        (17, 18),
        (18, 19),
        (19, 20),

        # Palm
        (5, 9),
        (9, 13),
        (13, 17)
    ]


    for start, end in connections:

        x1, y1 = lmList[start][0:2]
        x2, y2 = lmList[end][0:2]

        cv2.line(
            img,
            (x1, y1),
            (x2, y2),
            (0, 0, 0),
            2
        )



    for i, point in enumerate(lmList):

        x, y = point[0:2]

        cv2.circle(
            img,
            (x, y),
            5,
            (255, 255, 255),
            -1
        )

        cv2.circle(
            img,
            (x, y),
            6,
            (0, 0, 0),
            1
        )



def draw_information(
    img,
    servo_values,
    joint_data,
    wrist_angle,
    wrist_servo
):

    fingers = [
        "THUMB",
        "INDEX",
        "MIDDLE",
        "RING",
        "PINKY"
    ]


    y = 40


    for i, finger in enumerate(fingers):

        data = joint_data[finger]

        text = (
            f"{finger}: "
            f"MCP {int(data['MCP'])}  "
            f"PIP {int(data['PIP'])}  "
            f"DIP {int(data['DIP'])}  "
            f"SERVO {servo_values[i]}"
        )


        cv2.putText(
            img,
            text,
            (15, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 0),
            2
        )

        y += 30



    wrist_text = (
        f"WRIST L/R: "
        f"ANGLE {int(wrist_angle)}  "
        f"SERVO {wrist_servo}"
    )

    cv2.putText(
        img,
        wrist_text,
        (15, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (0, 255, 255),
        2
    )



print()
print("Starting hand tracking...")
print("Press Q to quit.")
print("Press R to reset smoothing.")
print()


try:

    while True:

        success, img = cap.read()

        if not success:

            continue



        img = cv2.flip(
            img,
            1
        )



        hands, img = detector.findHands(
            img,
            draw=False
        )


        if hands:

            hand = hands[0]

            lmList = hand["lmList"]


            draw_hand_skeleton(
                img,
                lmList
            )


            servo_values = []

            joint_data = {}


            for finger in FINGERS:

                curl, mcp, pip, dip = calculate_finger_curl(
                    lmList,
                    finger
                )

                curl = smooth_value(
                    finger,
                    curl
                )


                servo = map_to_servo(
                    curl,
                    finger
                )


                servo_values.append(
                    servo
                )


                joint_data[finger] = {

                    "MCP": mcp,

                    "PIP": pip,

                    "DIP": dip
                }

            wrist_angle_raw = calculate_wrist_angle(
                lmList
            )

            wrist_angle_smoothed = smooth_value(
                "WRIST",
                wrist_angle_raw
            )

            wrist_servo = map_to_servo(
                wrist_angle_smoothed,
                "WRIST"
            )

            servo_values.append(
                wrist_servo
            )


            send_servos(
                servo_values
            )

            draw_information(
                img,
                servo_values,
                joint_data,
                wrist_angle_smoothed,
                wrist_servo
            )


            cv2.putText(
                img,
                "HAND TRACKING ACTIVE",
                (850, 680),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )


        else:

            cv2.putText(
                img,
                "NO HAND DETECTED",
                (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )


        if ser and ser.is_open:

            status = "ESP32: CONNECTED"

        else:

            status = "ESP32: OFFLINE"


        cv2.putText(
            img,
            status,
            (950, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2
        )


        cv2.imshow(
            "Camera Controlled Robotic Hand",
            img
        )


        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            break


        if key == ord("r"):

            for buffer in history.values():

                buffer.clear()

            print(
                "Smoothing reset."
            )


except KeyboardInterrupt:

    print(
        "\nProgram stopped."
    )


finally:

    cap.release()

    cv2.destroyAllWindows()


    if ser and ser.is_open:

        ser.close()

        print(
            "Serial connection closed."
        )

    print(
        "Program finished."
    )
