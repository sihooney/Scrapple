from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from services.voice_service import VoiceService

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize Services
voice_service = VoiceService()

# Global State (Simulated partial DB)
global_state = {
    "visible_objects": Config.DEFAULT_VISIBLE_OBJECTS,
    "last_command": None,
    "last_decision": None
}

@app.route('/')
def index():
    return "<h1>Scrapple Backend Online</h1><p>Endpoints:</p><ul><li>GET /api/status</li><li>POST /api/voice/listen</li></ul>"

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "online", "state": global_state})

@app.route('/api/voice/listen', methods=['POST'])
def trigger_voice_listen():
    """
    Manually trigger the voice loop.
    1. Listen
    2. Transcribe
    3. Gemini Evaluate
    4. Speak Result
    """
    duration = request.json.get('duration', 5)
    
    # A. Speak Prompt
    voice_service.speak(f"Sensors active. I see {', '.join(global_state['visible_objects'])}. Command?")
    
    # B. Listen
    command_text = voice_service.listen(duration=duration)
    if not command_text:
        voice_service.speak("No command detected.")
        return jsonify({"success": False, "error": "No audio/text"})

    # C. Evaluate
    decision = voice_service.process_command(command_text, global_state['visible_objects'])
    
    # D. Speak Result
    if decision.get("valid"):
        voice_service.speak(f"Affirmative. Acquiring {decision.get('target')}.")
    else:
        voice_service.speak(f"Negative. {decision.get('reason')}")

    # Update State
    global_state["last_command"] = command_text
    global_state["last_decision"] = decision

    return jsonify({
        "command": command_text,
        "decision": decision
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
