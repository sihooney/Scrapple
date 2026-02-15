"""
Voice Interaction Endpoints
=============================
POST /api/voice/listen — Full voice flow with TTS, STT, Gemini evaluation
"""

from flask import jsonify, request
from services.lerobot_bridge import run_lerobot_commands
from config import Config


def register_voice_routes(app, global_state, voice_service):
    """Register voice interaction routes."""

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
        duration = request.json.get('duration', Config.AUDIO_RECORD_SECONDS) if request.json else Config.AUDIO_RECORD_SECONDS

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
