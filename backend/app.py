"""
Scrapple — Flask Backend
========================
Main API server for the salvage robot demo.

Endpoints:
    GET  /api/status        — System status and state
    POST /api/voice/listen  — Trigger voice interaction loop
    POST /api/demo/start    — Signal demo loop started
    POST /api/demo/stop     — Signal demo loop stopped
    GET  /api/arm/next      — Get next pick target for LeRobot
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from services.voice_service import VoiceService
from services.lerobot_bridge import run_lerobot_commands

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize Services
voice_service = VoiceService()

# Global State (demo: hardcoded list; no CV)
global_state = {
    "visible_objects": Config.DEFAULT_VISIBLE_OBJECTS,
    "last_command": None,
    "last_decision": None,
    "demo_running": False,
}


@app.route('/')
def index():
    return (
        "<h1>Scrapple Backend Online</h1><p>Endpoints:</p><ul>"
        "<li>GET /api/status</li>"
        "<li>POST /api/voice/listen</li>"
        "<li>POST /api/demo/start</li><li>POST /api/demo/stop</li>"
        "<li>GET /api/arm/next</li>"
        "</ul>"
    )


@app.route('/api/status', methods=['GET'])
def status():
    """Return system status and current state."""
    return jsonify({"status": "online", "state": global_state})


@app.route('/api/voice/listen', methods=['POST'])
def trigger_voice_listen():
    """
    Trigger the full voice interaction loop.

    Flow (matches Gemini-Speech A→E state machine):
        A. Receive visible_objects from state
        B. Announce visible objects via TTS
        C. Record operator audio (or text fallback)
        D. Send to Gemini for evaluation
        E. Speak result & return structured JSON

    Request body: { "duration": <seconds> }  (optional, defaults to config)

    Response:
        {
            "command": "<user text>",
            "decision": { "valid": bool, "target": "<name or null>", "reason": "<string>" },
            "prompt_spoken": "<TTS prompt>",
            "tts_result": "<TTS result>"
        }
    """
    # Get duration from request or use config default
    duration = request.json.get('duration', Config.AUDIO_RECORD_SECONDS)

    # ── State B: Announce visible objects ─────────────────────────────
    obj_list = ", ".join(global_state["visible_objects"])
    prompt_text = f"Scanners active. I see {obj_list}. What is the salvage target?"
    voice_service.speak(prompt_text)

    # ── State C: Listen for command ──────────────────────────────────
    command_text = voice_service.listen(duration=duration)

    if not command_text:
        tts_result = "No command detected."
        voice_service.speak(tts_result)
        return jsonify({
            "command": None,
            "decision": {"valid": False, "target": None, "reason": "No audio/text detected."},
            "prompt_spoken": prompt_text,
            "tts_result": tts_result,
        })

    # ── State D: Gemini evaluation ───────────────────────────────────
    decision = voice_service.process_command(command_text, global_state["visible_objects"])

    # ── State E: Speak result ────────────────────────────────────────
    if decision.get("valid"):
        tts_result = f"Confirmed. Locking on to target: {decision.get('target')}."
    else:
        reason = decision.get("reason", "Unknown rejection.")
        tts_result = f"Negative. {reason}"
    voice_service.speak(tts_result)

    # Update State
    global_state["last_command"] = command_text
    global_state["last_decision"] = decision

    # LeRobot: after valid decision, run commands for target
    if decision.get("valid") and decision.get("target"):
        run_lerobot_commands(decision["target"])

    return jsonify({
        "command": command_text,
        "decision": decision,
        "prompt_spoken": prompt_text,
        "tts_result": tts_result,
    })


@app.route('/api/demo/start', methods=['POST'])
def demo_start():
    """Signal that the demo loop has started (frontend Start button)."""
    global_state["demo_running"] = True
    return jsonify({"ok": True, "demo_running": True})


@app.route('/api/demo/stop', methods=['POST'])
def demo_stop():
    """Signal that the demo loop has stopped (frontend Stop button)."""
    global_state["demo_running"] = False
    return jsonify({"ok": True, "demo_running": False})


@app.route('/api/arm/next', methods=['GET'])
def arm_next():
    """
    Return the next pick target for the arm/RL pipeline.
    When last_decision is valid, returns { "target": "<name>" }; otherwise { "target": null }.
    """
    decision = global_state.get("last_decision") or {}
    if decision.get("valid") and decision.get("target"):
        return jsonify({"target": decision["target"]})
    return jsonify({"target": None})


if __name__ == '__main__':
    print("=" * 60)
    print("  🤖  SCRAPPLE — Salvage Robot Backend")
    print("=" * 60)
    print(f"  Visible Objects: {Config.DEFAULT_VISIBLE_OBJECTS}")
    print(f"  Audio Sample Rate: {Config.AUDIO_SAMPLE_RATE} Hz")
    print(f"  Gemini Model: {Config.GEMINI_MODEL}")
    print(f"  ElevenLabs Voice: {Config.ELEVENLABS_VOICE_ID}")
    print("-" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)