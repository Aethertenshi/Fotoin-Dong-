import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components import containers as mp_containers
import threading
import time
import math
import queue
import urllib.request
import os

# ---------------------------------------------------------------------------
# One Euro Filter (per scalar value)
# ---------------------------------------------------------------------------
class _OneEuroFilter:
    def __init__(self, freq=60.0, min_cutoff=1.0, beta=0.05, d_cutoff=1.0):
        self._freq = freq
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev = None
        self._dx_prev = 0.0

    def _alpha(self, cutoff):
        te = 1.0 / self._freq
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def __call__(self, x):
        if self._x_prev is None:
            self._x_prev = x
            return x
        dx = (x - self._x_prev) * self._freq
        dx_hat = self._dx_prev + self._alpha(self._d_cutoff) * (dx - self._dx_prev)
        cutoff = self._min_cutoff + self._beta * abs(dx_hat)
        x_hat = self._x_prev + self._alpha(cutoff) * (x - self._x_prev)
        self._x_prev = x_hat
        self._dx_prev = dx_hat
        return x_hat


# ---------------------------------------------------------------------------
# Per-hand landmark smoother (21 landmarks × 3 axes)
# ---------------------------------------------------------------------------
class _HandSmoother:
    def __init__(self):
        # filters[lm_idx][axis]
        self._filters = [[_OneEuroFilter(freq=60.0, min_cutoff=1.5, beta=0.1)
                          for _ in range(3)] for _ in range(21)]

    def smooth(self, landmarks):
        """landmarks: list of (x, y, z) tuples. Returns smoothed list."""
        out = []
        for i, (x, y, z) in enumerate(landmarks):
            sx = self._filters[i][0](x)
            sy = self._filters[i][1](y)
            sz = self._filters[i][2](z)
            out.append((sx, sy, sz))
        return out


# ---------------------------------------------------------------------------
# GestureManager
# ---------------------------------------------------------------------------
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("[GestureManager] Downloading hand_landmarker.task …")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[GestureManager] Model downloaded.")


class GestureManager:
    def __init__(self):
        self.detected_gesture = None
        self.landmarks = []
        self._running = False
        self._capture_thread = None
        self._detect_thread = None
        self._frame_queue = queue.Queue(maxsize=2)   # Drop stale frames
        self._pinch_cooldown = 0.0
        self._smoothers = [_HandSmoother(), _HandSmoother()]   # one per hand slot
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def start(self):
        _ensure_model()
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._detect_thread  = threading.Thread(target=self._detect_loop,  daemon=True)
        self._capture_thread.start()
        self._detect_thread.start()

    def stop(self):
        self._running = False
        if self._capture_thread:
            self._capture_thread.join()
        if self._detect_thread:
            self._detect_thread.join()

    # ------------------------------------------------------------------
    # Thread 1 — pure capture, no processing
    # ------------------------------------------------------------------
    def _capture_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[GestureManager] Webcam could not be opened.")
            self._running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS,          60)
        cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # Minimise capture latency

        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            # Drop oldest frame if queue is full — we only want fresh frames
            if self._frame_queue.full():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self._frame_queue.put(frame)

        cap.release()

    # ------------------------------------------------------------------
    # Thread 2 — preprocessing + MediaPipe Tasks inference
    # ------------------------------------------------------------------
    def _detect_loop(self):
        base_opts = mp_tasks.BaseOptions(
            model_asset_path=MODEL_PATH,
            delegate=mp_tasks.BaseOptions.Delegate.CPU,   # GPU acceleration
        )
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_opts,
            running_mode=mp_vision.RunningMode.VIDEO,     # Temporal tracking
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        last_time = time.time()
        frame_ts_ms = 0

        with mp_vision.HandLandmarker.create_from_options(options) as landmarker:
            while self._running:
                try:
                    frame = self._frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # --- Preprocessing ---
                frame = cv2.flip(frame, 1)

                # CLAHE on luminance only, then convert to RGB for MediaPipe
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                l, a, b_ch = cv2.split(lab)
                l = clahe.apply(l)
                enhanced_bgr = cv2.cvtColor(cv2.merge([l, a, b_ch]), cv2.COLOR_LAB2BGR)
                rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)

                # Monotonically increasing timestamp (required by VIDEO mode)
                now = time.time()
                dt = now - last_time
                last_time = now
                frame_ts_ms += int(dt * 1000)

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect_for_video(mp_image, frame_ts_ms)

                # --- Gesture logic ---
                current_gesture = None
                current_landmarks = []

                if self._pinch_cooldown > 0:
                    self._pinch_cooldown -= dt

                if result.hand_landmarks:
                    for hi, hand_lms in enumerate(result.hand_landmarks):
                        raw = [(lm.x, lm.y, lm.z) for lm in hand_lms]
                        smoother = self._smoothers[hi] if hi < len(self._smoothers) else _HandSmoother()
                        current_landmarks.append(smoother.smooth(raw))

                    num_hands = len(result.hand_landmarks)

                    # 1. Two-hand photo-frame gesture
                    if num_hands == 2:
                        h1 = result.hand_landmarks[0]
                        h2 = result.hand_landmarks[1]
                        d1 = math.hypot(h1[8].x - h2[4].x, h1[8].y - h2[4].y)
                        d2 = math.hypot(h2[8].x - h1[4].x, h2[8].y - h1[4].y)
                        if d1 < 0.09 and d2 < 0.09:
                            current_gesture = "frame"

                    # 2. Left-hand pinch (cycle background)
                    if not current_gesture and self._pinch_cooldown <= 0:
                        for idx, hand_lms in enumerate(result.hand_landmarks):
                            handedness = result.handedness[idx][0].category_name
                            if handedness == "Right" or hand_lms[9].x < 0.5:
                                dist = math.hypot(
                                    hand_lms[8].x - hand_lms[4].x,
                                    hand_lms[8].y - hand_lms[4].y,
                                )
                                if dist < 0.045:
                                    current_gesture = "pinch"
                                    self._pinch_cooldown = 0.6
                                    break

                    # 3. Fist clench (start/restart)
                    if not current_gesture:
                        for hand_lms in result.hand_landmarks:
                            if (hand_lms[8].y  > hand_lms[6].y  and
                                hand_lms[12].y > hand_lms[10].y and
                                hand_lms[16].y > hand_lms[14].y and
                                hand_lms[20].y > hand_lms[18].y):
                                current_gesture = "fist"
                                break

                with self._lock:
                    self.detected_gesture = current_gesture
                    self.landmarks = current_landmarks

    # ------------------------------------------------------------------
    # Thread-safe accessors for the game loop
    # ------------------------------------------------------------------
    @property
    def gesture(self):
        with self._lock:
            return self.detected_gesture

    @property
    def hand_landmarks(self):
        with self._lock:
            return list(self.landmarks)