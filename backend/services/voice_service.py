import io
import json
import os
import wave
import time
from typing import Any

import numpy as np
import speech_recognition as sr
from dotenv import load_dotenv

# Optional imports for hardware
try:
    import sounddevice as sd
    _HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    _HAS_SOUNDDEVICE = False

try:
    import pyaudio
    _HAS_PYAUDIO = True
except (ImportError, OSError):
    _HAS_PYAUDIO = False

try:
    from google import genai
    from google.genai import types as genai_types
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False

try:
    from elevenlabs import ElevenLabs
    _HAS_ELEVENLABS = True
except (ImportError, OSError):
    _HAS_ELEVENLABS = False

from config import Config

class VoiceService:
    """
    Service to handle Voice I/O and Gemini Decision Logic.
    Refactored from standalone 'VoiceCommander'.
    """

    def __init__(self):
        # Gemini Init
        self._gemini_client = None
        if _HAS_GENAI and Config.GEMINI_API_KEY:
            self._gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        else:
            print("[WARN] Gemini Client not initialized (Missing Key or Lib)")

        # ElevenLabs Init
        self._el_client = None
        if _HAS_ELEVENLABS and Config.ELEVEN_API_KEY:
            self._el_client = ElevenLabs(api_key=Config.ELEVEN_API_KEY)
        else:
            print("[WARN] ElevenLabs Client not initialized")

        self.voice_id = Config.ELEVENLABS_VOICE_ID

    def _build_system_instruction(self) -> str:
        return (
            "You are the **Wasteland Salvage Assistant**, the cognitive core of an "
            "autonomous salvage robot operating in a post-apocalyptic dumpster "
            "environment.  Your job is to interpret a human operator's spoken "
            "command and decide whether the requested salvage target is VALID.\n"
            "\n"
            "## RULES (follow these EXACTLY)\n"
            "\n"
            "1. You will receive:\n"
            "   - A text transcription of the operator's voice command.\n"
            "   - A VISIBLE_OBJECTS list: objects the robot's cameras currently see.\n"
            "\n"
            "2. A target is VALID **only if** it appears in the VISIBLE_OBJECTS list.\n"
            "   All comparisons are case-insensitive.\n"
            "\n"
            "3. A target is INVALID if:\n"
            "   - It is NOT in the VISIBLE_OBJECTS list (you cannot see it/not valid), OR\n"
            "   - The text is empty, nonsense, or unintelligible, OR\n"
            "   - The operator does not name any specific object.\n"
            "\n"
            "4. OUTPUT FORMAT — respond with **raw JSON only**.  No markdown fencing,\n"
            "   no explanation, no extra text.  The JSON schema is:\n"
            "\n"
            '   {"valid": <bool>, "target": "<string or null>", "reason": "<string>"}\n'
            "\n"
            "   - If valid is true:  target = the matched object name (lowercase),\n"
            '     reason = a short confirmation (e.g. "Target acquired: heart").\n'
            "   - If valid is false: target = null,\n"
            "     reason = a concise, thematic rejection explaining WHY\n"
            '     (e.g. "Object not in scanner range" or "Target unknown").\n'
            "\n"
            "5. Always respond in character as a terse, professional salvage unit.\n"
        )

    def speak(self, text: str) -> None:
        """Speak text using ElevenLabs (or print fallback)."""
        print(f"\n🔊 [BOT]: {text}")
        
        if not self._el_client or not _HAS_SOUNDDEVICE:
            return

        try:
            audio_gen = self._el_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=Config.ELEVENLABS_MODEL,
                output_format="pcm_16000",
            )
            audio_bytes = b"".join(chunk for chunk in audio_gen)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            sd.play(audio_array, samplerate=16000, blocking=True)
        except Exception as e:
            print(f"[ERR] TTS Error: {e}")

    def listen(self, duration=None) -> str:
        """Record audio and transcribe to text."""
        duration = duration or Config.AUDIO_RECORD_SECONDS
        
        # 1. Try SoundDevice
        if _HAS_SOUNDDEVICE:
            try:
                print(f"🎙️ Listening ({duration}s)...")
                audio_data = sd.rec(
                    int(Config.AUDIO_SAMPLE_RATE * duration),
                    samplerate=Config.AUDIO_SAMPLE_RATE,
                    channels=Config.AUDIO_CHANNELS,
                    dtype="int16",
                )
                sd.wait()
                
                # Convert to wav bytes for Google Speech API
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(Config.AUDIO_CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(Config.AUDIO_SAMPLE_RATE)
                    wf.writeframes(audio_data.tobytes())
                wav_data = wav_buffer.getvalue()
                return self._transcribe(wav_data)
            except Exception as e:
                print(f"[WARN] Mic Error: {e}")

        # Fallback to text input
        return input("⌨️ [MANUAL INPUT]: ").strip()

    def _transcribe(self, audio_bytes: bytes) -> str:
        r = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            print(f"🗣️ [USER]: {text}")
            return text
        except sr.UnknownValueError:
            print("❌ [STT] Unintelligible")
            return ""
        except Exception as e:
            print(f"❌ [STT] Error: {e}")
            return ""

    def process_command(self, user_text: str, visible_objects: list[str]) -> dict:
        """Send command + context to Gemini."""
        if not self._gemini_client:
            return {"valid": False, "reason": "Cognitive core offline (No API Key)."}

        context = f"VISIBLE_OBJECTS: {json.dumps(visible_objects)}\nEvaluate command."
        parts = [context, f'\nOperator said: "{user_text}"']

        for attempt in range(Config.GEMINI_MAX_RETRIES):
            try:
                response = self._gemini_client.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents=parts,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=self._build_system_instruction(),
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                print(f"[WARN] Gemini Error ({attempt+1}): {e}")
                time.sleep(Config.GEMINI_RETRY_DELAY)
        
        return {"valid": False, "reason": "Cognitive core unresponsive."}

# Singleton instance
voice_service = VoiceService()
