"""
Scrapple — Computer Vision Video Service
=========================================
YOLO object detection with neon circle visualization on video stream.

Provides MJPEG streaming with real-time detection overlays.
"""

import time
import math
import random
import threading
from typing import Generator

import cv2
import numpy as np
from ultralytics import YOLO

from config import Config


class CVVideoService:
    """Manages YOLO detection and video streaming with neon effects."""

    def __init__(self):
        self.model_path = Config.CV_MODEL_PATH
        self.video_path = Config.CV_VIDEO_PATH
        self.confidence = Config.CV_CONFIDENCE_THRESHOLD
        self.target_fps = Config.CV_STREAM_FPS
        self.jpeg_quality = Config.CV_JPEG_QUALITY
        
        # Neon palette (BGR) — cyan theme
        self.NEON_CYAN = (255, 229, 0)
        self.NEON_CYAN_DIM = (180, 160, 0)
        self.NEON_WHITE = (255, 255, 255)
        
        # Thread-safe detection state
        self._detections_lock = threading.Lock()
        self._latest_detections: list[dict] = []
        
        # Load model
        print(f"[CV] Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)
        print("[CV] Model loaded successfully")

    def _set_detections(self, dets: list[dict]):
        """Thread-safe setter for detections."""
        with self._detections_lock:
            self._latest_detections = dets

    def get_detections(self) -> list[dict]:
        """Thread-safe getter for detections."""
        with self._detections_lock:
            return list(self._latest_detections)

    def draw_neon_circle(self, frame: np.ndarray, cx: int, cy: int, radius: int,
                         label: str, frame_count: int) -> np.ndarray:
        """Draw a glowing neon circle with rotating arcs and particles."""
        h, w = frame.shape[:2]
        glow = np.zeros_like(frame, dtype=np.uint8)

        # Main circle
        cv2.circle(glow, (cx, cy), radius, self.NEON_CYAN, 2, cv2.LINE_AA)
        cv2.circle(glow, (cx, cy), radius + 4, self.NEON_CYAN_DIM, 1, cv2.LINE_AA)

        # Rotating dashed arcs
        rotation_deg = (frame_count * 3) % 360
        arc_radius = radius + 10
        num_arcs = 4
        arc_span = 50

        for i in range(num_arcs):
            start_angle = rotation_deg + i * (360 // num_arcs)
            end_angle = start_angle + arc_span
            cv2.ellipse(glow, (cx, cy), (arc_radius, arc_radius),
                        0, start_angle, end_angle, self.NEON_CYAN, 2, cv2.LINE_AA)

        # Second ring rotating opposite direction
        rotation_deg2 = (-frame_count * 2) % 360
        arc_radius2 = radius + 18
        for i in range(3):
            start_angle = rotation_deg2 + i * 120
            end_angle = start_angle + 30
            cv2.ellipse(glow, (cx, cy), (arc_radius2, arc_radius2),
                        0, start_angle, end_angle, self.NEON_CYAN_DIM, 1, cv2.LINE_AA)

        # Particles (bright dots around perimeter)
        num_particles = 12
        for i in range(num_particles):
            angle_deg = (frame_count * (2 + i * 0.3) + i * (360 / num_particles)) % 360
            angle_rad = math.radians(angle_deg)
            pr = radius + random.randint(5, 22)
            px = int(cx + pr * math.cos(angle_rad))
            py = int(cy + pr * math.sin(angle_rad))
            if 0 <= px < w and 0 <= py < h:
                size = random.choice([1, 1, 2])
                cv2.circle(glow, (px, py), size, self.NEON_WHITE, -1, cv2.LINE_AA)

        # Inner shimmer dots
        for i in range(6):
            angle_deg = (frame_count * 4 + i * 60) % 360
            angle_rad = math.radians(angle_deg)
            pr = radius - 5
            px = int(cx + pr * math.cos(angle_rad))
            py = int(cy + pr * math.sin(angle_rad))
            if 0 <= px < w and 0 <= py < h:
                cv2.circle(glow, (px, py), 1, self.NEON_CYAN, -1, cv2.LINE_AA)

        # Apply Gaussian blur for bloom effect
        glow_blurred = cv2.GaussianBlur(glow, (21, 21), 8)
        frame = cv2.add(frame, glow_blurred)
        frame = cv2.add(frame, glow)

        # Label with glow
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_size = cv2.getTextSize(label.upper(), font, font_scale, thickness)[0]
        tx = cx - text_size[0] // 2
        ty = cy - radius - 28

        # Glow behind text
        cv2.putText(frame, label.upper(), (tx, ty), font, font_scale,
                    self.NEON_CYAN, thickness + 3, cv2.LINE_AA)
        # Sharp text
        cv2.putText(frame, label.upper(), (tx, ty), font, font_scale,
                    self.NEON_WHITE, thickness, cv2.LINE_AA)

        return frame

    def generate_stream(self) -> Generator[bytes, None, None]:
        """Generate MJPEG stream with YOLO detection and neon effects."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"[CV] ERROR: Could not open {self.video_path}")
            return

        frame_delay = 1.0 / self.target_fps
        frame_count = 0
        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"[CV] Starting video stream: {vid_w}x{vid_h} @ {self.target_fps} fps")

        try:
            while True:
                start_time = time.time()

                success, frame = cap.read()
                if not success:
                    # Loop video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, frame = cap.read()
                    if not success:
                        break

                # Run YOLO detection
                results = self.model(frame, conf=self.confidence, verbose=False)

                # Collect detections and draw neon effects
                frame_dets: list[dict] = []
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id]

                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        radius = max(x2 - x1, y2 - y1) // 2

                        frame = self.draw_neon_circle(frame, cx, cy, radius, label, frame_count)

                        # Store normalized coordinates (0-1)
                        frame_dets.append({
                            'label': label,
                            'cx': cx / vid_w,
                            'cy': cy / vid_h,
                            'radius': radius / max(vid_w, vid_h),
                            'confidence': float(box.conf[0]),
                        })

                self._set_detections(frame_dets)
                frame_count += 1

                # Encode as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Frame rate control
                elapsed = time.time() - start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            print(f"[CV] Stream error: {e}")
        finally:
            cap.release()
            print("[CV] Video stream stopped")


# Singleton instance
cv_video_service = CVVideoService()
