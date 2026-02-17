# 🤖 Scrapple — AI-Powered Autonomous Salvage Robot

<div align="center">

**🏆 Built for MakeUofT 2026 | Doomsday Survival Theme**

*"In a world inspired by Mad Max, survival isn't just about finding resources—it's about doing so without losing a limb."*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg)](https://www.typescriptlang.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000.svg)](https://flask.palletsprojects.com/)
[![LeRobot](https://img.shields.io/badge/LeRobot-HuggingFace-FFD21E.svg)](https://github.com/huggingface/lerobot)

[Demo Video](https://www.youtube.com/watch?v=ghlbL9g7NKg) • [Devpost](https://devpost.com/software/scrapple-8al6hw)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Demo](#-demo)
- [System Architecture](#-system-architecture)
- [Technical Highlights](#-technical-highlights)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Backend Architecture](#-backend-architecture-flask--python)
- [Frontend Architecture](#-frontend-architecture-react--typescript--vite)
- [LeRobot Integration](#-lerobot-integration-details)
- [Performance Metrics](#-performance-characteristics)
- [API Reference](#-api-endpoints)
- [Data Flow](#-data-flow-diagrams)
- [Usage Guide](#-usage)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Deployment](#-deployment-guide)
- [Technology Stack](#-technology-stack-summary)
- [Project Structure](#-file-structure)
- [Future Enhancements](#-future-enhancements)
- [Acknowledgments](#-acknowledgments)

---

## 📖 Overview

Scrapple is an **autonomous robotic salvage system** that combines computer vision, natural language processing, and reinforcement learning to enable safe, hands-free object retrieval in hazardous environments. Built during a 24-hour hackathon sprint at **MakeUofT 2026**, the system demonstrates end-to-end integration of modern AI technologies with physical robotics hardware.


### Key Features

🎯 **Voice-Controlled Operation** — Natural language commands validated by Google Gemini 2.0 Flash  
👁️ **Real-Time Object Detection** — Custom-trained YOLO11 model with dual-camera feeds  
🦾 **Autonomous Pick-and-Place** — LeRobot imitation learning trained on Google Colab  
🎨 **Cyberpunk UI** — React-based interface with live video streams and terminal logs  
🔄 **Intelligent Resource Management** — Dynamic camera pause/resume for hardware sharing  

---

## 🎥 Demo

[![Scrapple Demo](https://img.youtube.com/vi/ghlbL9g7NKg/maxresdefault.jpg)](https://www.youtube.com/watch?v=ghlbL9g7NKg)

*Click to watch the full demonstration video*

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + TypeScript)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Voice Control│  │  CV Streams  │  │   System Log         │  │
│  │ (Web Speech) │  │  (2 Cameras) │  │   (Terminal UI)      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
└─────────┼──────────────────┼──────────────────────────────────┘
          │ HTTP/REST        │ MJPEG Stream
┌─────────▼──────────────────▼──────────────────────────────────┐
│                     BACKEND (Flask + Python)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Voice Service│  │  CV Service  │  │  LeRobot Bridge      │ │
│  │ • Gemini API │  │  • YOLO11    │  │  • Process Mgmt      │ │
│  │ • ElevenLabs │  │  • OpenCV    │  │  • Camera Control    │ │
│  │ • STT (Google│  │  • 2 Cameras │  │  • Trigger System    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                       ┌────────▼────────────────┐
                       │   LeRobot Hardware      │
                       │   • 6-DOF Arm           │
                       │   • Imitation Learning  │
                       │   • Policy Execution    │
                       └─────────────────────────┘
```

### Voice Command Flow (A→E State Machine)

The system implements a deterministic voice interaction pipeline:

```
A. DETECT → CV pipeline identifies visible objects in real-time
B. ANNOUNCE → Gemini TTS: "Scanners active. I see [objects]. What is the salvage target?"
C. LISTEN → Web Speech API or backend STT captures operator command
D. VALIDATE → Gemini 2.0 Flash evaluates command against visible objects
E. EXECUTE → If valid, pause cameras → trigger LeRobot → autonomous pick-and-place
```

**Critical Path**: 
```
User Voice → Web Speech API → POST /api/voice/evaluate → Gemini Validation 
→ POST /api/lerobot/run → Camera Pause → LeRobot Subprocess → Pick Object
```


---

## 🎯 Technical Highlights

### 1. LeRobot Hardware Integration & Reinforcement Learning

- **Custom 6-DOF Robotic Arm**: 3D-printed chassis with 6x 6V servos
- **Imitation Learning Pipeline**: Trained on Google Colab using human demonstrations
- **Policy Model**: ACT (Action Chunking Transformer) for smooth trajectory generation
- **Real-Time Inference**: Closed-loop control with camera feedback
- **Dataset**: 80+ demonstration episodes stored on HuggingFace
- **Intelligent Camera Management**: Dynamic pause/resume system prevents hardware conflicts

**Key Innovation**: Hybrid communication system (stdin + file triggers) enables both direct subprocess control and external process coordination, allowing seamless integration with the CV pipeline.

### 2. Real-Time Computer Vision Pipeline

- **Custom YOLO11 Training**: 78 hand-labeled images across 5 object classes (hotdog, skull, nut, gear, heart)
- **Dual-Camera System**: Front camera (YOLO detection) + Handeye camera (raw feed)
- **Performance Optimization**: Inference every 3rd frame, cached detections, 70% JPEG quality
- **Thread-Safe Architecture**: Lock-based detection state management for concurrent access
- **Cyberpunk Visualization**: Animated neon overlays with rotating arcs and confidence scores
- **MJPEG Streaming**: Real-time video delivery at 10-15 FPS per camera

**Key Innovation**: Built from scratch without pre-existing frameworks, demonstrating deep understanding of OpenCV, YOLO architecture, and real-time video processing. Camera resource sharing system allows LeRobot to access cameras without conflicts.

### 3. Multi-Modal AI Integration

- **Google Gemini 2.0 Flash**: 
  - Lenient natural language parsing ("grab that" → first visible object)
  - Strict JSON schema enforcement for reliable parsing
  - Exponential backoff retry logic (3 attempts, 10s base delay)
  - Temperature 0.0 for deterministic responses
  
- **ElevenLabs TTS**: 
  - "George" voice (deep, cinematic) for post-apocalyptic aesthetic
  - Turbo V2 model for lowest latency (~2-3s per utterance)
  - PCM 16kHz output for real-time playback
  
- **Google Web Speech API**: 
  - Browser-based STT with interim results
  - Energy threshold tuning for noisy environments
  - Graceful fallback to backend STT or text input

**Key Innovation**: Three-tier fallback system (sounddevice → pyaudio → console) ensures operation even without microphone access.

### 4. Full-Stack Implementation

- **Backend**: Flask REST API with 15+ endpoints, modular service architecture
- **Frontend**: React 19 + TypeScript with Web Speech API integration
- **Styling**: Tailwind CSS + custom cyberpunk theme (neon glows, animated backgrounds)
- **State Management**: Real-time polling (5s intervals), event-driven updates
- **Error Handling**: Comprehensive fallback chains at every layer


---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **2x USB Webcams** (OpenCV-compatible)
- **API Keys**: [Google Gemini](https://ai.google.dev/), [ElevenLabs](https://elevenlabs.io/)
- **Optional**: SO-101 Follower Arm for full hardware integration

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/scrapple.git
cd scrapple
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your API keys
echo "GEMINI_API_KEY=your_gemini_key_here" > .env
echo "ELEVEN_API_KEY=your_elevenlabs_key_here" >> .env
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
```

#### 4. Run the Application
```bash
# Terminal 1: Start backend
cd backend
python app.py  # Runs on http://localhost:5000

# Terminal 2: Start frontend
cd frontend
npm run dev  # Runs on http://localhost:5173
```

#### 5. Open in Browser
Navigate to `http://localhost:5173` and grant microphone permissions when prompted.

---

## 💡 How It Works

### Voice Command Flow

```
1. User clicks "RUN ONCE" → System announces visible objects via TTS
2. User speaks command → Web Speech API captures audio
3. Gemini validates command → Checks against detected objects
4. If valid → Cameras pause → LeRobot executes pick-and-place
5. Cameras resume → System ready for next command
```

### Computer Vision Pipeline

```
Camera Feed → YOLO11 Detection (every 3rd frame) → Neon Overlays
    ↓
Detection Cache (thread-safe) → MJPEG Stream → Frontend Display
    ↓
Hover Cards with [ACQUIRE] buttons → Manual pick trigger
```

### LeRobot Training & Execution

```
1. Data Collection: Human teleoperation demonstrations
2. Upload to HuggingFace: jakkii/eval_scrapple dataset
3. Train on Google Colab: Imitation learning policy
4. Deploy: Load weights → Real-time inference → Servo control
```


---

## 🔧 Backend Architecture

### Core Services

#### 1. VoiceService (`backend/services/voice_service.py`)
**Multi-modal voice interaction system with graceful degradation**

- **Speech-to-Text**: Google Web Speech API (free tier)
  - Energy threshold tuning for noisy environments
  - Dynamic ambient noise adjustment
  - Pause detection (0.8s silence threshold)
  
- **Cognitive Validation**: Gemini 2.0 Flash
  - Strict JSON schema enforcement
  - Lenient command parsing ("pick it" → first visible object)
  - Exponential backoff retry logic (3 attempts, 10s base delay)
  - Temperature: 0.0 (deterministic)
  - Max tokens: 128 (fast responses)
  
- **Text-to-Speech**: ElevenLabs "George" voice
  - Model: `eleven_turbo_v2` (lowest latency)
  - Output: PCM 16kHz for real-time playback
  - Fallback: Silent operation if API unavailable
  
- **Audio Capture**: Multi-backend fallback chain
  1. `sounddevice` (preferred, Windows-optimized)
  2. `pyaudio` (cross-platform fallback)
  3. Console text input (no-microphone mode)

**Key Innovation**: Lenient command parsing allows natural language ("grab that", "I want the skull") instead of rigid syntax.

#### 2. CVVideoService (`backend/services/cv_video_service.py`)
**Real-time dual-camera YOLO detection pipeline**

- **Model**: Custom-trained YOLO11n
  - Training: 78 images (5 classes: hotdog, skull, nut, gear, heart)
  - Confidence threshold: 0.5
  - Inference: Every 3rd frame (performance optimization)
  
- **Dual Camera System**:
  - **Camera 2 (Front)**: YOLO detection with neon overlays
  - **Camera 3 (Handeye)**: Raw feed for operator visibility
  - Resolution: 640x480 @ 10-15 FPS
  
- **Intelligent Pause/Resume**:
  - Pauses both cameras when LeRobot needs hardware access
  - Displays frozen frame with "LEROBOT ACTIVE" overlay
  - Automatic resume after robot operation completes
  - Thread-safe state management
  
- **Visualization**: Cyberpunk neon aesthetic
  - Animated rotating arcs around detections
  - Real-time confidence scores
  - Hover cards with [ACQUIRE] buttons
  
- **Performance**: 
  - MJPEG streaming at 70% JPEG quality
  - Frame delay control (1/FPS target)
  - Cached detections between YOLO runs

**Key Innovation**: Camera resource sharing system allows LeRobot to access cameras without conflicts, with visual feedback to operator.

#### 3. LeRobotBridge (`backend/services/lerobot_bridge.py`)
**Process management and hardware integration layer**

- **Subprocess Management**:
  - Spawns `lerobot.record` with full parameter control
  - Stdin pipe for Enter key injection (episode triggers)
  - Stdout capture for real-time logging
  - Graceful shutdown with 5s timeout → force kill
  
- **Configuration**:
  - Robot: SO-101 Follower Arm (6-DOF)
  - Port: COM24 (Windows serial)
  - Cameras: Dual OpenCV (indices 2, 3)
  - Dataset: HuggingFace repo (`jakkii/eval_scrapple`)
  - Policy: Trained imitation learning model
  
- **Communication Modes**:
  1. **Stdin Control**: Send Enter to start/stop episodes
  2. **File-based Triggers**: Write `lerobot_trigger.txt` for external monitoring
  3. **Callback System**: Event notifications (target set, output, status)
  
- **State Management**:
  - Thread-safe process tracking
  - Last target caching
  - Running status polling

**Key Innovation**: Hybrid communication system (stdin + file triggers) allows both direct control and external process coordination.

---

## 🎨 Frontend Architecture (React + TypeScript + Vite)

### Component Structure

#### App.tsx (Main Orchestrator)
- **State Management**: Logs, LeRobot status polling (5s intervals)
- **Layout**: Two-column design (controls | video feeds + terminal)
- **Event Handling**: Voice cycle coordination, CV pick triggers

#### VoiceControl.tsx (Voice Interface)
**Multi-state voice command system**

- **States**: `idle` → `announcing` → `listening` → `processing` → `executing` → `idle`
- **Web Speech API Integration**:
  - Continuous: false (single utterance)
  - Interim results: true (live transcript)
  - Language: en-US
  - Error handling: no-speech, not-allowed, network errors
  
- **Flow**:
  1. Click "RUN ONCE" → Backend announces objects
  2. 3s delay for TTS completion
  3. Start Web Speech recognition
  4. Display interim + final transcripts
  5. Send to Gemini for validation
  6. If valid → trigger LeRobot + show result
  
- **UI Elements**:
  - Dynamic button text (state-based)
  - Status indicator (green/amber/red with glow)
  - Transcript display (live + interim)
  - Gemini result card (valid/invalid)
  - Terminate button (force kill + UI reset)

#### CVVideoStream.tsx (Video Display)
**Dual-purpose camera feed component**

- **MJPEG Streaming**: Direct `<img>` tag with stream URL
- **Detection Overlay System**:
  - Polls `/api/detections` every 500ms
  - Converts normalized coords (0-1) to pixel positions
  - Calculates image rect with aspect ratio preservation
  - Renders hover zones over detections
  
- **Hover Cards**:
  - Emoji icons (🌭, 💀, 🔩, ⚙️, ❤️)
  - Object label + confidence %
  - [ACQUIRE] button → triggers LeRobot
  
- **Dual Mode**:
  - **YOLO Mode** (Camera 2): Shows detections + overlays
  - **RAW Mode** (Camera 3): Clean feed, no overlays

#### SystemLog.tsx (Terminal Display)
**Reverse-chronological log with color-coded entries**

- **Entry Types**:
  - `[USR]` — User voice commands (green)
  - `[BOT]` — Gemini/TTS responses (cyan)
  - `[SYS]` — System events (amber)
  
- **Features**:
  - Auto-scroll to top (newest first)
  - Timestamp per entry (HH:MM:SS)
  - Entry count badge
  - Monospace font (Share Tech Mono)

### Styling (Tailwind + Custom CSS)
**Cyberpunk/post-apocalyptic aesthetic**

- **Color Palette**:
  - Primary: Neon cyan (#00e5ff)
  - Accent: Amber (#ffaa00)
  - Success: Green (#00ff41)
  - Danger: Red (#ff0033)
  - Background: Dark grays (#0a0a0a, #1a1a1a)
  
- **Typography**:
  - Headers: Orbitron (geometric, futuristic)
  - Monospace: Share Tech Mono (terminal aesthetic)
  
- **Effects**:
  - Neon glow (box-shadow with color)
  - Animated grid background (60 FPS canvas)
  - Corner brackets on video feeds
  - Pulsing status indicators
  - Cursor blink animation


---

## 🦾 LeRobot Integration Details

### Hardware Setup
- **Robot**: SO-101 Follower Arm (6-DOF, 3D-printed chassis)
- **Servos**: 6x 6V servos with internal microcontroller
- **Cameras**: 2x USB webcams (OpenCV indices 2, 3)
- **Connection**: USB serial (COM24 on Windows)

### Training Pipeline (Google Colab)
1. **Data Collection**: Human teleoperation demonstrations
   - Record episodes via `lerobot.record`
   - Store to HuggingFace dataset (`jakkii/eval_scrapple`)
   - Capture: joint positions + camera frames + actions
   
2. **Imitation Learning**: Policy training
   - Model: ACT (Action Chunking Transformer) or Diffusion Policy
   - Input: Camera images + proprioceptive state
   - Output: Joint position commands
   - Training: Google Colab GPU (race against timeout)
   
3. **Deployment**: Policy execution
   - Load trained weights from `outputs/train/scrapple_model_4`
   - Real-time inference during pick-and-place
   - Closed-loop control with camera feedback

### Execution Flow
```
1. Voice/CV trigger → Target selected ("nut")
2. Backend calls POST /api/lerobot/run
3. CV service pauses cameras (releases hardware)
4. Write trigger file: TARGET=nut, TIMESTAMP=...
5. LeRobot subprocess reads trigger
6. Policy executes: approach → grasp → lift → place
7. Episode completes
8. Backend resumes cameras
9. UI shows "COMPLETE" status
```

### Camera Resource Management
**Critical Challenge**: LeRobot and CV service both need camera access

**Solution**: Intelligent pause/resume system
- CV service releases cameras when LeRobot starts
- Frozen frame displayed with overlay
- LeRobot gets exclusive camera access
- CV service resumes after robot completes
- Thread-safe state management prevents race conditions

---

## 📊 Performance Characteristics

### Latency Breakdown
- **Voice Command Cycle**: ~5-8 seconds total
  - TTS announcement: 2-3s
  - User speech: 1-2s
  - STT processing: 0.5-1s
  - Gemini validation: 1-2s
  - TTS response: 2-3s
  
- **CV Detection**: ~50ms per frame
  - YOLO inference: 30-40ms
  - Overlay rendering: 5-10ms
  - JPEG encoding: 5-10ms
  
- **LeRobot Pick**: ~10-15 seconds
  - Approach: 3-5s
  - Grasp: 2-3s
  - Lift: 2-3s
  - Place: 3-5s

### Throughput
- **CV Streaming**: 10-15 FPS (dual cameras)
- **Detection Polling**: 2 Hz (500ms intervals)
- **Status Polling**: 0.2 Hz (5s intervals)

### Resource Usage
- **Backend**: ~500MB RAM (YOLO model loaded)
- **Frontend**: ~100MB RAM (React + video streams)
- **LeRobot**: ~1GB RAM (policy model + camera buffers)

### Performance Metrics Summary

| Metric | Value |
|--------|-------|
| **Voice Command Latency** | 5-8 seconds (end-to-end) |
| **CV Detection Speed** | 30-40ms per frame (YOLO inference) |
| **Video Streaming** | 10-15 FPS (dual cameras, MJPEG) |
| **LeRobot Pick Time** | 10-15 seconds (approach → grasp → place) |
| **Model Accuracy** | 87% confidence on trained objects |
| **Memory Usage** | ~500MB (backend), ~100MB (frontend) |


---

## 🔌 API Endpoints

### Voice Routes (`backend/routes/voice.py`)
- `POST /api/voice/announce` — TTS announcement of visible objects
- `POST /api/voice/listen` — Full backend voice cycle (STT + Gemini + TTS)
- `POST /api/voice/evaluate` — Evaluate Web Speech API transcript

**Example Request**:
```bash
curl -X POST http://localhost:5000/api/voice/evaluate \
  -H "Content-Type: application/json" \
  -d '{"command": "pick the skull"}'
```

**Example Response**:
```json
{
  "command": "pick the skull",
  "decision": {
    "valid": true,
    "target": "skull",
    "reason": "Valid object from visible list"
  },
  "tts_result": "Confirmed. Locking on to target: skull."
}
```

### LeRobot Routes (`backend/routes/arm.py`)
- `GET /api/arm/next` — Poll for last valid target
- `POST /api/lerobot/start` — Start recording session
- `POST /api/lerobot/stop` — Stop recording session
- `POST /api/lerobot/enter` — Send Enter key to process
- `POST /api/lerobot/run` — Trigger pick sequence (pause cameras + write trigger)
- `POST /api/lerobot/kill` — Force terminate + resume cameras
- `GET /api/lerobot/status` — Session status + last target

### CV Routes (`backend/routes/video.py`)
- `GET /api/video/feed` — MJPEG stream (Camera 2, YOLO overlays)
- `GET /api/video/handeye` — MJPEG stream (Camera 3, raw)
- `GET /api/detections` — JSON array of current detections

**Example Response**:
```json
[
  {
    "label": "skull",
    "cx": 0.5,
    "cy": 0.3,
    "radius": 0.1,
    "confidence": 0.87
  }
]
```

### System Routes
- `GET /api/status` — Global state snapshot
- `POST /api/demo/start|stop` — Demo loop signals
- `POST /api/video/pause|resume` — Manual camera control

---

## 📈 Data Flow Diagrams

### Voice Command Flow
```
User speaks "pick the skull"
    ↓
Web Speech API (browser)
    ↓
POST /api/voice/evaluate {"command": "pick the skull"}
    ↓
VoiceService.process_command()
    ↓
Gemini 2.0 Flash validation
    ↓
{"valid": true, "target": "skull", "reason": "Valid object"}
    ↓
run_lerobot_commands("skull")
    ↓
POST /api/lerobot/run (internal)
    ↓
cv_video_service.pause() — Release cameras
    ↓
Write lerobot_trigger.txt
    ↓
LeRobot subprocess picks up skull
    ↓
cv_video_service.resume() — Reclaim cameras
    ↓
Frontend shows "COMPLETE"
```

### CV Detection Flow
```
Camera 2 captures frame
    ↓
YOLO11 inference (every 3rd frame)
    ↓
Detections: [{label: "skull", cx: 0.5, cy: 0.3, confidence: 0.87}, ...]
    ↓
Store in thread-safe cache
    ↓
MJPEG encoder (70% quality)
    ↓
Stream to frontend (multipart/x-mixed-replace)
    ↓
Frontend polls GET /api/detections
    ↓
Render hover zones over video
    ↓
User hovers → Show card with [ACQUIRE] button
    ↓
Click [ACQUIRE] → POST /api/lerobot/run
```

---

## 🎮 Usage

### Voice Control Mode

1. Click **"RUN ONCE"** button
2. Wait for TTS announcement: *"Scanners active. I see [objects]. What is the salvage target?"*
3. Speak your command: *"Pick the skull"* or *"Grab the nut"*
4. System validates command with Gemini
5. If valid, LeRobot autonomously picks the object

**Supported Commands**:
- `"[object]"` — Direct command
- `"grab [object]"` — Casual syntax
- `"I want the [object]"` — Natural language
- After speech recognition commands, Gemini process natural language commands, allowing for no specific commands to be required

### Visual Selection Mode

1. Hover over detected objects in the video feed
2. Hover card appears with object name and confidence
3. Click **[ACQUIRE]** button
4. LeRobot executes pick-and-place

### Manual Control

- **Terminate Process**: Force kill LeRobot and reset UI
- **Pause/Resume Video**: Manual camera control via API
- **System Log**: Real-time event monitoring

---

## 🐛 Troubleshooting

### Common Issues

**"No microphone detected"**
- Check sounddevice/pyaudio installation
- Verify microphone permissions in OS
- System automatically falls back to text input

**"Gemini API error"**
- Verify `GEMINI_API_KEY` in `.env`
- Check API quota/billing at [console.cloud.google.com](https://console.cloud.google.com)
- Review logs for rate limiting (429 errors)

**"YOLO model not found"**
- Verify path: `backend/runs/detect/train/weights/best.pt`
- System falls back to `yolo11n.pt` automatically
- Re-train model if custom classes needed

**"Camera X NOT FOUND"**
- Check camera indices (Windows: 0, 1, 2, ...)
- Verify cameras are connected and not in use
- Update `CV_LIVE_FEED_CAMERA` and `CV_CAMERA_FEED_INDEX` in config

**"LeRobot not responding"**
- Check robot connection (USB serial)
- Verify `LEROBOT_ROBOT_PORT` in config
- Test with mock robot first (see Testing section)

**"PAUSED - LEROBOT ACTIVE" stuck**
- Call `POST /api/lerobot/kill` to force reset
- Manually call `POST /api/video/resume`
- Check for crashed LeRobot process

**"Web Speech API not supported"**
- Use Chrome or Edge browser
- Ensure HTTPS or localhost (required for Web Speech)
- Fallback: Use backend voice endpoint instead

### Error Handling & Resilience

#### Voice Service
- **No Microphone**: Graceful fallback to console text input
- **STT Failure**: Returns empty string → "No command detected" response
- **Gemini API Error**: 
  - Retry 3x with exponential backoff (10s, 20s, 40s)
  - Rate limit detection (429, 503 errors)
  - Fallback: `{"valid": false, "reason": "Cannot evaluate"}`
- **ElevenLabs Error**: Log error, continue without TTS (silent mode)

#### CV Service
- **Model Not Found**: Fallback to `yolo11n.pt` (pretrained)
- **Camera Not Found**: Display "CAMERA X NOT FOUND" error frame
- **Feed Lost**: Retry camera open after 30 consecutive failures
- **Pause/Resume**: Thread-safe locks prevent race conditions

#### LeRobot Bridge
- **Process Crash**: Detect via `poll()`, log error, reset state
- **Timeout**: 5s graceful shutdown → force kill
- **Camera Conflict**: Pause system ensures exclusive access
- **Trigger File Error**: Resume cameras on exception

#### Frontend
- **Backend Offline**: Graceful degradation (no crashes)
- **Stream Error**: Display "NO_SIGNAL" status
- **Web Speech Unsupported**: Show error message, disable voice control
- **API Timeout**: Show error in log, allow retry

---

## 🛠️ Technology Stack Summary

### Backend
- **Framework**: Flask 3.0+ (Python web server)
- **AI/ML**:
  - Google Gemini 2.0 Flash (command validation)
  - ElevenLabs Turbo V2 (text-to-speech)
  - Google Web Speech (speech-to-text)
  - YOLO11n (object detection)
  - LeRobot (imitation learning)
- **Computer Vision**: OpenCV, Ultralytics
- **Audio**: sounddevice, pyaudio, SpeechRecognition
- **Utilities**: python-dotenv, numpy

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3.4
- **UI Libraries**: Framer Motion, Lucide React
- **Testing**: Vitest, Testing Library

### Hardware
- **Robot**: SO-101 Follower Arm (6-DOF)
- **Cameras**: 2x USB webcams (640x480)
- **Servos**: 6x 6V servos
- **Connection**: USB serial (COM port)

### Infrastructure
- **Training**: Google Colab (GPU)
- **Dataset**: 80+ episodes of manual training

---

## 📁 File Structure

```
Scrapple/
├── backend/
│   ├── app.py                      # Flask entry point
│   ├── config.py                   # Centralized configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # API keys (gitignored)
│   ├── services/
│   │   ├── voice_service.py        # Voice pipeline (STT/Gemini/TTS)
│   │   ├── cv_video_service.py     # YOLO detection + streaming
│   │   └── lerobot_bridge.py       # LeRobot process management
│   ├── routes/
│   │   ├── voice.py                # Voice endpoints
│   │   ├── arm.py                  # LeRobot endpoints
│   │   ├── video.py                # CV streaming endpoints
│   │   ├── status.py               # System status
│   │   └── demo.py                 # Demo control
│   ├── dataset/
│   │   ├── train/                  # 78 training images
│   │   ├── test/                   # 19 test images
│   │   └── data.yaml               # YOLO class definitions
│   ├── runs/detect/train/weights/
│   │   └── best.pt                 # Trained YOLO11 model
│   ├── lerobot_command.txt         # Target file (runtime)
│   └── lerobot_trigger.txt         # Trigger file (runtime)
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Main orchestrator
│   │   ├── main.tsx                # React entry point
│   │   ├── index.css               # Global styles + Tailwind
│   │   └── components/
│   │       ├── VoiceControl.tsx    # Voice interface
│   │       ├── CVVideoStream.tsx   # Video display + overlays
│   │       ├── SystemLog.tsx       # Terminal log
│   │       ├── GridCanvas.tsx      # Animated background
│   │       ├── HudHeader.tsx       # Title overlay
│   │       └── HudFooter.tsx       # Status bar
│   ├── package.json                # Node dependencies
│   ├── vite.config.ts              # Vite configuration
│   └── tailwind.config.js          # Tailwind configuration
├── README.md                       # This file
└── .gitignore                      # Git ignore rules
```


---

## 🚧 Future Enhancements

### Phase 1: Robustness
- [ ] **PID Loop Tuning**: Improve servo control precision
- [ ] **Expand Training Dataset**: 200+ images for better accuracy
- [ ] **Error Recovery**: Automatic retry on failed picks
- [ ] **Collision Detection**: Safety boundaries for arm movement

### Phase 2: Intelligence
- [ ] **Auto-Sorting**: Classify objects by material after pickup
- [ ] **Multi-Object Sequences**: Pick multiple items in one cycle
- [ ] **Adaptive Grasping**: Adjust grip based on object shape
- [ ] **Obstacle Avoidance**: Path planning around detected objects

### Phase 3: Deployment
- [ ] **Edge Computing**: Move backend to Raspberry Pi/Jetson
- [ ] **Mobile App**: iOS/Android control interface
- [ ] **Offline Mode**: Local STT/TTS models (no API dependency)
- [ ] **Battery Power**: Portable operation for field deployment

### Phase 4: Advanced Features
- [ ] **SLAM Integration**: Simultaneous localization and mapping
- [ ] **Multi-Robot Coordination**: Fleet management
- [ ] **Reinforcement Learning**: Online policy improvement
- [ ] **Force Feedback**: Tactile sensing for delicate objects

---

## 🙏 Acknowledgments

**Built for MakeUofT 2026** — Canada's largest hardware hackathon

**Technologies**:
- [LeRobot](https://github.com/huggingface/lerobot) by HuggingFace — Imitation learning framework
- [YOLO](https://github.com/ultralytics/ultralytics) by Ultralytics — Object detection
- [Gemini](https://ai.google.dev/) by Google — Natural language processing
- [ElevenLabs](https://elevenlabs.io/) — Text-to-speech synthesis

**Inspiration**:
- Mad Max franchise — Post-apocalyptic aesthetic
- Keep Talking and Nobody Explodes — Collaborative gameplay
- Boston Dynamics — Robotics innovation

**Team**: Built collaboratively during a 24-hour hackathon sprint

---

## 📄 License

This project was built for educational purposes during MakeUofT 2026. Feel free to use, modify, and learn from the code.

---

## 📧 Contact

**Questions?** Open an issue or reach out via the [Devpost](https://devpost.com/software/scrapple-8al6hw) page.

**Built with ❤️ during MakeUofT 2026**

---

<div align="center">

**⭐ Star this repo if you found it interesting!**

[Demo Video](https://www.youtube.com/watch?v=ghlbL9g7NKg) • [Devpost](https://devpost.com/software/scrapple-8al6hw)

</div>
