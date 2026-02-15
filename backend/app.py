import time
import math
import random
import threading

import cv2
import numpy as np
from flask import Flask, Response, jsonify
from flask_cors import CORS
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────
MODEL_PATH = r'runs\detect\train\weights\best.pt'
VIDEO_PATH = 'dataset/test_video.mov'
CONFIDENCE = 0.15
TARGET_FPS = 25

# Neon palette (BGR) — cyan only, no magenta
NEON_CYAN = (255, 229, 0)
NEON_CYAN_DIM = (180, 160, 0)
NEON_WHITE = (255, 255, 255)

app = Flask(__name__)
CORS(app)

# Load model once at startup
model = YOLO(MODEL_PATH)

# Thread-safe shared detection state
_detections_lock = threading.Lock()
_latest_detections: list[dict] = []


def _set_detections(dets: list[dict]):
    global _latest_detections
    with _detections_lock:
        _latest_detections = dets


def _get_detections() -> list[dict]:
    with _detections_lock:
        return list(_latest_detections)


# ── Neon Drawing Helpers ──────────────────────────────────────

def draw_neon_circle(frame: np.ndarray, cx: int, cy: int, radius: int,
                     label: str, frame_count: int) -> np.ndarray:
    """Draw a glowing neon circle with rotating arcs and particles — cyan only."""
    h, w = frame.shape[:2]

    # Create a glow overlay (black = transparent when added)
    glow = np.zeros_like(frame, dtype=np.uint8)

    # ── 1. Main circle (thick, for glow base) ────────────────
    cv2.circle(glow, (cx, cy), radius, NEON_CYAN, 2, cv2.LINE_AA)
    cv2.circle(glow, (cx, cy), radius + 4, NEON_CYAN_DIM, 1, cv2.LINE_AA)

    # ── 2. Rotating dashed arcs ──────────────────────────────
    rotation_deg = (frame_count * 3) % 360
    arc_radius = radius + 10
    num_arcs = 4
    arc_span = 50

    for i in range(num_arcs):
        start_angle = rotation_deg + i * (360 // num_arcs)
        end_angle = start_angle + arc_span
        cv2.ellipse(glow, (cx, cy), (arc_radius, arc_radius),
                    0, start_angle, end_angle, NEON_CYAN, 2, cv2.LINE_AA)

    # Second ring rotating opposite direction
    rotation_deg2 = (-frame_count * 2) % 360
    arc_radius2 = radius + 18
    for i in range(3):
        start_angle = rotation_deg2 + i * 120
        end_angle = start_angle + 30
        cv2.ellipse(glow, (cx, cy), (arc_radius2, arc_radius2),
                    0, start_angle, end_angle, NEON_CYAN_DIM, 1, cv2.LINE_AA)

    # ── 3. Particles (bright dots around perimeter) ──────────
    num_particles = 12
    for i in range(num_particles):
        angle_deg = (frame_count * (2 + i * 0.3) + i * (360 / num_particles)) % 360
        angle_rad = math.radians(angle_deg)
        pr = radius + random.randint(5, 22)
        px = int(cx + pr * math.cos(angle_rad))
        py = int(cy + pr * math.sin(angle_rad))
        if 0 <= px < w and 0 <= py < h:
            size = random.choice([1, 1, 2])
            cv2.circle(glow, (px, py), size, NEON_WHITE, -1, cv2.LINE_AA)

    # ── 4. Inner shimmer dots ────────────────────────────────
    for i in range(6):
        angle_deg = (frame_count * 4 + i * 60) % 360
        angle_rad = math.radians(angle_deg)
        pr = radius - 5
        px = int(cx + pr * math.cos(angle_rad))
        py = int(cy + pr * math.sin(angle_rad))
        if 0 <= px < w and 0 <= py < h:
            cv2.circle(glow, (px, py), 1, NEON_CYAN, -1, cv2.LINE_AA)

    # ── 5. Apply Gaussian blur to the glow overlay for bloom ─
    glow_blurred = cv2.GaussianBlur(glow, (21, 21), 8)

    # Composite: add the blurred glow, then the sharp glow on top
    frame = cv2.add(frame, glow_blurred)
    frame = cv2.add(frame, glow)

    # ── 6. Label with glow ───────────────────────────────────
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    text_size = cv2.getTextSize(label.upper(), font, font_scale, thickness)[0]
    tx = cx - text_size[0] // 2
    ty = cy - radius - 28

    # Glow behind text
    cv2.putText(frame, label.upper(), (tx, ty), font, font_scale,
                NEON_CYAN, thickness + 3, cv2.LINE_AA)
    # Sharp text
    cv2.putText(frame, label.upper(), (tx, ty), font, font_scale,
                NEON_WHITE, thickness, cv2.LINE_AA)

    return frame


# ── MJPEG Generator ──────────────────────────────────────────

def generate_frames():
    """Yield JPEG frames as multipart MJPEG stream."""
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"ERROR: Could not open {VIDEO_PATH}")
        return

    frame_delay = 1.0 / TARGET_FPS
    frame_count = 0
    vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while True:
        start_time = time.time()

        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = cap.read()
            if not success:
                break

        # Run YOLO detection
        results = model(frame, conf=CONFIDENCE, verbose=False)

        # Collect detections for the API + draw neon effects
        frame_dets: list[dict] = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                cls_id = int(box.cls[0])
                label = model.names[cls_id]

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                radius = max(x2 - x1, y2 - y1) // 2

                frame = draw_neon_circle(frame, cx, cy, radius, label, frame_count)

                # Store normalized coordinates (0-1)
                frame_dets.append({
                    'label': label,
                    'cx': cx / vid_w,
                    'cy': cy / vid_h,
                    'radius': radius / max(vid_w, vid_h),
                    'confidence': float(box.conf[0]),
                })

        _set_detections(frame_dets)
        frame_count += 1

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        elapsed = time.time() - start_time
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()


# ── Routes ────────────────────────────────────────────────────

@app.route('/api/video_feed')
def video_feed():
    """Stream processed video as MJPEG."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/detections')
def detections():
    """Return the latest detection positions as JSON."""
    return jsonify(_get_detections())


# ── Voice / STT+TTS Routes ───────────────────────────────────

# Lazy-init so the server starts even without voice deps
_voice_svc = None


def _get_voice_service():
    global _voice_svc
    if _voice_svc is None:
        from voice_service import VoiceService
        _voice_svc = VoiceService()
    return _voice_svc


@app.route('/api/voice/objects')
def voice_objects():
    """Return unique labels from latest detections (for voice prompt)."""
    dets = _get_detections()
    labels = sorted(set(d['label'] for d in dets))
    return jsonify(labels)


@app.route('/api/voice/start', methods=['POST'])
def voice_start():
    """Step 1: Announce visible objects via TTS and return the prompt text."""
    try:
        svc = _get_voice_service()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    dets = _get_detections()
    visible = sorted(set(d['label'] for d in dets))

    if not visible:
        return jsonify({"prompt": None, "objects": [], "message": "No objects detected."})

    obj_str = ", ".join(visible)
    prompt = f"Scanners active. I see {obj_str}. What is the salvage target?"

    # Speak it (blocking — plays audio then returns)
    try:
        svc.speak(prompt)
    except Exception as e:
        return jsonify({"prompt": prompt, "objects": visible, "tts_error": str(e)})

    return jsonify({"prompt": prompt, "objects": visible})


@app.route('/api/voice/record', methods=['POST'])
def voice_record():
    """Step 2: Record from mic and transcribe via STT."""
    from flask import request
    body = request.get_json(silent=True) or {}
    duration = body.get('duration', 4)

    try:
        svc = _get_voice_service()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    command_text = svc.listen(duration)
    return jsonify({"transcript": command_text or ""})


@app.route('/api/voice/evaluate', methods=['POST'])
def voice_evaluate():
    """Step 3: Evaluate command with Gemini & speak result."""
    from flask import request
    body = request.get_json(silent=True) or {}
    command_text = body.get('command', '')
    visible = body.get('objects', [])

    if not command_text:
        return jsonify({"decision": {"valid": False, "target": None, "reason": "No command."}})

    try:
        svc = _get_voice_service()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    decision = svc.process_command(command_text, visible)

    valid = decision.get("valid", False)
    target = decision.get("target")
    reason = decision.get("reason", "")

    if valid:
        response_text = f"Confirmed. Locking on to target: {target}."
    else:
        response_text = f"Negative. {reason}"

    try:
        svc.speak(response_text)
    except Exception:
        pass

    return jsonify({"decision": decision, "response": response_text})


# ── Main ──────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Starting Scrapple video stream server...")
    print(f"Model: {MODEL_PATH}")
    print(f"Video: {VIDEO_PATH}")
    print(f"Stream at: http://127.0.0.1:5000/api/video_feed")
    print(f"Detections at: http://127.0.0.1:5000/api/detections")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
