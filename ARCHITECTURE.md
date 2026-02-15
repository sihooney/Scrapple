# Scrapple — Architecture and Demo Flow

## Overview

Scrapple is the front-end and I/O system for the MakeUofT salvage robot demo. It directs the robotic arm (LeRobot) **which object to pick** from a **hardcoded list**; the RL model has no computer vision for this demo.

---

## Demo flow

1. User presses **Start** on the website → demo loop begins.
2. **Voice (TTS):** Backend says: *"Please select what object to choose. I see [heart, hot dog, gear, screw]. What is the salvage target?"*
3. **User speaks** → STT → Gemini validates against the hardcoded list → decision `{ valid, target, reason }`.
4. **Voice feedback:** Backend speaks acceptance or rejection (TTS).
5. **LeRobot:** If valid, backend runs command-prompt / control commands for the chosen target (manual entry may be required).
6. **Loop continues:** prompt again → user speaks → process → LeRobot → repeat until user presses **Stop**.
7. **Website:** Live terminal log shows prompts, user command, decision, BOT lines (voice feedback), and `LeRobot: pick "X"`.

---

## Components

- **Frontend (React + Vite):** Start/Stop buttons, demo loop (calls `POST /api/voice/listen` repeatedly), SystemLog as live terminal, VoiceControl for one-shot mic when demo is not running.
- **Backend (Flask):** Voice I/O (VoiceService: TTS prompt → listen → STT → Gemini → TTS result), global state (`visible_objects` = hardcoded list, `last_decision`, `demo_running`), LeRobot bridge (placeholder that logs; RL team can add real commands).
- **Config:** `DEFAULT_VISIBLE_OBJECTS` in `backend/config.py` is the single source for the demo object list. No CV pipeline for the demo.

---

## API contract (for RL / arm team)

### `POST /api/voice/listen`

- **Request body:** `{ "duration": 5 }` (seconds to listen).
- **Response (success):**  
  `{ "command": "<user text>", "decision": { "valid": bool, "target": "<name or null>", "reason": "<string>" }, "prompt_spoken": "<TTS prompt>", "tts_result": "<TTS result>" }`
- When `decision.valid === true`, **`decision.target`** is the object to pick (e.g. `"heart"`). The backend already calls the LeRobot bridge with this target; the arm pipeline can also read it from this response or from `GET /api/arm/next`.

### `GET /api/arm/next`

- Returns the last valid pick target for polling.  
- **Response:** `{ "target": "<name>" }` if the last decision was valid and had a target, else `{ "target": null }`.

### `GET /api/status`

- **Response:** `{ "status": "online", "state": { "visible_objects", "last_command", "last_decision", "demo_running" } }`.  
- `state.last_decision` includes `valid`, `target`, `reason` for the last voice round.

### `POST /api/demo/start` and `POST /api/demo/stop`

- Signal that the frontend has started or stopped the demo loop.  
- Response: `{ "ok": true, "demo_running": true|false }`.

---

## LeRobot integration

- **Location:** `backend/services/lerobot_bridge.py` — `run_lerobot_commands(target: str)`.
- **Current behaviour:** Logs and prints `LeRobot: pick target = "<name>"`. Manual entry may be used to drive the arm.
- **Extension:** The RL/arm team can replace or extend this with actual LeRobot API or CLI calls.

---

## Deployment

- **Backend:** Run from `Scrapple/backend` with a Python venv; `pip install -r requirements.txt`; set env vars `GEMINI_API_KEY`, `ELEVEN_API_KEY`. Start with `python app.py` (Flask on port 5000).
- **Frontend:** From `Scrapple/frontend`, `npm install` and `npm run dev` (dev server proxies or points to `http://localhost:5000` for API).
- **CORS:** Backend allows frontend origin via Flask-CORS.
