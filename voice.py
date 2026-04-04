import os, re
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

def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so TTS reads clean prose."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = text.replace('`', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

KOKORO_URL = "http://192.168.1.152:8800/tts"

def synthesize_speech(text: str) -> bytes:
    import subprocess, tempfile, os, requests
    text = _strip_markdown(text)
    try:
        resp = requests.post(KOKORO_URL, json={"text": text}, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 100:
            wav_path = tempfile.mktemp(suffix='.wav')
            mp3_path = tempfile.mktemp(suffix='.mp3')
            try:
                with open(wav_path, 'wb') as f:
                    f.write(resp.content)
                subprocess.run(['ffmpeg', '-y', '-i', wav_path, '-codec:a', 'libmp3lame', '-qscale:a', '2', mp3_path], capture_output=True, timeout=15)
                with open(mp3_path, 'rb') as f:
                    return f.read()
            finally:
                for p in [wav_path, mp3_path]:
                    try: os.unlink(p)
                    except: pass
    except Exception:
        pass
    # Piper fallback
    PIPER_MODEL = '/home/jes/models/piper/en_GB-jenny_dioco-medium.onnx'
    wav_path = tempfile.mktemp(suffix='.wav')
    mp3_path = tempfile.mktemp(suffix='.mp3')
    try:
        try:
            result = subprocess.run(['python3', '-m', 'piper', '--model', PIPER_MODEL, '--output_file', wav_path], input=text, capture_output=True, text=True, timeout=30)
            if result.returncode != 0: raise Exception(result.stderr)
        except Exception:
            result = subprocess.run(['/home/jes/control-plane/piper/piper', '--model', PIPER_MODEL, '--output_file', wav_path], input=text, capture_output=True, text=True, timeout=30)
            if result.returncode != 0: raise Exception(f'Piper failed: {result.stderr}')
        subprocess.run(['ffmpeg', '-y', '-i', wav_path, '-codec:a', 'libmp3lame', '-qscale:a', '2', mp3_path], capture_output=True, timeout=15)
        with open(mp3_path, 'rb') as f: audio_bytes = f.read()
        if not audio_bytes: raise Exception('Empty audio output')
        return audio_bytes
    finally:
        for p in [wav_path, mp3_path]:
            try: os.unlink(p)
            except: pass
