"""
Scrapple — Centralized Configuration
=====================================
Ported from working Gemini-Speech-Salvage-Input settings.
All tunable constants live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_do_not_use_in_prod')

    # ── Allowed Object Sets ─────────────────────────────────────────────
    # "Visible" objects are now the ONLY objects.
    # Only what is in this list is considered valid for salvage.
    DEFAULT_VISIBLE_OBJECTS: list[str] = ["hotdog", "skull", "nut", "gear", "heart"]

    # ── Audio Recording ─────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE: int = 16_000   # 16 kHz – matches Gemini expectations
    AUDIO_CHANNELS: int = 1           # Mono
    AUDIO_RECORD_SECONDS: int = 4     # Default listen window (3-5 s range)
    AUDIO_CHUNK_SIZE: int = 1024      # Frames per PyAudio buffer

    # ── Gemini ──────────────────────────────────────────────────────────
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 128          # Keep responses tiny → faster
    GEMINI_TEMPERATURE: float = 0.0              # Deterministic
    GEMINI_RESPONSE_MIME_TYPE: str = "application/json"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY: int = 10                 # Seconds to clear rate limit buckets

    # ── Loop Pacing ─────────────────────────────────────────────────────
    LOOP_DELAY: int = 3                          # Seconds to wait between loops

    # ── ElevenLabs ──────────────────────────────────────────────────────
    ELEVEN_API_KEY = os.getenv('ELEVEN_API_KEY')
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"   # "George" – deep & cinematic
    ELEVENLABS_MODEL: str = "eleven_turbo_v2"           # Lowest-latency model

    # ── Computer Vision ─────────────────────────────────────────────────
    CV_MODEL_PATH: str = "runs/detect/train/weights/best.pt"
    CV_FALLBACK_MODEL: str = "yolo11n.pt"
    CV_VIDEO_PATH: str = "dataset/test_video.mov"
    CV_CONFIDENCE_THRESHOLD: float = 0.5
    CV_STREAM_FPS: int = 20                             # Target frame rate
    CV_JPEG_QUALITY: int = 85                           # JPEG compression quality
