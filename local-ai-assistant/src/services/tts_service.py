"""
TTS Service - Text-to-Speech FastAPI Microservice
Phase 3.2 - Local AI Assistant v1.6

OpenAI-compatible endpoint for text-to-speech using Piper TTS.
Runs on CPU only with thread limiting to preserve resources for LLM.
"""

import os
import sys
import uuid
import time
import re
import wave
import struct
import io
from pathlib import Path
from typing import Optional, List

# ============================================
# CPU THREAD LIMITING (Must be set before imports)
# ============================================
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config_loader import get_tts_config
from src.utils.logger import setup_logger
from src.utils.runtime_paths import bundled_or_writable_dir, ensure_writable_dir

# ============================================
# CONFIGURATION & PATHS
# ============================================
TTS_CFG = get_tts_config()
SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", str(TTS_CFG["port"])))

MODELS_DIR = bundled_or_writable_dir("models", "piper")
LOGS_DIR = ensure_writable_dir("logs")
TEMP_DIR = ensure_writable_dir("temp", "tts")

logger = setup_logger("tts_service", LOGS_DIR / "tts_service.log")

# Voice mapping
VOICE_MAP = {
    "uk": "uk_UA-lada-x_low",
    "en": "en_US-lessac-medium",
    "uk_UA-lada-x_low": "uk_UA-lada-x_low",
    "en_US-lessac-medium": "en_US-lessac-medium",
}

# ============================================
# PIPER ENGINE (lazy loaded)
# ============================================
piper_synthesize_fn = None
piper_load_error = None


def _load_piper_engine():
    """Load the Piper synthesis function (lazy, thread-safe via module import)."""
    global piper_synthesize_fn, piper_load_error
    if piper_synthesize_fn is not None or piper_load_error is not None:
        return

    try:
        from piper.synthesize import synthesize
        piper_synthesize_fn = synthesize
        logger.info("Piper TTS engine loaded via library")
    except Exception as exc:
        piper_load_error = str(exc)
        logger.warning(f"Piper library unavailable: {exc}. Will use subprocess fallback.")


def _read_wav_data(wav_path: Path) -> tuple:
    """Read WAV file and return (sample_rate, raw_pcm_bytes)."""
    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        pcm_data = wf.readframes(n_frames)
    return sample_rate, n_channels, sampwidth, pcm_data


def _write_wav(file_obj, pcm_data: bytes, sample_rate: int = 22050,
               n_channels: int = 1, sampwidth: int = 2):
    """Write PCM data as a valid WAV file to file_obj."""
    with wave.open(file_obj, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)


def synthesize_with_subprocess(text: str, model_path: Path, length_scale: float) -> Optional[bytes]:
    """Fallback: synthesize using Piper subprocess."""
    temp_wav = TEMP_DIR / f"{uuid.uuid4()}.wav"
    try:
        cmd = [
            sys.executable, "-m", "piper",
            "--model", str(model_path),
            "--output_file", str(temp_wav),
            "--length_scale", str(length_scale),
        ]
        import subprocess
        process = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdin=subprocess.PIPE,
            capture_output=True,
            check=True,
            timeout=30,
        )
        if temp_wav.exists():
            _, _, _, pcm = _read_wav_data(temp_wav)
            return pcm
    except Exception as e:
        logger.error(f"Subprocess synthesis failed: {e}")
    finally:
        if temp_wav.exists():
            try:
                temp_wav.unlink()
            except OSError:
                pass
    return None


def synthesize_with_library(text: str, model_path: Path, length_scale: float) -> Optional[bytes]:
    """Synthesize using Piper library directly."""
    try:
        audio_generator = piper_synthesize_fn(
            text,
            model_path=str(model_path),
            length_scale=length_scale,
        )
        # Collect all audio chunks
        all_audio = b""
        for audio_chunk in audio_generator:
            all_audio += audio_chunk
        return all_audio if all_audio else None
    except Exception as e:
        logger.error(f"Library synthesis failed for '{text[:30]}': {e}")
        return None


def synthesize_sentence(text: str, model_path: Path, sample_rate: int,
                        length_scale: float) -> Optional[tuple]:
    """
    Synthesize a single sentence.
    Returns (pcm_bytes, sample_rate, channels, sampwidth) or None.
    """
    _load_piper_engine()

    if piper_synthesize_fn is not None:
        pcm = synthesize_with_library(text, model_path, length_scale)
        if pcm:
            return pcm, sample_rate, 1, 2
    else:
        result = synthesize_with_subprocess(text, model_path, length_scale)
        if result:
            return result, sample_rate, 1, 2

    return None


# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(
    title="Local AI TTS Service",
    description="OpenAI-compatible TTS using Piper (CPU)",
    version="1.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OpenAI_TTS_Request(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "uk"
    response_format: str = "wav"
    speed: float = 1.0


# ============================================
# TEXT SPLITTING
# ============================================
def split_text(text: str, max_len: int = 150) -> List[str]:
    """Splits text into sentences for low-latency synthesis."""
    if len(text) <= max_len:
        return [text]

    sentences = re.split(r'([.!?]+)', text)
    chunks = []
    current_chunk = ""

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i] + sentences[i + 1]
        if len(current_chunk) + len(sentence) <= max_len:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())
    elif not chunks and text:
        chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]

    return chunks


# ============================================
# ENDPOINTS
# ============================================
@app.post("/v1/audio/speech")
def speech(request: OpenAI_TTS_Request):
    """
    OpenAI-compatible speech synthesis endpoint.
    - v1.6: Piper library integration, proper WAV concatenation
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] TTS: voice={request.voice}, length={len(request.input)}, speed={request.speed}")

    max_len = TTS_CFG.get("max_text_length", 5000)
    if len(request.input) > max_len:
        raise HTTPException(status_code=400, detail=f"Input text too long (max {max_len} chars)")

    voice_key = VOICE_MAP.get(request.voice, "uk")
    model_path = MODELS_DIR / f"{voice_key}.onnx"

    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        raise HTTPException(status_code=404, detail=f"Voice model '{request.voice}' not found")

    sample_rate = TTS_CFG.get("sample_rate", 22050)
    length_scale = 1.0 / max(0.5, min(2.0, request.speed))

    start_time = time.time()
    chunks = split_text(request.input, max_len=150)
    logger.info(f"[{request_id}] Split into {len(chunks)} chunks")

    all_pcm = []
    for chunk in chunks:
        result = synthesize_sentence(chunk, model_path, sample_rate, length_scale)
        if result:
            pcm, _, _, _ = result
            all_pcm.append(pcm)

    if not all_pcm:
        raise HTTPException(status_code=500, detail="Failed to synthesize audio")

    elapsed = time.time() - start_time
    logger.info(f"[{request_id}] Synthesis complete in {elapsed:.2f}s")

    def iter_wav():
        combined_pcm = b"".join(all_pcm)
        buf = io.BytesIO()
        _write_wav(buf, combined_pcm, sample_rate)
        buf.seek(0)
        yield buf.read()

    return StreamingResponse(iter_wav(), media_type="audio/wav")


@app.get("/health")
def health():
    available_voices = [f.stem for f in MODELS_DIR.glob("*.onnx")]
    return JSONResponse(content={
        "status": "ok",
        "service": "Local AI TTS",
        "cpu_limit": {
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        },
        "available_voices": available_voices,
        "device": "cpu",
    })


@app.post("/api/v1/unload")
def unload():
    count = 0
    for f in TEMP_DIR.glob("*.wav"):
        try:
            f.unlink()
            count += 1
        except OSError:
            pass
    return {"status": "unloaded", "files_cleaned": count}


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info(f"Local AI TTS Service starting on port {SERVICE_PORT}...")
    logger.info(f"CPU Thread limit: {os.environ['OMP_NUM_THREADS']}")
    logger.info(f"Models directory: {MODELS_DIR}")
    logger.info("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT, log_level="warning")
