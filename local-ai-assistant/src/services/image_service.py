"""
Image Generation Service - Stable Diffusion Turbo FastAPI Microservice
Phase 4.2 - Local AI Assistant v1.6
"""

import base64
import os
import sys
import threading
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config_loader import get_image_config, get_service_url
from src.utils.logger import setup_logger
from src.utils.runtime_paths import bundled_or_writable_dir, ensure_writable_dir

# Configuration from YAML + env overrides
img_cfg = get_image_config()
SERVICE_PORT = int(os.getenv("IMAGE_SERVICE_PORT", str(img_cfg["port"])))
ORCHESTRATOR_URL = get_service_url("orchestrator")

# Resolve model path: env > cached snapshot > hub name
ENV_MODEL_PATH = os.getenv("SD_TURBO_MODEL_PATH")
if ENV_MODEL_PATH:
    MODEL_ID = ENV_MODEL_PATH
else:
    _models_dir = bundled_or_writable_dir("models", "sd_turbo")
    _snapshot_dirs = sorted(_models_dir.glob("models--stabilityai--sd-turbo/snapshots/*"))
    if _snapshot_dirs:
        MODEL_ID = str(_snapshot_dirs[-1])
    else:
        MODEL_ID = img_cfg["model_name"]

PIPELINE_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ORCHESTRATOR_TIMEOUT_SEC = 30

LOGS_DIR = ensure_writable_dir("logs")

logger = setup_logger("image_gen", LOGS_DIR / "image_gen_service.log")

app = FastAPI(title="Image Gen Service", version="1.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512
    steps: int = 1
    seed: Optional[int] = None


pipe = None
pipeline_lock = threading.Lock()


def unload_pipeline():
    global pipe
    pipe = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def ensure_numpy_runtime():
    import numpy as np

    major = int(np.__version__.split(".", maxsplit=1)[0])
    if major >= 2:
        raise RuntimeError(
            f"Unsupported NumPy {np.__version__}. Use numpy<2.0.0 for SD Turbo on Windows."
        )


def get_pipeline():
    global pipe
    if pipe is None:
        ensure_numpy_runtime()
        try:
            from diffusers import AutoPipelineForText2Image
        except Exception as exc:
            raise RuntimeError(
                "Diffusers failed to import. Check diffusers/transformers compatibility."
            ) from exc

        logger.info(f"Loading SD Turbo pipeline from {MODEL_ID}")
        try:
            pipeline_kwargs = {
                "torch_dtype": torch.float16 if PIPELINE_DEVICE == "cuda" else torch.float32,
                "local_files_only": True,
            }
            if PIPELINE_DEVICE == "cuda":
                pipeline_kwargs["variant"] = "fp16"

            pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, **pipeline_kwargs)
        except Exception as exc:
            if "Numpy is not available" in str(exc):
                raise RuntimeError(
                    "SD Turbo could not initialize: NumPy unavailable. "
                    "Pin numpy==1.26.4 and reinstall the environment."
                ) from exc
            if "local_files_only" in str(exc):
                logger.warning(f"Local model not found at {MODEL_ID}, trying hub download...")
                pipeline_kwargs["local_files_only"] = False
                pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, **pipeline_kwargs)
            else:
                raise

        pipe.to(PIPELINE_DEVICE)

        if img_cfg.get("enable_attention_slicing", True):
            pipe.enable_attention_slicing()
        if img_cfg.get("enable_vae_slicing", True):
            pipe.enable_vae_slicing()

        logger.info("SD Turbo pipeline loaded successfully")
    return pipe


@app.post("/api/v1/generate")
def generate(request: GenerateRequest):
    request_id = str(uuid.uuid4())
    generator = None
    if request.seed is not None:
        generator = torch.Generator(device=PIPELINE_DEVICE).manual_seed(request.seed)

    width = request.width if request.width > 0 else img_cfg.get("default_width", 512)
    height = request.height if request.height > 0 else img_cfg.get("default_height", 512)
    steps = request.steps if request.steps > 0 else img_cfg.get("num_steps", 1)

    try:
        try:
            requests.post(
                f"{ORCHESTRATOR_URL}/prepare/image",
                timeout=ORCHESTRATOR_TIMEOUT_SEC,
            )
        except Exception as exc:
            logger.warning(f"[{request_id}] Orchestrator preparation failed: {exc}")

        with pipeline_lock:
            pipeline = get_pipeline()
            result = pipeline(
                prompt=request.prompt,
                num_inference_steps=steps,
                guidance_scale=img_cfg.get("guidance_scale", 0.0),
                width=width,
                height=height,
                generator=generator,
            )
            image = result.images[0]

            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return {"image": base64.b64encode(buffered.getvalue()).decode()}
    except Exception as exc:
        logger.error(f"[{request_id}] Error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if img_cfg.get("unload_immediately", True):
            with pipeline_lock:
                unload_pipeline()


@app.get("/health")
def health():
    return {"status": "ok", "device": PIPELINE_DEVICE, "model": MODEL_ID}


@app.post("/api/v1/unload")
def unload():
    with pipeline_lock:
        unload_pipeline()
    return {"status": "unloaded"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
