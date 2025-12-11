#!/usr/bin/env python3
"""
3D Cube Control using Hand Gestures.
Uses MediaPipe for hand tracking and OpenGL for 3D rendering.
"""
"""
Real-Time 3D Object Manipulation with Hand Gestures
Using MediaPipe new API (0.10.30+)

Controls:
- Open hand + move left/right → Rotate object on Y-axis
- Open hand + move up/down → Rotate object on X-axis
- Pinch (thumb + index finger) → Zoom in/out
- Close hand or remove hand → Pause interaction
"""

import cv2
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import time
from collections import deque
import urllib.request
import os

# MediaPipe imports (new API)
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


# =============================================================================
# CONFIGURATION
# =============================================================================


class Config:
    WEBCAM_WIDTH = 640
    WEBCAM_HEIGHT = 480
    RENDER_WIDTH = 800
    RENDER_HEIGHT = 600
    ROTATION_SENSITIVITY = 0.3  # degrees per frame
    ZOOM_SENSITIVITY = 0.015
    smoothing_factor_size = 0.4
    ZOOM_MIN = -15.0
    ZOOM_MAX = -2.0
    ZOOM_DEFAULT = -6.0


# =============================================================================
# DOWNLOAD MODEL FILE
# =============================================================================


def download_model():
    """Download the hand landmarker model if not present"""
    model_path = "hand_landmarker.task"
    if not os.path.exists(model_path):
        print("Downloading hand landmark model...")
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        urllib.request.urlretrieve(url, model_path)
        print("Model downloaded!")
    return model_path


# =============================================================================
# HAND TRACKING (New MediaPipe API)
# =============================================================================


class HandTracker:
    """
    MediaPipe hand tracking using new Tasks API

    Key landmarks:
    - 0: Wrist
    - 4: Thumb tip (for pinch)
    - 8: Index finger tip (for pinch)
    - 5, 9, 13, 17: Finger bases (for palm center)
    """

    THUMB_TIP = 4
    INDEX_TIP = 8
    INDEX_PIP = 6
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    RING_TIP = 16
    RING_PIP = 14
    PALM_LANDMARKS = [0, 5, 9, 13, 17]

    def __init__(self):
        model_path = download_model()

        self.frame_width = Config.WEBCAM_WIDTH
        self.frame_height = Config.WEBCAM_HEIGHT

        # Create hand landmarker with VIDEO mode
        # Initialize MediaPipe hand landmarker with real-time detection mode
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.frame_timestamp = 0

    def process_frame(self, frame):
        """Process frame and extract hand landmarks"""
        self.frame_height, self.frame_width = frame.shape[:2]

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Process with timestamp
        self.frame_timestamp += 33  # ~30fps
        results = self.landmarker.detect_for_video(mp_image, self.frame_timestamp)

        landmarks = None

        if results.hand_landmarks and len(results.hand_landmarks) > 0:
            hand_landmarks = results.hand_landmarks[0]

            # Draw landmarks on frame
            self._draw_landmarks(frame, hand_landmarks)

            # Convert to pixel coordinates
            landmarks = {}
            for idx, lm in enumerate(hand_landmarks):
                landmarks[idx] = (
                    lm.x * self.frame_width,
                    lm.y * self.frame_height,
                    lm.z * self.frame_width,
                )

        return frame, landmarks

    def _draw_landmarks(self, frame, hand_landmarks):
        """Draw hand landmarks and connections on frame"""
        h, w = frame.shape[:2]

        # Draw connections
        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),  # Thumb
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),  # Index
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),  # Middle
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),  # Ring
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),  # Pinky
            (5, 9),
            (9, 13),
            (13, 17),  # Palm
        ]

        for start, end in connections:
            x1 = int(hand_landmarks[start].x * w)
            y1 = int(hand_landmarks[start].y * h)
            x2 = int(hand_landmarks[end].x * w)
            y2 = int(hand_landmarks[end].y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 230, 210), 2)

        # Draw landmarks
        for lm in hand_landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            cv2.circle(frame, (x, y), 5, (255, 40, 180), -1)
            cv2.circle(frame, (x, y), 7, (0, 230, 210), 2)

    def get_palm_center(self, landmarks):
        """Calculate palm center from key landmarks"""
        x = np.mean([landmarks[i][0] for i in self.PALM_LANDMARKS])
        y = np.mean([landmarks[i][1] for i in self.PALM_LANDMARKS])
        return np.array([x, y])

    def get_pinch_distance(self, landmarks):
        """Calculate distance between thumb tip and index tip"""
        thumb = np.array([landmarks[self.THUMB_TIP][0], landmarks[self.THUMB_TIP][1]])
        index = np.array([landmarks[self.INDEX_TIP][0], landmarks[self.INDEX_TIP][1]])
        return float(np.linalg.norm(thumb - index))

    def is_hand_open(self, landmarks):
        """Check if hand is open by verifying finger extension"""

        def is_extended(tip, pip):
            return landmarks[tip][1] < landmarks[pip][1] - 10

        index_extended = is_extended(self.INDEX_TIP, self.INDEX_PIP)
        middle_extended = is_extended(self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring_extended = is_extended(self.RING_TIP, self.RING_PIP)

        return index_extended and middle_extended and ring_extended

    def release(self):
        self.landmarker.close()


# =============================================================================
# GESTURE CONTROLLER
# =============================================================================


class GestureController:
    """
    Converts hand movements to 3D transformations

    - Palm moves left/right → Y-axis rotation
    - Palm moves up/down → X-axis rotation
    - Pinch distance change → Zoom
    """

    def __init__(self):
        self.prev_palm = None
        self.prev_pinch = None

        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = Config.ZOOM_DEFAULT

        self.smooth_dx = 0.0
        self.smooth_dy = 0.0
        self.smooth_dz = 0.0

        self.history_x = deque(maxlen=5)
        self.history_y = deque(maxlen=5)

        self.is_active = False
        self.stable_frames = 0

    def update(self, landmarks, hand_tracker):
        """Update rotation and zoom based on hand position"""

        if landmarks is None:
            self._reset()
            return False

        if not hand_tracker.is_hand_open(landmarks):
            self._reset()
            return False

        self.is_active = True
        self.stable_frames += 1

        palm = hand_tracker.get_palm_center(landmarks)
        pinch = hand_tracker.get_pinch_distance(landmarks)

        # Detect open hand (rotate) and pinch (zoom) gestures
        if self.prev_palm is not None and self.stable_frames > 2:
            delta = palm - self.prev_palm
            alpha = Config.smoothing_factor_size

            self.smooth_dx = alpha * delta[0] + (1 - alpha) * self.smooth_dx
            self.smooth_dy = alpha * delta[1] + (1 - alpha) * self.smooth_dy

            self.history_x.append(self.smooth_dx)
            self.history_y.append(self.smooth_dy)

            avg_dx = np.mean(self.history_x)
            avg_dy = np.mean(self.history_y)

            self.rotation_y += avg_dx * Config.ROTATION_SENSITIVITY
            self.rotation_x += avg_dy * Config.ROTATION_SENSITIVITY

            if self.prev_pinch is not None:
                pinch_delta = pinch - self.prev_pinch
                self.smooth_dz = alpha * pinch_delta + (1 - alpha) * self.smooth_dz
                self.zoom += self.smooth_dz * Config.ZOOM_SENSITIVITY
                self.zoom = np.clip(self.zoom, Config.ZOOM_MIN, Config.ZOOM_MAX)

        self.prev_palm = palm.copy()
        self.prev_pinch = pinch

        return True

    def _reset(self):
        self.prev_palm = None
        self.prev_pinch = None
        self.smooth_dx = 0.0
        self.smooth_dy = 0.0
        self.smooth_dz = 0.0
        self.history_x.clear()
        self.history_y.clear()
        self.stable_frames = 0
        self.is_active = False

    def reset_transform(self):
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = Config.ZOOM_DEFAULT
        self._reset()


# =============================================================================
# 3D RENDERER
# =============================================================================


class Renderer3D:
    """OpenGL 3D renderer using Pygame"""

    def __init__(self):
        self.idle_rotation = 0.0

        pygame.init()
        pygame.display.set_caption("3dCubeControl — Hand Gesture")

        self.screen = pygame.display.set_mode(
            (Config.RENDER_WIDTH, Config.RENDER_HEIGHT), DOUBLEBUF | OPENGL
        )

        self._setup_opengl()

    def _setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.2, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

        glLightfv(GL_LIGHT1, GL_POSITION, [-3, 2, -3, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.2, 0.1, 0.4, 1])

        glShadeModel(GL_SMOOTH)
        glClearColor(0.04, 0.04, 0.10, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, Config.RENDER_WIDTH / Config.RENDER_HEIGHT, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_cube(self, size=1.5):
        s = size / 2

        faces = [
            (
                [0, 0, 1],
                [1.0, 0.08, 0.08],
                [[-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]],
            ),
            (
                [0, 0, -1],
                [0.0, 1.0, 0.3],
                [[s, -s, -s], [-s, -s, -s], [-s, s, -s], [s, s, -s]],
            ),
            (
                [0, 1, 0],
                [0.0, 0.5, 1.0],
                [[-s, s, s], [s, s, s], [s, s, -s], [-s, s, -s]],
            ),
            (
                [0, -1, 0],
                [1.0, 0.95, 0.0],
                [[-s, -s, -s], [s, -s, -s], [s, -s, s], [-s, -s, s]],
            ),
            (
                [1, 0, 0],
                [0.8, 0.0, 1.0],
                [[s, -s, s], [s, -s, -s], [s, s, -s], [s, s, s]],
            ),
            (
                [-1, 0, 0],
                [0.0, 1.0, 0.9],
                [[-s, -s, -s], [-s, -s, s], [-s, s, s], [-s, s, -s]],
            ),
        ]

        glBegin(GL_QUADS)
        for normal, color, verts in faces:
            glNormal3fv(normal)
            glColor3fv(color)
            for v in verts:
                glVertex3fv(v)
        glEnd()

        glDisable(GL_LIGHTING)
        glColor3f(0.95, 0.95, 0.95)
        glLineWidth(2.5)

        edges = [
            ((-s, -s, -s), (s, -s, -s)),
            ((s, -s, -s), (s, s, -s)),
            ((s, s, -s), (-s, s, -s)),
            ((-s, s, -s), (-s, -s, -s)),
            ((-s, -s, s), (s, -s, s)),
            ((s, -s, s), (s, s, s)),
            ((s, s, s), (-s, s, s)),
            ((-s, s, s), (-s, -s, s)),
            ((-s, -s, -s), (-s, -s, s)),
            ((s, -s, -s), (s, -s, s)),
            ((s, s, -s), (s, s, s)),
            ((-s, s, -s), (-s, s, s)),
        ]

        glBegin(GL_LINES)
        for v1, v2 in edges:
            glVertex3fv(v1)
            glVertex3fv(v2)
        glEnd()

        glEnable(GL_LIGHTING)

    def draw_grid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.08, 0.18, 0.38)
        glLineWidth(1)

        size, divisions = 10, 10
        step = size / divisions
        half = size / 2

        glBegin(GL_LINES)
        for i in range(divisions + 1):
            p = -half + i * step
            glVertex3f(p, -2, -half)
            glVertex3f(p, -2, half)
            glVertex3f(-half, -2, p)
            glVertex3f(half, -2, p)
        glEnd()

        glEnable(GL_LIGHTING)

    def render(self, rot_x, rot_y, zoom, active):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0, 0, zoom)
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        if not active:
            self.idle_rotation += 0.3
            glRotatef(self.idle_rotation, 0, 1, 0)

        self.draw_grid()
        self.draw_cube()

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return False
        return True

    def cleanup(self):
        pygame.quit()


# =============================================================================
# MAIN APPLICATION
# =============================================================================


class App:
    def __init__(self):
        print("Opening webcam...")
        self.cap = cv2.VideoCapture(0)

        # Wait for camera permission on Mac
        for i in range(10):
            if self.cap.isOpened():
                ret, _ = self.cap.read()
                if ret:
                    break
            print(f"Waiting for camera... ({i+1}/10)")
            time.sleep(1)
            self.cap.release()
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError(
                "Cannot open webcam!\n"
                "Please grant camera permission:\n"
                "  System Preferences > Security & Privacy > Privacy > Camera\n"
                "  Enable access for Terminal/your IDE"
            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.WEBCAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.WEBCAM_HEIGHT)

        print("Webcam opened successfully!")

        print("Initializing hand tracker...")
        self.tracker = HandTracker()
        print("Hand tracker ready!")

        self.gesture = GestureController()
        self.renderer = Renderer3D()

        self.fps_history = deque(maxlen=30)
        self.last_time = time.time()

    def get_fps(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        if dt > 0:
            self.fps_history.append(1 / dt)
        return np.mean(self.fps_history) if self.fps_history else 0

    def draw_hud(self, frame, fps):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        if self.gesture.is_active:
            status, color = "ACTIVE - Move hand", (0, 255, 120)
        else:
            status, color = "PAUSED - Show open hand", (0, 140, 255)

        cv2.putText(frame, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(
            frame,
            f"Rotation: X={self.gesture.rotation_x:.1f} Y={self.gesture.rotation_y:.1f}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Zoom: {self.gesture.zoom:.2f}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        return frame

    def run(self):
        print("\n" + "=" * 50)
        print("  HAND GESTURE 3D CONTROL")
        print("=" * 50)
        print("\nControls:")
        print("  Open hand + move  -> Rotate cube")
        print("  Pinch gesture     -> Zoom in/out")
        print("  Close hand        -> Pause")
        print("  R key             -> Reset view")
        print("  Q key or ESC      -> Quit")
        print("=" * 50 + "\n")

        running = True
        while running:
            fps = self.get_fps()

            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break

            frame = cv2.flip(frame, 1)
            frame, landmarks = self.tracker.process_frame(frame)
            self.gesture.update(landmarks, self.tracker)

            frame = self.draw_hud(frame, fps)
            cv2.imshow("Hand Tracking", frame)

            self.renderer.render(
                self.gesture.rotation_x,
                self.gesture.rotation_y,
                self.gesture.zoom,
                self.gesture.is_active,
            )

            # Handle Pygame events (for 3D window)
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE or event.key == K_q:
                        running = False
                    elif event.key == K_r:
                        self.gesture.reset_transform()
                        print("View reset!")

            # Handle OpenCV events (for webcam window)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # Q or ESC
                running = False
            elif key == ord("r"):
                self.gesture.reset_transform()
                print("View reset!")

        self.cleanup()

    def cleanup(self):
        self.cap.release()
        self.tracker.release()
        self.renderer.cleanup()
        cv2.destroyAllWindows()
        print("\nGoodbye!")


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("[INFO] Starting 3D Cube Control... Press 'q' to quit.")
    try:
        app = App()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
