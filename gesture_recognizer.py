# ==============================
# FINAL GESTURE RECOGNIZER - WINDOWS STABLE
# ==============================
# Uses MediaPipe + OpenCV + improved camera opening
# Opens camera reliably when launched from FastAPI/Streamlit
# Supports:
# - Palm Open     → Volume Up
# - Fist          → Volume Down
# - Pinch         → Click
# - Thumbs Up     → Zoom In
# - Thumbs Down   → Zoom Out
# - Circle Gesture→ Open Spotify
# - Swipe Right   → Next Slide
# - Swipe Left    → Previous Slide
# ==============================

import cv2
import mediapipe as mp
import math
import time
import collections
import argparse
from controller import (
    volume_up, volume_down, next_slide, prev_slide,
    do_click, open_spotify, zoom_in, zoom_out
)

# ===== TUNABLE PARAMETERS =====
COOLDOWN = 0.7
SWIPE_THRESHOLD = 120
PINCH_THRESHOLD = 35
CIRCLE_BUFFER = 28
CIRCLE_VARIANCE_THRESHOLD = 0.28
CIRCLE_MIN_RADIUS = 25
THUMB_DIRECTION_MARGIN = 25
CLICK_COOLDOWN = 0.35
# ==============================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
)

# ------------------------------------------
# Utility functions
# ------------------------------------------

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def get_points(landmarks, w, h):
    return [(int(lm.x * w), int(lm.y * h)) for lm in landmarks.landmark]

def finger_states(landmarks, w, h):
    pts = get_points(landmarks, w, h)
    tips = [4,8,12,16,20]
    pips = [3,6,10,14,18]

    fingers = []

    # Thumb: use x-axis
    thumb_ext = abs(pts[tips[0]][0] - pts[pips[0]][0]) > 18
    fingers.append(thumb_ext)

    # Other fingers: tip.y < pip.y
    for i in range(1,5):
        fingers.append(pts[tips[i]][1] < pts[pips[i]][1] - 6)

    return fingers, pts

def is_circle(buf):
    if len(buf) < 12:
        return False

    xs = [p[0] for p in buf]
    ys = [p[1] for p in buf]
    cx = sum(xs)/len(xs)
    cy = sum(ys)/len(ys)
    radii = [math.hypot(x-cx, y-cy) for x,y in buf]

    mean_r = sum(radii)/len(radii)
    if mean_r < CIRCLE_MIN_RADIUS:
        return False

    var = sum((r-mean_r)**2 for r in radii) / len(radii)
    rel_var = math.sqrt(var)/mean_r

    angles = [math.atan2(y-cy, x-cx) for x,y in buf]
    angles.sort()
    span = angles[-1] - angles[0]
    if span < 0:
        span += 2*math.pi

    return rel_var < CIRCLE_VARIANCE_THRESHOLD and span > math.pi


# ------------------------------------------
# MAIN FUNCTION
# ------------------------------------------

def main(device=0, show_preview=True):

    # ===== FIXED CAMERA OPENING FOR WINDOWS =====
    cap = cv2.VideoCapture(device, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] Camera couldn't open with CAP_DSHOW. Trying fallback...")
        cap = cv2.VideoCapture(device)

    if not cap.isOpened():
        print("[FATAL] Camera access failed. Exiting recognizer.")
        return

    print("[INFO] Camera opened successfully.")

    last_action = 0
    last_click = 0
    last_circle = 0
    last_zoom = 0
    prev_index_x = None
    circle_buf = collections.deque(maxlen=CIRCLE_BUFFER)

    print("[INFO] Gesture recognizer running...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Frame capture failed.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        label = None
        now = time.time()

        # ----------------------------
        # DETECTION
        # ----------------------------
        if result.multi_hand_landmarks:
            lm = result.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

            fingers, pts = finger_states(lm, w, h)

            wrist = pts[0]
            index_tip = pts[8]
            thumb_tip = pts[4]

            # ----------------------------
            # 1. VOLUME UP (Palm Open)
            # ----------------------------
            if now - last_action > COOLDOWN and all(fingers):
                volume_up()
                label = "Volume Up (Palm Open)"
                last_action = now

            # ----------------------------
            # 2. VOLUME DOWN (Fist)
            # ----------------------------
            if now - last_action > COOLDOWN and not any(fingers[1:]):
                volume_down()
                label = "Volume Down (Fist)"
                last_action = now

            # ----------------------------
            # 3. PINCH CLICK
            # ----------------------------
            pinch_dist = distance(index_tip, thumb_tip)
            if pinch_dist < PINCH_THRESHOLD and now - last_click > CLICK_COOLDOWN:
                do_click()
                label = "Click (Pinch)"
                last_click = now

            # ----------------------------
            # 4. ZOOM (Thumbs Up / Down)
            # ----------------------------
            thumb_ext = fingers[0]
            others_folded = not fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]

            if thumb_ext and others_folded and now - last_zoom > COOLDOWN:

                # Thumbs Up
                if thumb_tip[1] < wrist[1] - THUMB_DIRECTION_MARGIN:
                    zoom_in()
                    label = "Zoom In (Thumbs Up)"
                    last_zoom = now

                # Thumbs Down
                elif thumb_tip[1] > wrist[1] + THUMB_DIRECTION_MARGIN:
                    zoom_out()
                    label = "Zoom Out (Thumbs Down)"
                    last_zoom = now

            # ----------------------------
            # 5. SWIPE L/R
            # ----------------------------
            index_x = index_tip[0]
            if prev_index_x is not None and now - last_action > COOLDOWN:
                dx = index_x - prev_index_x

                if dx > SWIPE_THRESHOLD:
                    next_slide()
                    label = "Next Slide (Swipe Right)"
                    last_action = now

                elif dx < -SWIPE_THRESHOLD:
                    prev_slide()
                    label = "Previous Slide (Swipe Left)"
                    last_action = now

            prev_index_x = index_x

            # ----------------------------
            # 6. CIRCLE GESTURE
            # ----------------------------
            circle_buf.append(index_tip)

            if len(circle_buf) == CIRCLE_BUFFER and now - last_circle > 1.5:
                if is_circle(circle_buf):
                    open_spotify()
                    label = "Open Spotify (Circle)"
                    last_circle = now
                    circle_buf.clear()

        # ----------------------------
        # UI display
        # ----------------------------
        if label:
            cv2.putText(frame, label, (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 255), 2)

        if show_preview:
            cv2.imshow("Gesture Recognizer - ESC to exit", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                print("[INFO] Exit requested.")
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    main(device=args.device, show_preview=not args.no_preview)
