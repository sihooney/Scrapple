"""Quick test of Gemini + ElevenLabs APIs."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("1. Testing Gemini API...")
print("=" * 50)
try:
    from google import genai
    key = os.getenv("GEMINI_API_KEY", "")
    print(f"   Key: {key[:8]}...{key[-4:]}")
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello in 5 words or less.",
    )
    print(f"   ✅ Gemini response: {resp.text.strip()}")
except Exception as e:
    print(f"   ❌ Gemini FAILED: {e}")

print()
print("=" * 50)
print("2. Testing ElevenLabs API...")
print("=" * 50)
try:
    from elevenlabs import ElevenLabs
    key = os.getenv("ELEVEN_API_KEY", "")
    print(f"   Key: {key[:8]}...{key[-4:]}")
    el = ElevenLabs(api_key=key)
    audio_gen = el.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        text="Test.",
        model_id="eleven_monolingual_v1",
        output_format="pcm_16000",
    )
    audio_bytes = b"".join(chunk for chunk in audio_gen)
    print(f"   ✅ ElevenLabs returned {len(audio_bytes)} bytes of audio")
except Exception as e:
    print(f"   ❌ ElevenLabs FAILED: {e}")

print()
print("=" * 50)
print("3. Testing VoiceService import...")
print("=" * 50)
try:
    from voice_service import VoiceService
    print("   ✅ VoiceService imported (no singleton created)")
    svc = VoiceService()
    print(f"   ✅ VoiceService instance created")
    print(f"   Gemini client: {'✅' if svc._gemini_client else '❌ None'}")
    print(f"   ElevenLabs client: {'✅' if svc._el_client else '❌ None'}")
except Exception as e:
    print(f"   ❌ VoiceService FAILED: {e}")

print()
print("Done.")
