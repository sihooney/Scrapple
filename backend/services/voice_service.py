"""
Scrapple — Voice & Cognitive Interface
======================================
Production-grade VoiceService: microphone capture → Gemini intent
extraction → ElevenLabs spoken response.

Ported from working Gemini-Speech-Salvage-Input voice_interface.py
"""

from __future__ import annotations

import io
import json
import os
import wave
import time
from typing import Any

import numpy as np
import speech_recognition as sr
from dotenv import load_dotenv

# ── Lazy / optional imports (graceful degradation) ──────────────────
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

# ── Local config ────────────────────────────────────────────────────
from config import Config

load_dotenv()


class VoiceService:
    """Bridges human voice → Gemini cognition → ElevenLabs speech.

    Parameters
    ----------
    voice_id : str | None
        ElevenLabs voice to use.  Falls back to config default.
    record_seconds : int
        Duration of the microphone listen window.
    """

    def __init__(
        self,
        voice_id: str | None = None,
        record_seconds: int | None = None,
    ) -> None:
        self.voice_id: str = voice_id or Config.ELEVENLABS_VOICE_ID
        self.record_seconds: int = record_seconds or Config.AUDIO_RECORD_SECONDS

        # ── Gemini setup ────────────────────────────────────────────
        self._gemini_client = None
        if _HAS_GENAI:
            api_key = Config.GEMINI_API_KEY
            if api_key:
                try:
                    self._gemini_client = genai.Client(api_key=api_key)
                    # Test API key validity with a simple call
                    print("[OK] Gemini client initialized.")
                except Exception as e:
                    print(f"[ERROR] Gemini initialization failed: {e}")
                    print(f"[ERROR] Please check GEMINI_API_KEY in .env – it may be invalid.")
            else:
                print("[ERROR] GEMINI_API_KEY not set in .env")
        else:
            print("[ERROR] google-genai not installed")

        # ── ElevenLabs setup ────────────────────────────────────────
        self._el_client = None
        if _HAS_ELEVENLABS:
            el_key = Config.ELEVEN_API_KEY
            if el_key:
                try:
                    self._el_client = ElevenLabs(api_key=el_key)
                    # Test API key validity
                    print("[OK] ElevenLabs client initialized.")
                except Exception as e:
                    print(f"[ERROR] ElevenLabs initialization failed: {e}")
                    print(f"[ERROR] Please check ELEVEN_API_KEY in .env – it may be invalid.")
            else:
                print("[ERROR] ELEVEN_API_KEY not set in .env")
        else:
            print("[ERROR] elevenlabs not installed")

    # ── Gemini System Instruction (Prompt Engineering) ───────────────
    def _build_system_instruction(self) -> str:
        """Return the system prompt that turns Gemini into the Wasteland
        Salvage Assistant with strict JSON-only output."""

        return (
            "You are the **Wasteland Salvage Assistant**, the cognitive core of an "
            "autonomous salvage robot. Your job is to interpret a human operator's "
            "spoken command and extract the target object they want to grab.\n"
            "\n"
            "## RULES (follow these EXACTLY)\n"
            "\n"
            "1. You will receive:\n"
            "   - A text transcription of the operator's voice command.\n"
            "   - A VISIBLE_OBJECTS list: objects the robot's cameras currently see.\n"
            "\n"
            "2. BE LENIENT - Accept ANY command that expresses intent to grab/pick something:\n"
            "   - 'pick the nut', 'grab skull', 'get the gear', 'take heart' = VALID\n"
            "   - 'I want the hotdog', 'give me the skull', 'that one' = VALID (pick any visible)\n"
            "   - Even partial matches: 'pick it', 'grab that' = VALID (pick first visible object)\n"
            "\n"
            "3. A target is INVALID ONLY if:\n"
            "   - The text is completely empty or unintelligible nonsense, OR\n"
            "   - The operator explicitly says 'no', 'stop', 'cancel', 'nevermind'\n"
            "\n"
            "4. If the operator names an object not in VISIBLE_OBJECTS but expresses grab intent,\n"
            "   pick the FIRST object from VISIBLE_OBJECTS instead and set valid=true.\n"
            "\n"
            "5. OUTPUT FORMAT — respond with **raw JSON only**. No markdown, no extra text:\n"
            "\n"
            '   {"valid": <bool>, "target": "<string or null>", "reason": "<string>"}\n'
            "\n"
            "   - If valid is true: target = object name (lowercase from VISIBLE_OBJECTS)\n"
            '     reason = short confirmation (e.g. "Target acquired: heart")\n'
            "   - If valid is false: target = null\n"
            '     reason = why (e.g. "No grab intent detected")\n'
            "\n"
            "6. Be helpful - when in doubt, say YES and pick a visible target.\n"
        )

    # ── Audio Recording ──────────────────────────────────────────────
    def _record_audio(self, duration: int | None = None) -> dict[str, Any]:
        """Record from the microphone and return audio data.

        Tries backends in order: sounddevice → pyaudio → text input.

        Returns
        -------
        dict with keys:
            ``"type"``  – ``"audio"`` or ``"text"``
            ``"data"``  – WAV bytes (audio) or raw string (text fallback)
        """
        duration = duration or self.record_seconds

        # ── Backend 1: sounddevice (preferred on Windows) ────────────
        if _HAS_SOUNDDEVICE:
            try:
                print(f"\n🎙️  Listening for {duration} seconds …")
                audio_data = sd.rec(
                    int(Config.AUDIO_SAMPLE_RATE * duration),
                    samplerate=Config.AUDIO_SAMPLE_RATE,
                    channels=Config.AUDIO_CHANNELS,
                    dtype="int16",
                )
                sd.wait()  # Block until recording completes

                wav_bytes = self._numpy_to_wav(audio_data)
                print("✅  Audio captured (sounddevice).")
                return {"type": "audio", "data": wav_bytes}

            except (OSError, IOError, Exception) as exc:
                print(f"[WARN] sounddevice mic error ({exc}). Trying fallback…")

        # ── Backend 2: pyaudio ───────────────────────────────────────
        if _HAS_PYAUDIO:
            try:
                pa = pyaudio.PyAudio()
                stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=Config.AUDIO_CHANNELS,
                    rate=Config.AUDIO_SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=Config.AUDIO_CHUNK_SIZE,
                )
                print(f"\n🎙️  Listening for {duration} seconds …")
                frames: list[bytes] = []
                for _ in range(int(Config.AUDIO_SAMPLE_RATE / Config.AUDIO_CHUNK_SIZE * duration)):
                    data = stream.read(Config.AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                    frames.append(data)

                stream.stop_stream()
                stream.close()
                pa.terminate()

                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(Config.AUDIO_CHANNELS)
                    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(Config.AUDIO_SAMPLE_RATE)
                    wf.writeframes(b"".join(frames))

                print("✅  Audio captured (pyaudio).")
                return {"type": "audio", "data": wav_buffer.getvalue()}

            except (OSError, IOError) as exc:
                print(f"[WARN] PyAudio mic error ({exc}). Falling back to text.")

        # ── Backend 3: text console ──────────────────────────────────
        text = input("\n⌨️  No microphone — type your command: ").strip()
        return {"type": "text", "data": text}

    @staticmethod
    def _numpy_to_wav(audio_array: np.ndarray) -> bytes:
        """Convert a numpy int16 array to WAV bytes."""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(Config.AUDIO_CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(Config.AUDIO_SAMPLE_RATE)
            wf.writeframes(audio_array.tobytes())
        return wav_buffer.getvalue()

    # ── ElevenLabs TTS ───────────────────────────────────────────────
    def speak(self, text: str) -> None:
        """Speak *text* via ElevenLabs using raw PCM.
        
        Requires:
        - ELEVEN_API_KEY in .env (valid)
        - sounddevice installed
        - Internet connection to ElevenLabs API
        
        Raises exception if API key is invalid or service unavailable.
        """
        print(f"\n🔊  {text}")
        
        if not self._el_client:
            raise RuntimeError(
                "[ERROR] ElevenLabs TTS unavailable. Check:\n"
                "  1. Is ELEVEN_API_KEY set in .env?\n"
                "  2. Is it valid and not expired?\n"
                "  3. Is elevenlabs package installed (pip install elevenlabs)?"
            )
        
        if not _HAS_SOUNDDEVICE:
            raise RuntimeError(
                "[ERROR] sounddevice not available. Install via:\n"
                "  pip install sounddevice"
            )
        
        try:
            # Request raw PCM from ElevenLabs API
            audio_gen = self._el_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=Config.ELEVENLABS_MODEL,
                output_format="pcm_16000",
            )
            
            # Consume generator to bytes
            audio_bytes = b"".join(chunk for chunk in audio_gen)
            
            if not audio_bytes:
                raise RuntimeError("[ERROR] ElevenLabs returned empty audio - check API key validity")
            
            # Convert bytes to numpy array and play via sounddevice
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            sd.play(audio_array, samplerate=16000, blocking=True)
            
        except Exception as exc:
            # Re-raise with context
            error_msg = str(exc)
            if "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                raise RuntimeError(
                    f"[ERROR] ElevenLabs API key is invalid or expired: {exc}\n"
                    "Please verify ELEVEN_API_KEY in .env is correct."
                )
            else:
                raise RuntimeError(f"[ERROR] ElevenLabs TTS failed: {exc}")

    # ── Speech to Text (Decryption) ──────────────────────────────────
    def _transcribe_audio(self, audio_data: bytes) -> str:
        """Convert WAV audio bytes to text using Google Web Speech."""
        print("\n🔐  Decrypting signal (Speech-to-Text)...")

        # Google Web Speech (Free, via SpeechRecognition)
        try:
            recognizer = sr.Recognizer()
            
            # Adjust energy threshold for better detection
            recognizer.energy_threshold = 300  # Lower = more sensitive
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8  # Seconds of silence to consider phrase complete
            
            with sr.AudioFile(io.BytesIO(audio_data)) as source:
                # Adjust for ambient noise briefly
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.record(source)

            # Try Google Web Speech with language hint
            text = recognizer.recognize_google(audio, language="en-US")
            print(f"✅  Decryption (Google): \"{text}\"")
            return text
        except sr.UnknownValueError:
            print("❌  Decryption failed: Audio unintelligible.")
            print("   TIP: Speak clearly and say a valid target like 'pick the nut' or 'grab the skull'")
            return ""
        except sr.RequestError as e:
            print(f"[ERROR] Google Speech API error: {e}")
            print("   Check internet connection or try again.")
            return ""
        except Exception as e:
            print(f"[WARN] STT failed: {e}")
            return ""

    # ── Gemini Evaluation ────────────────────────────────────────────
    def process_command(
        self,
        command_text: str,
        visible_objects: list[str],
    ) -> dict[str, Any]:
        """Send the decrypted text command + context to Gemini.

        Parameters
        ----------
        command_text
            The transcribed text from the operator.
        visible_objects
            Objects the vision system currently sees.

        Returns
        -------
        dict  ``{"valid": bool, "target": str|None, "reason": str}``
        """
        fallback_invalid: dict[str, Any] = {
            "valid": False,
            "target": None,
            "reason": "Cannot evaluate.",
        }

        if not self._gemini_client:
            return fallback_invalid

        # Build the user-turn content parts
        context_text = (
            f"VISIBLE_OBJECTS: {json.dumps(visible_objects)}\n"
            "Evaluate the following operator command:"
        )

        parts: list[Any] = [context_text]

        if not command_text:
            return fallback_invalid

        parts.append(f'\nOperator said: "{command_text}"')

        for attempt in range(1, Config.GEMINI_MAX_RETRIES + 1):
            try:
                response = self._gemini_client.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents=parts,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=self._build_system_instruction(),
                        max_output_tokens=Config.GEMINI_MAX_OUTPUT_TOKENS,
                        temperature=Config.GEMINI_TEMPERATURE,
                        response_mime_type=Config.GEMINI_RESPONSE_MIME_TYPE,
                    ),
                )
                raw = response.text.strip()
                result = json.loads(raw)

                # Ensure schema integrity
                result.setdefault("valid", False)
                result.setdefault("target", None)
                result.setdefault("reason", "No reason provided.")
                return result

            except json.JSONDecodeError:
                print(f"[WARN] Gemini returned non-JSON: {response.text!r}")
                return fallback_invalid
            except Exception as exc:
                error_str = str(exc)
                # Check for 429 (Resource Exhausted) or 503 (Service Unavailable)
                if "429" in error_str or "503" in error_str:
                    if attempt < Config.GEMINI_MAX_RETRIES:
                        wait_time = Config.GEMINI_RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                        print(f"[WARN] Gemini API error {exc}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ERROR] Gemini call failed after {Config.GEMINI_MAX_RETRIES} attempts: {exc}")
                        return fallback_invalid
                else:
                    # Non-retriable error
                    print(f"[ERROR] Gemini call failed: {exc}")
                    return fallback_invalid

        return fallback_invalid

    # ── Convenience methods for Flask API ─────────────────────────────
    def listen(self, duration: int | None = None) -> str:
        """Record audio and transcribe to text. Returns transcribed text only."""
        user_input = self._record_audio(duration)

        if user_input["type"] == "audio":
            return self._transcribe_audio(user_input["data"])
        else:
            # It's already text (typed input)
            command_text = user_input["data"]
            print(f"⌨️  Manual Entry: \"{command_text}\"")
            return command_text

    def listen_and_evaluate(self, visible_objects: list[str]) -> dict[str, Any]:
        """Execute the full A → E interaction loop.

        State A : Receive *visible_objects* from the vision pipeline.
        State B : Announce visible objects via TTS.
        State C : Record operator audio (or text fallback).
        State D : Send to Gemini for dual-gate logic evaluation.
        State E : Speak result & return structured JSON.

        Parameters
        ----------
        visible_objects
            Objects currently detected by the vision system.

        Returns
        -------
        dict  ``{"valid": bool, "target": str|None, "reason": str}``
        """
        # ── State A: receive visible list (already the argument) ─────

        # ── State B: announce ────────────────────────────────────────
        obj_list_str = ", ".join(visible_objects) if visible_objects else "nothing"
        self.speak(
            f"Scanners active. I see {obj_list_str}. "
            "What is the salvage target?"
        )

        # ── State C: listen ──────────────────────────────────────────
        user_input = self._record_audio()

        # ── State C.5: decrypt (STT) ─────────────────────────────────
        if user_input["type"] == "audio":
            # Transcribe audio to text
            command_text = self._transcribe_audio(user_input["data"])
        else:
            # It's already text (typed input)
            command_text = user_input["data"]
            print(f"⌨️  Manual Entry: \"{command_text}\"")

        # ── State D: Gemini logic gate ───────────────────────────────
        result = self._evaluate_with_gemini(command_text, visible_objects)

        # ── State E: speak result & return ───────────────────────────
        if result.get("valid"):
            self.speak(f"Confirmed. Locking on to target: {result['target']}.")
        else:
            reason = result.get("reason", "Unknown rejection.")
            self.speak(f"Negative. {reason}")

        return result

    def _evaluate_with_gemini(
        self,
        command_text: str,
        visible_objects: list[str],
    ) -> dict[str, Any]:
        """Internal wrapper that returns result without speaking."""
        return self.process_command(command_text, visible_objects)


# Singleton instance
voice_service = VoiceService()