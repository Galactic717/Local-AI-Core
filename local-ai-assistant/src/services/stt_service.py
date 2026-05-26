"""
STT Service - Speech-to-Text FastAPI Microservice
Phase 2.3 - Local AI Assistant v1.6
"""

import os
import uuid
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
import requests

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config_loader import get_stt_config, get_service_url
from src.utils.logger import setup_logger
from src.utils.runtime_paths import bundled_or_writable_dir, ensure_writable_dir

# Configuration from YAML + env overrides
STT_CFG = get_stt_config()
SERVICE_PORT = STT_CFG["port"]
ORCHESTRATOR_URL = get_service_url("orchestrator")
DEVICE = STT_CFG["device"] if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = STT_CFG["compute_type"] if DEVICE == "cuda" else "float32"

# Point HuggingFace cache to our bundled models directory
_WHISPER_MODELS_DIR = bundled_or_writable_dir("models", "whisper")
os.environ.setdefault("HF_HOME", str(_WHISPER_MODELS_DIR))
os.environ.setdefault("HF_HUB_CACHE", str(_WHISPER_MODELS_DIR))

from faster_whisper import WhisperModel

# Paths
LOGS_DIR = ensure_writable_dir("logs")
TEMP_DIR = ensure_writable_dir("temp", "stt")

logger = setup_logger("stt_service", LOGS_DIR / "stt_service.log")

# Resolve model: try local cached snapshot first, fall back to model name
def _resolve_whisper_model(model_name: str) -> str:
    """Find cached faster-whisper model or return model name for download."""
    # faster-whisper uses guillaumekln org on HF
    _snapshot_dirs = sorted(_WHISPER_MODELS_DIR.glob("models--*--faster-whisper-*/snapshots/*"))
    if _snapshot_dirs:
        snapshot_path = str(_snapshot_dirs[-1])
        logger.info(f"Using cached Whisper model: {snapshot_path}")
        return snapshot_path
    logger.info(f"No cached model found, will use model name: {model_name}")
    return model_name

MODEL_PATH = _resolve_whisper_model(STT_CFG["model_name"])

app = FastAPI(title="STT Service", version="1.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None


def get_model():
    global model
    if model is None:
        logger.info(f"Loading Whisper model: {MODEL_PATH} ({DEVICE}, {COMPUTE_TYPE})")
        model = WhisperModel(
            MODEL_PATH,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            download_root=str(_WHISPER_MODELS_DIR),
        )
        logger.info("Whisper model loaded successfully")
    return model


@app.post("/v1/audio/transcriptions")
def transcribe(file: UploadFile = File(...), language: Optional[str] = Form(None)):
    request_id = str(uuid.uuid4())
    temp_path = TEMP_DIR / f"{request_id}_{file.filename}"

    try:
        # Request VRAM preparation
        try:
            requests.post(f"{ORCHESTRATOR_URL}/prepare/stt", timeout=30)
        except Exception as e:
            logger.warning(f"Orchestrator ping failed: {e}")

        with open(temp_path, "wb") as buffer:
            buffer.write(file.file.read())

        m = get_model()
        lang = language or STT_CFG["default_language"]
        segments, info = m.transcribe(
            str(temp_path),
            beam_size=STT_CFG["beam_size"],
            language=lang,
        )

        text = " ".join([s.text for s in segments]).strip()

        return {
            "text": text,
            "language": info.language,
            "duration": info.duration,
        }
    except Exception as e:
        logger.error(f"STT Error [{request_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE, "model": MODEL_PATH}


@app.post("/api/v1/unload")
def unload():
    global model
    model = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"status": "unloaded"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
