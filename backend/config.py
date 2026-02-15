import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_do_not_use_in_prod')
    
    # Audio Settings
    AUDIO_RECORD_SECONDS = 5
    AUDIO_SAMPLE_RATE = 44100
    AUDIO_CHANNELS = 1
    AUDIO_CHUNK_SIZE = 1024
    
    # Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = "gemini-1.5-flash"
    GEMINI_MAX_RETRIES = 2
    GEMINI_RETRY_DELAY = 1.0  # seconds
    
    # ElevenLabs
    ELEVEN_API_KEY = os.getenv('ELEVEN_API_KEY')
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM" # Rachel
    ELEVENLABS_MODEL = "eleven_monolingual_v1"
    
    # Vision / Logic
    # Default fallback if vision service isn't running
    DEFAULT_VISIBLE_OBJECTS = ["screw", "gear", "heart", "hot dog"]
