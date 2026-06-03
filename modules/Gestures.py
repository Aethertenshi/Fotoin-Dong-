import cv2
import mediapipe as mp
import threading
import time
import math

class GestureManager:
    def __init__(self):
        """
        Manages webcam capture and MediaPipe hand gesture tracking in a background thread
        to maintain a stable and fast Pygame frame rate.
        """
        self.detected_gesture = None
        self.landmarks = []      # List of hand landmark coordinates for visualization
        self._running = False
        self._thread = None
        
        # Swipe movement history
        self._x_history = []
        self._swipe_cooldown = 0.0

    def start(self):
        """Starts the background tracking thread."""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Safely stops the tracking thread and releases webcam resources."""
        self._running = False
        if self._thread:
            self._thread.join()

    def _run(self):
        # Open webcam capture
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Webcam could not be opened.")
            return
            
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        last_time = time.time()
        
        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue
                
            # Mirror the frame so left/right moves match player perspective
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process hand landmarks
            results = hands.process(rgb_frame)
            
            current_gesture = None
            current_landmarks = []
            
            # Reduce cooldown
            now = time.time()
            dt = now - last_time
            last_time = now
            if self._swipe_cooldown > 0:
                self._swipe_cooldown -= dt
                
            if results.multi_hand_landmarks:
                # Store normalized coordinates (0.0 to 1.0)
                for hand_lms in results.multi_hand_landmarks:
                    lms_list = []
                    for lm in hand_lms.landmark:
                        lms_list.append((lm.x, lm.y, lm.z))
                    current_landmarks.append(lms_list)
                
                num_hands = len(results.multi_hand_landmarks)
                
                # 1. Detect Two-Hand Photo Frame Gesture
                if num_hands == 2:
                    hand1_lms = results.multi_hand_landmarks[0].landmark
                    hand2_lms = results.multi_hand_landmarks[1].landmark
                    
                    # Compute cross distances between index tips and thumb tips
                    dist1 = math.hypot(hand1_lms[8].x - hand2_lms[4].x, hand1_lms[8].y - hand2_lms[4].y)
                    dist2 = math.hypot(hand2_lms[8].x - hand1_lms[4].x, hand2_lms[8].y - hand1_lms[4].y)
                    
                    # Standard normalized distance threshold
                    if dist1 < 0.09 and dist2 < 0.09:
                        current_gesture = "frame"
                        
                # 2. Individual Hand Gestures (Fist clench or Air Swipe)
                if not current_gesture:
                    hand_lms = results.multi_hand_landmarks[0].landmark
                    
                    # Track x position of Middle Finger Knuckle (landmark 9) for swiping
                    x_pos = hand_lms[9].x
                    self._x_history.append(x_pos)
                    if len(self._x_history) > 10:
                        self._x_history.pop(0)
                        
                    # Trigger Swipe left or right
                    if len(self._x_history) >= 8 and self._swipe_cooldown <= 0:
                        dx = self._x_history[-1] - self._x_history[0]
                        if abs(dx) > 0.18:
                            if dx > 0:
                                current_gesture = "swipe_right"
                            else:
                                current_gesture = "swipe_left"
                            self._swipe_cooldown = 0.8
                            self._x_history.clear()
                            
                    # Fist clench detection
                    if not current_gesture:
                        # Check if fingers are folded (y of tips is lower than their joints)
                        folded_index = hand_lms[8].y > hand_lms[6].y
                        folded_middle = hand_lms[12].y > hand_lms[10].y
                        folded_ring = hand_lms[16].y > hand_lms[14].y
                        folded_pinky = hand_lms[20].y > hand_lms[18].y
                        
                        if folded_index and folded_middle and folded_ring and folded_pinky:
                            current_gesture = "fist"
            else:
                self._x_history.clear()
                
            self.detected_gesture = current_gesture
            self.landmarks = current_landmarks
            
            # Prevent thread from hogging CPU
            time.sleep(0.01)
            
        cap.release()