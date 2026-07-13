"""
Finger Addition — show fingers on both hands and it adds them live.

Left hand  -> first number  (0-5, count of raised fingers)
Right hand -> second number (0-5, count of raised fingers)
Displays: left + right = total   (total can be 0-10)

Keys: q = quit

Requires: opencv-python, mediapipe, numpy (see requirements.txt)
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"

# Landmark indices for each fingertip and the knuckle just below it (PIP joint).
# MediaPipe numbers each hand's 21 points the same way every time.
FINGER_TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
FINGER_PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
THUMB_TIP, THUMB_IP = 4, 3

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]


def draw_landmarks(frame, hand_landmarks, width, height):
    """Draw hand landmarks and skeleton connections."""
    for start_idx, end_idx in HAND_CONNECTIONS:
        pt1 = hand_landmarks[start_idx]
        pt2 = hand_landmarks[end_idx]
        x1, y1 = int(pt1.x * width), int(pt1.y * height)
        x2, y2 = int(pt2.x * width), int(pt2.y * height)
        cv2.line(frame, (x1, y1), (x2, y2), (224, 224, 224), 2)
    for lm in hand_landmarks:
        x, y = int(lm.x * width), int(lm.y * height)
        cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)


def count_fingers(landmarks, handedness_label):
    """Return how many fingers are raised (0-5) for one detected hand."""
    up = 0

    # Four main fingers: "up" if the fingertip sits higher on screen
    # (smaller y value) than its own middle knuckle.
    for name in FINGER_TIPS:
        tip_y = landmarks[FINGER_TIPS[name]].y
        pip_y = landmarks[FINGER_PIPS[name]].y
        if tip_y < pip_y - 0.02:  # small margin avoids flicker right at the edge
            up += 1

    # Thumb moves sideways, not up-down, so compare x instead of y.
    # Which side counts as "extended" depends on which hand it is, since
    # the frame is mirrored for a natural selfie-view.
    thumb_tip_x = landmarks[THUMB_TIP].x
    thumb_ip_x = landmarks[THUMB_IP].x
    if handedness_label == "Right":
        thumb_up = thumb_tip_x > thumb_ip_x + 0.02
    else:
        thumb_up = thumb_tip_x < thumb_ip_x - 0.02
    if thumb_up:
        up += 1

    return up


def open_camera(preferred=0, max_index=4, width=960, height=540):
    """Try the preferred camera index first, then scan a few others."""
    tried = [preferred] + [i for i in range(max_index + 1) if i != preferred]
    for i in tried:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ok, frame = cap.read()
            if ok and frame is not None:
                if i != preferred:
                    print(f"Camera index {preferred} unavailable — using index {i} instead.")
                return cap
            cap.release()
    return None


def main():
    cap = open_camera(0, width=960, height=540)
    if cap is None:
        raise SystemExit(
            "Could not open any webcam (tried indices 0-4).\n"
            "  - Check your camera isn't in use by another app\n"
            "  - On Windows, check Settings > Privacy > Camera access is allowed"
        )

    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    with vision.HandLandmarker.create_from_options(options) as detector:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)  # mirror, so it feels natural
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)
            results = detector.detect_for_video(mp_image, timestamp_ms)

            left_count, right_count = None, None

            if results.hand_landmarks and results.handedness:
                # Pair wrist X-coordinate, finger count, and landmarks
                detected_hands = []
                for lm, handedness in zip(results.hand_landmarks, results.handedness):
                    label = handedness[0].category_name  # "Left" or "Right" (anatomical)
                    n = count_fingers(lm, label)
                    wrist_x = lm[0].x
                    detected_hands.append((wrist_x, n, lm))
                
                # Sort hands by screen position (left-to-right)
                detected_hands.sort(key=lambda item: item[0])
                
                if len(detected_hands) == 1:
                    # One hand on screen: determine side by center line
                    wrist_x, n, lm = detected_hands[0]
                    if wrist_x < 0.5:
                        left_count = n
                    else:
                        right_count = n
                    draw_landmarks(frame, lm, w, h)
                elif len(detected_hands) >= 2:
                    # Two hands: leftmost is 1st number, rightmost is 2nd number
                    left_count = detected_hands[0][1]
                    right_count = detected_hands[1][1]
                    draw_landmarks(frame, detected_hands[0][2], w, h)
                    draw_landmarks(frame, detected_hands[1][2], w, h)

            a = left_count if left_count is not None else 0
            b = right_count if right_count is not None else 0
            total = a + b

            # --- overlay ---
            cv2.rectangle(frame, (0, 0), (w, 90), (20, 20, 20), -1)

            left_txt = str(left_count) if left_count is not None else "-"
            right_txt = str(right_count) if right_count is not None else "-"
            eq = f"{left_txt} + {right_txt} = {total}"
            cv2.putText(frame, eq, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                        (255, 255, 255), 3, cv2.LINE_AA)

            cv2.putText(frame, "Left hand = 1st number | Right hand = 2nd number | q = quit",
                        (20, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

            cv2.imshow("Finger Addition", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()