"""
Voice Interaction Endpoints
=============================
POST /api/voice/announce — Gemini announces visible objects via TTS
POST /api/voice/listen   — Full voice flow with TTS, STT, Gemini evaluation
POST /api/voice/evaluate — Evaluate text command from frontend Web Speech API
"""

from flask import jsonify, request
from services.lerobot_bridge import run_lerobot_commands
from config import Config


def register_voice_routes(app, global_state, voice_service):
    """Register voice interaction routes."""

    @app.route('/api/voice/announce', methods=['POST'])
    def announce_visible_objects():
        """
        Announce visible objects via TTS.
        
        This is called at the start of the voice flow to tell the user
        what objects Gemini can see.
        
        Response:
            {
                "spoken": "<TTS text>",
                "visible_objects": ["nut", "skull", ...]
            }
        """
        obj_list = ", ".join(global_state["visible_objects"])
        prompt_text = f"Scanners active. I see {obj_list}. Say pick the, then the object name."
        
        try:
            voice_service.speak(prompt_text)
        except Exception as e:
            print(f"[VOICE] TTS failed: {e}")
        
        return jsonify({
            "spoken": prompt_text,
            "visible_objects": global_state["visible_objects"],
        })

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
        prompt_text = f"Scanners active. I see {obj_list}. Say pick the, then the object name."
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

    @app.route('/api/voice/evaluate', methods=['POST'])
    def evaluate_voice_command():
        """
        Evaluate a text command from the frontend Web Speech API.
        
        This endpoint receives transcribed text from the browser's
        Web Speech API and evaluates it using Gemini.
        
        Request body:
            {
                "command": "<transcribed text>",
                "visible_objects": ["nut", "skull", ...]  (optional)
            }
        
        Response:
            {
                "command": "<transcribed text>",
                "decision": { "valid": bool, "target": "<name or null>", "reason": "<string>" },
                "tts_result": "<spoken response>"
            }
        """
        data = request.json or {}
        command_text = data.get('command', '').strip()
        
        # Use provided visible_objects or fall back to global state
        visible_objects = data.get('visible_objects') or global_state.get("visible_objects", [])
        
        if not command_text:
            return jsonify({
                "command": None,
                "decision": {"valid": False, "target": None, "reason": "No command provided."},
                "tts_result": "No command detected.",
            })

        print(f"\n[VOICE] Web Speech command: \"{command_text}\"")
        print(f"[VOICE] Visible objects: {visible_objects}")
        
        # Evaluate with Gemini
        decision = voice_service.process_command(command_text, visible_objects)
        
        # Speak result via TTS
        if decision.get("valid"):
            tts_result = f"Confirmed. Locking on to target: {decision.get('target')}."
        else:
            reason = decision.get("reason", "Unknown rejection.")
            tts_result = f"Negative. {reason}"
        
        try:
            voice_service.speak(tts_result)
        except Exception as e:
            print(f"[VOICE] TTS failed: {e}")

        # Update State
        global_state["last_command"] = command_text
        global_state["last_decision"] = decision

        # LeRobot: after valid decision, run commands for target
        if decision.get("valid") and decision.get("target"):
            run_lerobot_commands(decision["target"])

        return jsonify({
            "command": command_text,
            "decision": decision,
            "tts_result": tts_result,
        })
