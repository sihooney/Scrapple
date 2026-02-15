"""
Scrapple — Centralized Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── API Keys ─────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ELEVEN_API_KEY: str = os.getenv("ELEVEN_API_KEY", "")

    # ── Gemini ───────────────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 256
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_RESPONSE_MIME_TYPE: str = "application/json"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY: float = 2.0

    # ── ElevenLabs ───────────────────────────────────────────
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"
    ELEVENLABS_MODEL: str = "eleven_monolingual_v1"

    # ── Audio ────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_RECORD_SECONDS: int = 4

    # ── Vision ───────────────────────────────────────────────
    DEFAULT_VISIBLE_OBJECTS: list[str] = [
        "gear", "heart", "hotdog", "nut", "skull",
    ]
