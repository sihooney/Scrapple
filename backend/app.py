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

import os
from flask import Flask
from flask_cors import CORS
from config import Config
from services.voice_service import VoiceService

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

# Register route modules
from routes.status import register_status_routes
from routes.voice import register_voice_routes
from routes.demo import register_demo_routes
from routes.arm import register_arm_routes

register_status_routes(app, global_state)
register_voice_routes(app, global_state, voice_service)
register_demo_routes(app, global_state)
register_arm_routes(app, global_state)


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


if __name__ == '__main__':
    print("=" * 60)
    print("  🤖  SCRAPPLE — Salvage Robot Backend")
    print("=" * 60)
    print(f"  Visible Objects: {Config.DEFAULT_VISIBLE_OBJECTS}")
    print(f"  Audio Sample Rate: {Config.AUDIO_SAMPLE_RATE} Hz")
    print(f"  Gemini Model: {Config.GEMINI_MODEL}")
    print(f"  ElevenLabs Voice: {Config.ELEVENLABS_VOICE_ID}")
    print("-" * 60)
    app.run(host='0.0.0.0', port=5000, debug=(os.getenv('FLASK_ENV', 'development') == 'development'))