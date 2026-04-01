import os
from dotenv import dotenv_values

_model = None

def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("/home/jes/models/faster-whisper-tiny", device="cpu", compute_type="int8")
    return _model

def _load_api_key() -> str:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    cfg = dotenv_values(env_path)
    key = cfg.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY", "")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    return key

def transcribe_audio(audio_path: str) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio_path, beam_size=1, language="en")
    return " ".join(s.text.strip() for s in segments).strip()

def synthesize_speech(text: str) -> bytes:
    from elevenlabs.client import ElevenLabs
    api_key = _load_api_key()
    client = ElevenLabs(api_key=api_key)
    VOICE_ID = "RILOU7YmBhvwJGDGjNmP"
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=VOICE_ID,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128",
    )
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio)
    chunks = []
    for chunk in audio:
        if chunk:
            chunks.append(chunk)
    return b"".join(chunks)
