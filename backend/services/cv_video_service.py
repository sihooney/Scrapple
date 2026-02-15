"""
Scrapple — Computer Vision Video Service
=========================================
YOLO object detection with neon circle visualization.

Uses physical camera index 2 directly (same as LeRobot "front" camera).
When LeRobot runs, the camera is released and the last frame is frozen.
"""

import time
import threading
from typing import Generator, Optional

import cv2
import numpy as np
from ultralytics import YOLO

from config import Config


class CVVideoService:
    """Manages YOLO detection and video streaming with pause/freeze support."""

    def __init__(self):
        self.model_path = Config.CV_MODEL_PATH
        self.confidence = Config.CV_CONFIDENCE_THRESHOLD
        
        # Camera indices (LeRobot cameras)
        self.camera_index = 2      # Front camera (YOLO detection)
        self.camera_index_2 = 3    # Handeye camera (raw feed)
        
        # Neon palette (BGR)
        self.NEON_CYAN = (255, 229, 0)
        self.NEON_CYAN_DIM = (180, 160, 0)
        self.NEON_WHITE = (255, 255, 255)
        self.NEON_RED = (0, 0, 255)
        
        # Thread-safe detection state
        self._detections_lock = threading.Lock()
        self._latest_detections: list[dict] = []
        
        # Pause/freeze state (shared for both cameras)
        self._paused = False
        self._pause_lock = threading.Lock()
        self._frozen_frame: Optional[np.ndarray] = None
        self._frozen_frame_2: Optional[np.ndarray] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._cap_2: Optional[cv2.VideoCapture] = None
        
        # Load YOLO model
        print(f"[CV] Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)
        print("[CV] Model loaded successfully")
        print(f"[CV] Front Camera: index {self.camera_index}")
        print(f"[CV] Handeye Camera: index {self.camera_index_2}")

    def _set_detections(self, dets: list[dict]):
        """Thread-safe setter for detections."""
        with self._detections_lock:
            self._latest_detections = dets

    def get_detections(self) -> list[dict]:
        """Thread-safe getter for detections."""
        with self._detections_lock:
            return list(self._latest_detections)

    def is_paused(self) -> bool:
        """Check if video is paused."""
        with self._pause_lock:
            return self._paused

    def pause(self) -> bool:
        """
        Pause video and release both cameras for LeRobot.
        Returns True if successfully paused.
        """
        with self._pause_lock:
            if self._paused:
                return True  # Already paused
            
            self._paused = True
            print("[CV] ⏸ Video PAUSED - releasing cameras for LeRobot")
            
            # Release camera 2 (front)
            if self._cap is not None:
                try:
                    self._cap.release()
                    print(f"[CV] Camera {self.camera_index} released")
                except:
                    pass
                self._cap = None
            
            # Release camera 3 (handeye)
            if self._cap_2 is not None:
                try:
                    self._cap_2.release()
                    print(f"[CV] Camera {self.camera_index_2} released")
                except:
                    pass
                self._cap_2 = None
            
            return True

    def resume(self) -> bool:
        """
        Resume video after LeRobot finishes.
        Returns True if successfully resumed.
        """
        with self._pause_lock:
            if not self._paused:
                return True  # Already running
            
            self._paused = False
            self._frozen_frame = None
            print("[CV] ▶ Video RESUMED")
            return True

    def draw_neon_circle(self, frame: np.ndarray, cx: int, cy: int, radius: int,
                         label: str, frame_count: int) -> np.ndarray:
        """Draw a simple neon circle (optimized - no blur)."""
        cv2.circle(frame, (cx, cy), radius, self.NEON_CYAN, 2, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), radius + 3, self.NEON_CYAN_DIM, 1, cv2.LINE_AA)

        # Rotating arc
        rotation_deg = (frame_count * 3) % 360
        arc_radius = radius + 8
        cv2.ellipse(frame, (cx, cy), (arc_radius, arc_radius),
                    0, rotation_deg, rotation_deg + 60, self.NEON_CYAN, 2, cv2.LINE_AA)

        # Label
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(label.upper(), font, 0.5, 1)[0]
        tx = cx - text_size[0] // 2
        ty = cy - radius - 15
        cv2.putText(frame, label.upper(), (tx, ty), font, 0.5, self.NEON_WHITE, 1, cv2.LINE_AA)

        return frame

    def _draw_paused_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw a 'PAUSED - LEROBOT ACTIVE' overlay on frozen frame."""
        overlay = frame.copy()
        
        # Darken the frame
        overlay = cv2.addWeighted(overlay, 0.5, np.zeros_like(overlay), 0.5, 0)
        
        # Draw border
        cv2.rectangle(overlay, (5, 5), (635, 475), self.NEON_RED, 3)
        
        # Draw text
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        text1 = "PAUSED"
        text_size1 = cv2.getTextSize(text1, font, 1.5, 3)[0]
        tx1 = (640 - text_size1[0]) // 2
        cv2.putText(overlay, text1, (tx1, 200), font, 1.5, self.NEON_RED, 3, cv2.LINE_AA)
        
        text2 = "LEROBOT ACTIVE"
        text_size2 = cv2.getTextSize(text2, font, 0.8, 2)[0]
        tx2 = (640 - text_size2[0]) // 2
        cv2.putText(overlay, text2, (tx2, 260), font, 0.8, self.NEON_CYAN, 2, cv2.LINE_AA)
        
        text3 = "Camera released to robot"
        text_size3 = cv2.getTextSize(text3, font, 0.5, 1)[0]
        tx3 = (640 - text_size3[0]) // 2
        cv2.putText(overlay, text3, (tx3, 320), font, 0.5, self.NEON_WHITE, 1, cv2.LINE_AA)
        
        return overlay

    def generate_stream(self) -> Generator[bytes, None, None]:
        """Generate MJPEG stream with YOLO detection. Supports pause/freeze."""
        print(f"[CV] Opening camera {self.camera_index}...")
        
        # Performance settings
        target_fps = 10
        frame_delay = 1.0 / target_fps
        yolo_interval = 3  # Run YOLO every 3rd frame
        
        frame_count = 0
        cached_detections: list[dict] = []
        consecutive_failures = 0
        
        while True:
            # Check if paused
            if self.is_paused():
                # Show frozen frame with overlay
                if self._frozen_frame is not None:
                    paused_frame = self._draw_paused_overlay(self._frozen_frame)
                else:
                    paused_frame = self._create_error_frame("PAUSED - LEROBOT ACTIVE")
                
                _, buffer = cv2.imencode('.jpg', paused_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.5)  # Slow updates while paused
                continue
            
            # Open camera if needed
            if self._cap is None or not self._cap.isOpened():
                self._cap = cv2.VideoCapture(self.camera_index)
                
                if not self._cap.isOpened():
                    print(f"[CV] ERROR: Could not open camera {self.camera_index}")
                    error_frame = self._create_error_frame(f"CAMERA {self.camera_index} NOT FOUND")
                    _, buffer = cv2.imencode('.jpg', error_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(1.0)
                    continue
                
                # Camera settings
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                vid_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                vid_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"[CV] Camera opened: {vid_w}x{vid_h} @ {target_fps} fps")
            
            start_time = time.time()
            
            success, frame = self._cap.read()
            if not success:
                consecutive_failures += 1
                if consecutive_failures >= 30:
                    error_frame = self._create_error_frame("CAMERA FEED LOST")
                    _, buffer = cv2.imencode('.jpg', error_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(1.0)
                    consecutive_failures = 0
                    # Try reopening
                    self._cap.release()
                    self._cap = None
                else:
                    time.sleep(0.05)
                continue
            
            consecutive_failures = 0
            
            # Save frame for potential freeze
            self._frozen_frame = frame.copy()
            
            vid_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            vid_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

            # Run YOLO every N frames
            if frame_count % yolo_interval == 0:
                results = self.model(frame, conf=self.confidence, verbose=False)
                
                cached_detections = []
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id]
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        radius = max(x2 - x1, y2 - y1) // 2
                        
                        cached_detections.append({
                            'label': label,
                            'cx': cx / vid_w,
                            'cy': cy / vid_h,
                            'cx_px': cx,
                            'cy_px': cy,
                            'radius': radius / max(vid_w, vid_h),
                            'radius_px': radius,
                            'confidence': float(box.conf[0]),
                        })
                
                self._set_detections(cached_detections)

            # Draw detections
            for det in cached_detections:
                frame = self.draw_neon_circle(
                    frame, det['cx_px'], det['cy_px'], 
                    det['radius_px'], det['label'], frame_count
                )

            frame_count += 1

            # Encode JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            # Frame rate control
            elapsed = time.time() - start_time
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)

    def generate_stream_handeye(self) -> Generator[bytes, None, None]:
        """Generate MJPEG stream from camera 3 (handeye). Raw feed, no YOLO."""
        print(f"[CV] Opening handeye camera {self.camera_index_2}...")
        
        target_fps = 15
        frame_delay = 1.0 / target_fps
        frame_count = 0
        consecutive_failures = 0
        
        while True:
            # Check if paused
            if self.is_paused():
                if self._frozen_frame_2 is not None:
                    paused_frame = self._draw_paused_overlay(self._frozen_frame_2)
                else:
                    paused_frame = self._create_error_frame("PAUSED - LEROBOT ACTIVE")
                
                _, buffer = cv2.imencode('.jpg', paused_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.5)
                continue
            
            # Open camera if needed
            if self._cap_2 is None or not self._cap_2.isOpened():
                self._cap_2 = cv2.VideoCapture(self.camera_index_2)
                
                if not self._cap_2.isOpened():
                    print(f"[CV] ERROR: Could not open handeye camera {self.camera_index_2}")
                    error_frame = self._create_error_frame(f"CAMERA {self.camera_index_2} NOT FOUND")
                    _, buffer = cv2.imencode('.jpg', error_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(1.0)
                    continue
                
                self._cap_2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self._cap_2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self._cap_2.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                vid_w = int(self._cap_2.get(cv2.CAP_PROP_FRAME_WIDTH))
                vid_h = int(self._cap_2.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"[CV] Handeye camera opened: {vid_w}x{vid_h} @ {target_fps} fps")
            
            start_time = time.time()
            
            success, frame = self._cap_2.read()
            if not success:
                consecutive_failures += 1
                if consecutive_failures >= 30:
                    error_frame = self._create_error_frame("HANDEYE FEED LOST")
                    _, buffer = cv2.imencode('.jpg', error_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(1.0)
                    consecutive_failures = 0
                    self._cap_2.release()
                    self._cap_2 = None
                else:
                    time.sleep(0.05)
                continue
            
            consecutive_failures = 0
            self._frozen_frame_2 = frame.copy()
            
            # Draw simple border overlay (no YOLO)
            cv2.rectangle(frame, (2, 2), (637, 477), self.NEON_CYAN_DIM, 1)
            
            # Label
            cv2.putText(frame, "HANDEYE", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, self.NEON_CYAN, 1, cv2.LINE_AA)
            
            frame_count += 1
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            elapsed = time.time() - start_time
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)

    def _create_error_frame(self, message: str) -> np.ndarray:
        """Create an error frame with a message."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(message, font, 0.8, 2)[0]
        tx = (640 - text_size[0]) // 2
        ty = (480 + text_size[1]) // 2
        
        cv2.putText(frame, message, (tx, ty), font, 0.8, self.NEON_CYAN, 2, cv2.LINE_AA)
        cv2.rectangle(frame, (10, 10), (630, 470), self.NEON_CYAN_DIM, 2)
        
        return frame


# Singleton instance
cv_video_service = CVVideoService()
