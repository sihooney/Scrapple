# Scrapple — System Architecture for LeRobot Integration

## Mission Statement

Scrapple is the perception, cognition, and UI layer for a salvage robot demo. The system provides:
1. **Computer Vision** — YOLO-based object detection (demonstration feature)
2. **Voice Interface** — Natural language command validation via Gemini + ElevenLabs TTS
3. **LeRobot Control Interface** — API and bridge layer for robotic arm integration

**Primary Goal**: Enable LeRobot arm to pick objects based on validated voice commands.

---

## System State Machine (A→E Flow)

The core demo follows a deterministic state machine:

```
A. RECEIVE visible_objects from CV pipeline or config
B. ANNOUNCE objects via TTS: "Scanners active. I see [objects]. What is the salvage target?"
C. RECORD operator audio (sounddevice/pyaudio) or text fallback
D. VALIDATE command via Gemini against visible_objects list
E. RESPOND via TTS + trigger LeRobot bridge if valid
```

**Critical Path**: `POST /api/voice/listen` → VoiceService → Gemini validation → `run_lerobot_commands(target)`

---

## Architecture Overview

### Backend (Flask on port 5000)

**Entry Point**: `backend/app.py`
- Initializes Flask app with CORS
- Registers 5 route modules (status, voice, demo, arm, video)
- Maintains global_state dict: `{visible_objects, last_command, last_decision, demo_running}`
- Initializes VoiceService singleton

**Services** (`backend/services/`):
1. **VoiceService** (`voice_service.py`)
   - Audio recording: sounddevice (preferred) → pyaudio (fallback) → text input (console)
   - STT: Google Web Speech (free, via SpeechRecognition library)
   - Validation: Gemini 2.0 Flash with strict JSON schema
   - TTS: ElevenLabs "George" voice (deep, cinematic)
   - Returns: `{valid: bool, target: str|null, reason: str}`

2. **CVVideoService** (`cv_video_service.py`)
   - Loads YOLO11n from `runs/detect/train/weights/best.pt`
   - Processes `dataset/test_video.mov` with real-time detection
   - Streams MJPEG at 20 FPS with neon circle overlays
   - Thread-safe detection state for frontend polling
   - Detects: hotdog, skull, nut, gear, heart (5 classes)

3. **LeRobot Bridge** (`lerobot_bridge.py`)
   - **CURRENT**: Placeholder logging function
   - **INTEGRATION POINT**: Replace `run_lerobot_commands(target: str)` with actual control logic
   - Called automatically after valid voice decision in `routes/voice.py`

**Routes** (`backend/routes/`):
- `voice.py`: POST /api/voice/listen — Full voice cycle
- `arm.py`: GET /api/arm/next — Returns last valid target for polling
- `status.py`: GET /api/status — System state snapshot
- `demo.py`: POST /api/demo/start|stop — Demo loop signals
- `video.py`: GET /api/video/feed, GET /api/detections — CV streaming

**Configuration** (`backend/config.py`):
- All tunable constants in one place
- Environment variables: GEMINI_API_KEY, ELEVEN_API_KEY, SECRET_KEY, FLASK_ENV
- Object list: DEFAULT_VISIBLE_OBJECTS = ["hotdog", "skull", "nut", "gear", "heart"]
- Audio: 16kHz, mono, 4s default listen window
- CV: Model paths, confidence threshold (0.5), FPS (20), JPEG quality (85)

### Frontend (React + Vite + Tailwind)

**Entry Point**: `frontend/src/App.tsx`
- Manages demo state: logs, demoRunning
- Handles voice cycle: POST /api/voice/listen → parse response → update logs
- Layout: Left column (controls + status) | Right column (videos + terminal)

**Components** (`frontend/src/components/`):
1. **GridCanvas** — 60fps animated background (z-index: 0)
2. **HudHeader/HudFooter** — Fixed overlays with title, status, clock (z-index: 2)
3. **CVVideoStream** — MJPEG display with detection hover cards, neon effects
4. **VideoDisplay** — Browser webcam feed (getUserMedia) for demonstration
5. **SystemLog** — Terminal-style log (newest first, color-coded)
6. **Demo Control Panel** — RUN ONCE button
7. **System Status Panel** — Voice/Vision/Arm/Network indicators

**Layout**:
- Left: 320px column with control panels
- Right: Video streams (420px tall, side-by-side grid) + System Log (flex-1)
- Cyberpunk aesthetic: cyan (#00e5ff), Orbitron + Share Tech Mono fonts

---

## API Contract for LeRobot Integration

### Primary Endpoint: POST /api/voice/listen

**Purpose**: Execute full voice command cycle and return validated target.

**Request**:
```json
{
  "duration": 4  // Optional: seconds to listen (default from config)
}
```

**Response**:
```json
{
  "command": "pick the skull",
  "decision": {
    "valid": true,
    "target": "skull",
    "reason": "Valid object from visible list"
  },
  "prompt_spoken": "Scanners active. I see hotdog, skull, nut, gear, heart. What is the salvage target?",
  "tts_result": "Confirmed. Locking on to target: skull."
}
```

**Behavior**:
- If `decision.valid === true`, backend automatically calls `run_lerobot_commands(decision.target)`
- Frontend logs show: `🤖 LeRobot: pick "skull"`
- RL team can extend `lerobot_bridge.py` to execute actual arm commands

### Polling Endpoint: GET /api/arm/next

**Purpose**: Allow RL pipeline to poll for latest valid target.

**Response**:
```json
{
  "target": "skull"  // or null if no valid decision yet
}
```

**Use Case**: RL team can poll this endpoint instead of listening to voice endpoint directly.

### Status Endpoint: GET /api/status

**Purpose**: Monitor system state.

**Response**:
```json
{
  "status": "online",
  "state": {
    "visible_objects": ["hotdog", "skull", "nut", "gear", "heart"],
    "last_command": "pick the skull",
    "last_decision": {
      "valid": true,
      "target": "skull",
      "reason": "Valid object from visible list"
    },
    "demo_running": false
  }
}
```

### CV Endpoints (Demonstration Feature)

**GET /api/video/feed**:
- Returns: MJPEG stream (multipart/x-mixed-replace)
- Content: Test video with YOLO detection overlays
- Purpose: Visual demonstration of object detection

**GET /api/detections**:
- Returns: JSON array of current detections
- Format: `[{label, cx, cy, radius, confidence}, ...]` (normalized 0-1 coords)
- Purpose: Frontend hover card positioning

---

## LeRobot Integration Strategies

### Strategy 1: Direct Bridge Extension (Recommended for Simple Control)

**Location**: `backend/services/lerobot_bridge.py`

**Current Code**:
```python
def run_lerobot_commands(target: str) -> None:
    if not target:
        return
    msg = f"LeRobot: pick target = {target!r}"
    print(f"\n[LEROBOT] {msg}")
    # TODO: RL team can add actual LeRobot API or subprocess calls here.
```

**Extension Options**:
1. **Subprocess**: Call LeRobot CLI commands
   ```python
   import subprocess
   subprocess.run(["lerobot", "pick", target], check=True)
   ```

2. **Python API**: Import LeRobot library directly
   ```python
   from lerobot import RobotController
   robot = RobotController()
   robot.pick_object(target)
   ```

3. **HTTP API**: Call LeRobot REST endpoint
   ```python
   import requests
   requests.post("http://lerobot:8080/pick", json={"target": target})
   ```

4. **ROS Integration**: Publish to ROS topic
   ```python
   import rospy
   from std_msgs.msg import String
   pub = rospy.Publisher('/pick_target', String, queue_size=10)
   pub.publish(target)
   ```

**Advantages**: Minimal code changes, automatic triggering after voice validation.

### Strategy 2: Polling Architecture (Recommended for Decoupled Systems)

**Approach**: RL team runs separate process that polls `/api/arm/next`.

**Implementation**:
```python
# lerobot_poller.py
import time
import requests

while True:
    response = requests.get("http://localhost:5000/api/arm/next")
    data = response.json()
    
    if data["target"]:
        print(f"New target: {data['target']}")
        # Execute pick command
        robot.pick_object(data["target"])
        # Clear target by calling voice endpoint again or waiting for next command
    
    time.sleep(0.5)  # Poll every 500ms
```

**Advantages**: Decouples RL pipeline from Flask backend, easier debugging, can run on separate device.

### Strategy 3: New API Endpoint (Recommended for Complex Control)

**Approach**: Add new endpoint for direct arm control with position/trajectory data.

**Implementation**:
```python
# backend/routes/arm.py
@app.route('/api/arm/execute', methods=['POST'])
def arm_execute():
    """
    Execute arm movement with detailed control.
    Request: {
        "target": "skull",
        "position": {"x": 0.5, "y": 0.3, "z": 0.2},
        "approach": "top",
        "speed": 0.5
    }
    """
    data = request.json
    # Call LeRobot with detailed parameters
    result = lerobot_controller.execute_pick(
        target=data["target"],
        position=data.get("position"),
        approach=data.get("approach", "top"),
        speed=data.get("speed", 0.5)
    )
    return jsonify({"success": True, "result": result})
```

**Advantages**: Full control over arm parameters, supports complex trajectories, can integrate CV coordinates.

### Strategy 4: CV-Guided Picking (Future Enhancement)

**Approach**: Use CV detection coordinates to guide arm positioning.

**Data Flow**:
1. Voice command validates target: "pick the skull"
2. Backend queries `/api/detections` for skull coordinates
3. Converts normalized coords (0-1) to real-world coordinates
4. Passes position data to LeRobot: `pick_object("skull", x=0.5, y=0.3, z=0.2)`

**Implementation**:
```python
# backend/services/lerobot_bridge.py
from services.cv_video_service import cv_video_service

def run_lerobot_commands(target: str) -> None:
    # Get current detections
    detections = cv_video_service.get_detections()
    
    # Find target in detections
    target_det = next((d for d in detections if d["label"] == target), None)
    
    if target_det:
        # Convert normalized coords to real-world
        x, y, z = convert_to_world_coords(target_det["cx"], target_det["cy"])
        robot.pick_object(target, position=(x, y, z))
    else:
        # Fallback: pick without position data
        robot.pick_object(target)
```

**Advantages**: Precise positioning, leverages existing CV pipeline, more robust picking.

---

## Camera Integration Options

### Current State
- **CVVideoStream**: Displays test video with YOLO detection (demonstration only)
- **VideoDisplay**: Browser webcam via getUserMedia (placeholder for LeRobot camera)
- **CameraFeed.tsx**: Unused placeholder component with "NO SIGNAL"

### Option 1: Replace VideoDisplay with LeRobot Camera Stream

**Approach**: Stream LeRobot camera feed to frontend.

**Backend**:
```python
# backend/routes/video.py
@app.route('/api/lerobot/camera', methods=['GET'])
def lerobot_camera():
    """Stream LeRobot camera as MJPEG."""
    def generate():
        camera = LeRobotCamera()
        while True:
            frame = camera.read()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
```

**Frontend**:
```tsx
// Replace VideoDisplay.tsx img src
<img src="http://localhost:5000/api/lerobot/camera" alt="LeRobot camera" />
```

### Option 2: Run YOLO on LeRobot Camera Feed

**Approach**: Replace test video with live camera in CVVideoService.

**Implementation**:
```python
# backend/services/cv_video_service.py
def __init__(self):
    # Replace VideoCapture with camera
    self.cap = cv2.VideoCapture(0)  # or LeRobot camera device
    # Rest of initialization unchanged
```

**Advantages**: Real-time detection on actual workspace, no test video needed.

### Option 3: Dual Camera Setup

**Approach**: Keep both CV demo and LeRobot camera.

**Layout**: Three video panels (CV demo | LeRobot camera | Webcam) or replace webcam with LeRobot.

---

## Configuration Management

### Environment Variables (.env file)
```bash
# Required
GEMINI_API_KEY=your_gemini_key_here
ELEVEN_API_KEY=your_elevenlabs_key_here

# Optional
SECRET_KEY=your_flask_secret
FLASK_ENV=development  # or production

# LeRobot (add as needed)
LEROBOT_API_URL=http://localhost:8080
LEROBOT_DEVICE=/dev/ttyUSB0
LEROBOT_CAMERA_INDEX=0
```

### Config Extension for LeRobot
```python
# backend/config.py
class Config:
    # ... existing config ...
    
    # ── LeRobot ─────────────────────────────────────────────────────────
    LEROBOT_API_URL: str = os.getenv('LEROBOT_API_URL', 'http://localhost:8080')
    LEROBOT_DEVICE: str = os.getenv('LEROBOT_DEVICE', '/dev/ttyUSB0')
    LEROBOT_CAMERA_INDEX: int = int(os.getenv('LEROBOT_CAMERA_INDEX', '0'))
    LEROBOT_PICK_SPEED: float = 0.5
    LEROBOT_APPROACH_HEIGHT: float = 0.3  # meters above object
```

---

## Data Structures

### Voice Decision Schema
```python
{
    "valid": bool,        # True if command matches visible_objects
    "target": str | None, # Object name if valid, else None
    "reason": str         # Human-readable explanation
}
```

### Detection Schema
```python
{
    "label": str,         # Object class name
    "cx": float,          # Normalized center X (0-1)
    "cy": float,          # Normalized center Y (0-1)
    "radius": float,      # Normalized radius (0-1)
    "confidence": float   # Detection confidence (0-1)
}
```

### Global State Schema
```python
{
    "visible_objects": list[str],  # Current detectable objects
    "last_command": str | None,    # Last transcribed user text
    "last_decision": dict | None,  # Last Gemini validation result
    "demo_running": bool           # Demo loop state flag
}
```

---

## Deployment Guide

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with API keys
echo "GEMINI_API_KEY=your_key" > .env
echo "ELEVEN_API_KEY=your_key" >> .env

# Run server
python app.py  # Starts on http://localhost:5000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

### Production Deployment
```bash
# Backend
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Frontend
cd frontend
npm run build
# Serve dist/ with nginx or static file server
```

---

## Testing Strategies

### Voice Pipeline Testing
```python
# Test without microphone (text input fallback)
# VoiceService automatically falls back to console input if audio fails

# Test Gemini validation
from services.voice_service import VoiceService
vs = VoiceService()
decision = vs.process_command("pick the skull", ["hotdog", "skull", "nut"])
assert decision["valid"] == True
assert decision["target"] == "skull"
```

### API Testing
```bash
# Test voice endpoint
curl -X POST http://localhost:5000/api/voice/listen \
  -H "Content-Type: application/json" \
  -d '{"duration": 4}'

# Test arm polling
curl http://localhost:5000/api/arm/next

# Test status
curl http://localhost:5000/api/status
```

### LeRobot Bridge Testing
```python
# Mock LeRobot for testing
class MockRobot:
    def pick_object(self, target):
        print(f"MOCK: Picking {target}")
        return {"success": True}

# Replace in lerobot_bridge.py
robot = MockRobot()
```

---

## Error Handling

### Voice Service Errors
- **No microphone**: Falls back to text input (console)
- **STT failure**: Returns None, triggers "No command detected" response
- **Gemini API error**: Retries 3 times with exponential backoff, returns error decision
- **ElevenLabs error**: Logs error, continues without TTS

### CV Service Errors
- **Model not found**: Falls back to yolo11n.pt
- **Video not found**: Logs error, stream returns empty frames
- **Detection failure**: Returns empty detection list

### LeRobot Bridge Errors
- **Current**: Logs error, continues (no crash)
- **Recommended**: Add try/except in `run_lerobot_commands()`, log to SystemLog

---

## Performance Considerations

### Backend
- Voice cycle: ~5-8 seconds (TTS + listen + STT + Gemini + TTS)
- CV streaming: 20 FPS target, ~50ms per frame
- Detection polling: 200ms intervals from frontend
- Gemini API: ~1-2 seconds per validation

### Frontend
- GridCanvas: 60 FPS animation (requestAnimationFrame)
- Video streams: 420px tall, side-by-side layout
- Log updates: Instant (React state)
- Hover cards: CSS animations, no performance impact

### Optimization Tips
- Use Gemini Flash (not Pro) for faster responses
- Cache YOLO model in memory (already implemented)
- Reduce CV FPS if CPU-bound (config: CV_STREAM_FPS)
- Use ElevenLabs turbo_v2 for lowest latency

---

## Security Considerations

### API Keys
- Store in .env file (never commit to git)
- Use environment variables in production
- Rotate keys regularly

### CORS
- Currently allows all origins (development)
- Production: Restrict to frontend domain only
```python
CORS(app, origins=["https://your-frontend-domain.com"])
```

### Input Validation
- Voice commands validated against whitelist (visible_objects)
- Gemini provides additional validation layer
- No SQL injection risk (no database)

---

## Troubleshooting

### "No microphone detected"
- Check sounddevice/pyaudio installation
- Verify microphone permissions
- Falls back to text input automatically

### "Gemini API error"
- Verify GEMINI_API_KEY in .env
- Check API quota/billing
- Review error logs for rate limiting

### "YOLO model not found"
- Verify model path: `backend/runs/detect/train/weights/best.pt`
- Falls back to yolo11n.pt automatically
- Re-train model if needed

### "LeRobot not responding"
- Check LeRobot device connection
- Verify API URL/port in config
- Test with mock robot first

---

## File Structure Reference

```
Scrapple/
├── backend/
│   ├── app.py                 # Flask entry point
│   ├── config.py              # Configuration constants
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (not in git)
│   ├── services/
│   │   ├── voice_service.py   # Voice pipeline (TTS/STT/Gemini)
│   │   ├── cv_video_service.py # YOLO detection + streaming
│   │   └── lerobot_bridge.py  # LeRobot integration point
│   ├── routes/
│   │   ├── voice.py           # POST /api/voice/listen
│   │   ├── arm.py             # GET /api/arm/next
│   │   ├── status.py          # GET /api/status
│   │   ├── demo.py            # POST /api/demo/start|stop
│   │   └── video.py           # GET /api/video/feed, /api/detections
│   ├── dataset/               # YOLO training data
│   │   ├── train/             # 78 training images
│   │   ├── test/              # 19 test images
│   │   └── data.yaml          # Class definitions
│   └── runs/detect/train/weights/
│       └── best.pt            # Trained YOLO model
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Main React component
│   │   ├── main.tsx           # React entry point
│   │   ├── index.css          # Global styles
│   │   └── components/
│   │       ├── GridCanvas.tsx      # Animated background
│   │       ├── HudHeader.tsx       # Title overlay
│   │       ├── HudFooter.tsx       # Status bar
│   │       ├── CVVideoStream.tsx   # YOLO detection display
│   │       ├── VideoDisplay.tsx    # Webcam feed
│   │       ├── SystemLog.tsx       # Terminal log
│   │       └── CameraFeed.tsx      # Unused placeholder
│   ├── package.json           # Node dependencies
│   └── vite.config.ts         # Vite configuration
└── ARCHITECTURE.md            # This file
```

---

## Next Steps for LeRobot Integration

### Phase 1: Basic Control (Recommended Start)
1. Extend `lerobot_bridge.py` with actual control commands
2. Test with mock robot or simulator
3. Verify voice → validation → pick flow works end-to-end

### Phase 2: Camera Integration
1. Replace test video with LeRobot camera feed
2. Run YOLO on live camera stream
3. Update frontend to display live feed

### Phase 3: CV-Guided Picking
1. Extract object coordinates from detections
2. Convert normalized coords to real-world positions
3. Pass position data to LeRobot pick commands

### Phase 4: Advanced Features
1. Add trajectory planning
2. Implement collision avoidance
3. Add multi-object picking sequences
4. Integrate force feedback

---

## Contact & Support

**For AI Agents**: This document is designed for AI readability. All integration points are clearly marked with "INTEGRATION POINT" or "TODO" comments in code.

**Key Integration Files**:
- `backend/services/lerobot_bridge.py` — Primary extension point
- `backend/routes/arm.py` — API endpoint for polling
- `backend/config.py` — Configuration constants
- `frontend/src/components/VideoDisplay.tsx` — Camera feed placeholder

**Testing Approach**: Start with Strategy 1 (Direct Bridge Extension) for quickest results, then migrate to Strategy 2 (Polling) or Strategy 3 (New Endpoint) as needed.
