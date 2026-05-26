"""
VRAM Orchestrator - Central Coordinator for Model Management
Phase 1.4.2 - Local AI Assistant
"""

import sys
import time
import threading
import gc
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

import pynvml
import requests
import torch
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add project root to sys.path for internal imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logger
from src.utils.runtime_paths import bundled_path, ensure_writable_dir

# ==================== Configuration ====================
CONFIG_DIR = bundled_path("config")
LOGS_DIR = ensure_writable_dir("logs")

logger = setup_logger('orchestrator', LOGS_DIR / "orchestrator.log")

# Load config
with open(CONFIG_DIR / "ollama_config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# ==================== Data Models ====================

class ModelType(Enum):
    """Model types for priority management"""
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    IMAGE_GEN = "image_gen"

@dataclass
class ModelInfo:
    """Information about a loaded model"""
    name: str
    type: ModelType
    vram_mb: int
    loaded_at: float
    last_used: float

class PrepareRequest(BaseModel):
    model_name: str
    required_mb: int

# ==================== VRAM Orchestrator ====================

class VRAMOrchestrator:
    """
    Central coordinator for VRAM management.

    v1.2 Features:
    - Threading.Lock for race condition protection
    - Verify /api/ps after unload
    - Aggressive cleanup (torch + gc)
    - VRAM threshold = 5200 MB
    """

    def __init__(self):
        """Initialize orchestrator from config"""
        orch_config = config['orchestrator']
        services = config['services']

        self.threshold_mb = orch_config['vram_threshold_mb']
        self.critical_mb = orch_config['vram_critical_mb']
        self.warning_mb = orch_config['vram_warning_mb']
        self.cooldown_sec = orch_config['cooldown_sec']
        self.check_interval_sec = orch_config['check_interval_sec']
        self.verify_timeout_sec = orch_config['verify_timeout_sec']
        self.max_retries = orch_config['max_retries']
        self.service_timeout_sec = orch_config.get('service_timeout_sec', 30)
        self.image_timeout_sec = orch_config.get('image_timeout_sec', 60)

        # Service URLs
        self.ollama_url = services['ollama']
        self.stt_url = services['stt']
        self.tts_url = services['tts']
        self.image_url = services['image_gen']

        # Threading lock for race condition protection
        self.lock = threading.RLock()
        self.active_model_hint: Optional[str] = None

        # Initialize NVML
        try:
            pynvml.nvmlInit()
            self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = pynvml.nvmlDeviceGetName(self.gpu_handle)
            logger.info(f"NVML initialized: {gpu_name}")
        except Exception as e:
            logger.error(f"Failed to initialize NVML: {e}")
            raise

        # Track loaded models
        self.loaded_models: Dict[str, ModelInfo] = {}

        # Unload priority
        self.unload_priority = config['unload_priority']

        logger.info(f"Orchestrator initialized (threshold: {self.threshold_mb}MB)")

    # ==================== VRAM Monitoring ====================

    def get_vram_usage_mb(self) -> int:
        """Get current VRAM usage in MB"""
        try:
            info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            return info.used // (1024 ** 2)
        except Exception as e:
            logger.error(f"Error getting VRAM usage: {e}")
            return 0

    def get_vram_free_mb(self) -> int:
        """Get free VRAM in MB"""
        try:
            info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            return info.free // (1024 ** 2)
        except Exception as e:
            logger.error(f"Error getting free VRAM: {e}")
            return 0

    def get_vram_total_mb(self) -> int:
        """Get total VRAM in MB"""
        try:
            info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            return info.total // (1024 ** 2)
        except Exception as e:
            logger.error(f"Error getting total VRAM: {e}")
            return 6144

    def get_vram_percent(self) -> float:
        """Get VRAM usage as percentage"""
        used = self.get_vram_usage_mb()
        total = self.get_vram_total_mb()
        return (used / total) * 100 if total > 0 else 0

    def is_vram_available(self, required_mb: int) -> bool:
        """Check if enough VRAM is available"""
        current = self.get_vram_usage_mb()
        return (current + required_mb) <= self.threshold_mb

    def get_vram_status(self) -> Dict:
        """Get comprehensive VRAM status"""
        used = self.get_vram_usage_mb()
        free = self.get_vram_free_mb()
        total = self.get_vram_total_mb()
        percent = self.get_vram_percent()

        return {
            'used_mb': used,
            'free_mb': free,
            'total_mb': total,
            'percent': round(percent, 2),
            'threshold_mb': self.threshold_mb,
            'warning_mb': self.warning_mb,
            'critical_mb': self.critical_mb,
            'available': used < self.threshold_mb,
            'status': 'critical' if used > self.critical_mb else 'warning' if used > self.warning_mb else 'ok',
            'loaded_models': list(self.loaded_models.keys()),
            'active_model': self.active_model_hint or 'Idle'
        }

    # ==================== Cleanup Methods ====================

    def aggressive_cleanup(self):
        """Aggressive VRAM cleanup"""
        logger.info("Running aggressive cleanup...")

        # Clear PyTorch cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        # PATCH v1.3: Видалено gc.collect() звідси для уникнення зайвих фрізів
        # gc.collect()

        time.sleep(0.5)

    def verify_vram_freed(self, target_mb: int, timeout: int = None) -> bool:
        """
        Verify VRAM was freed to target level.
        Retry with aggressive cleanup if needed.
        """
        if timeout is None:
            timeout = self.verify_timeout_sec

        start_time = time.time()

        while time.time() - start_time < timeout:
            current = self.get_vram_usage_mb()

            if current <= target_mb or current <= 1500:
                logger.info(f"VRAM freed: {current}MB <= max({target_mb}MB, 1500MB)")
                return True

            # Aggressive cleanup
            self.aggressive_cleanup()
            time.sleep(0.5)

        current = self.get_vram_usage_mb()
        logger.warning(f"VRAM not fully freed: {current}MB > {target_mb}MB")
        return False

    # ==================== Model Registry ====================

    def register_model(self, name: str, model_type: ModelType, vram_mb: int):
        """Register a loaded model"""
        self.loaded_models[name] = ModelInfo(
            name=name,
            type=model_type,
            vram_mb=vram_mb,
            loaded_at=time.time(),
            last_used=time.time()
        )
        logger.info(f"Registered model: {name} ({vram_mb}MB)")

    def unregister_model(self, name: str):
        """Unregister an unloaded model"""
        if name in self.loaded_models:
            del self.loaded_models[name]
            logger.info(f"Unregistered model: {name}")

    def update_model_usage(self, name: str):
        """Update last used timestamp"""
        if name in self.loaded_models:
            self.loaded_models[name].last_used = time.time()

    def get_models_by_priority(self) -> List[str]:
        """Get loaded models sorted by unload priority"""
        models = list(self.loaded_models.values())
        models.sort(key=lambda m: (
            self.unload_priority.get(m.type.value, 99),
            m.last_used
        ))
        return [m.name for m in models]

    # ==================== Ollama Management ====================

    def get_loaded_ollama_models(self) -> List[Dict]:
        """Get currently loaded Ollama models"""
        try:
            response = requests.get(
                f"{self.ollama_url}/api/ps",
                timeout=self.service_timeout_sec,
            )
            if response.status_code == 200:
                return response.json().get('models', [])
        except Exception as e:
            logger.error(f"Error getting Ollama models: {e}")
        return []

    def estimate_model_vram_mb(self, model_name: str) -> int:
        """Best-effort VRAM estimate for registry bookkeeping."""
        name = model_name.lower()
        if "phi4-mini" in name:
            return 2500
        if "7b" in name:
            return 4200
        if "8b" in name:
            return 4600
        if "10b" in name:
            return 5200
        return 3500

    def sync_ollama_registry(self):
        """Mirror currently loaded Ollama models into the local registry."""
        loaded = self.get_loaded_ollama_models()
        loaded_names = {model.get('name') for model in loaded if model.get('name')}

        for model_name in loaded_names:
            if model_name not in self.loaded_models:
                self.register_model(
                    model_name,
                    ModelType.LLM,
                    self.estimate_model_vram_mb(model_name),
                )
            else:
                self.update_model_usage(model_name)

        stale_llms = [
            name for name, info in self.loaded_models.items()
            if info.type == ModelType.LLM and name not in loaded_names
        ]
        for model_name in stale_llms:
            self.unregister_model(model_name)

    def verify_ollama_unloaded(self, model_name: str, timeout: int = 5) -> bool:
        """Verify Ollama model is fully unloaded via /api/ps"""
        timeout = max(timeout, self.service_timeout_sec)
        start_time = time.time()

        while time.time() - start_time < timeout:
            models = self.get_loaded_ollama_models()

            if not any(m['name'] == model_name for m in models):
                logger.info(f"Verified unloaded: {model_name}")
                return True

            time.sleep(0.5)

        logger.warning(f"Model still loaded: {model_name}")
        return False

    def unload_ollama_model(self, model_name: str) -> bool:
        """Unload specific Ollama model with verification"""
        try:
            logger.info(f"Unloading Ollama model: {model_name}")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": model_name, "keep_alive": 0},
                timeout=self.service_timeout_sec
            )

            if response.status_code == 200:
                # Verify via /api/ps
                if self.verify_ollama_unloaded(model_name):
                    self.unregister_model(model_name)
                    if self.active_model_hint == model_name:
                        self.active_model_hint = None
                    self.aggressive_cleanup()
                    return True

        except Exception as e:
            logger.error(f"Error unloading Ollama model: {e}")

        return False

    def unload_all_ollama_models(self):
        """Unload all Ollama models"""
        self.sync_ollama_registry()
        models = self.get_loaded_ollama_models()

        for model in models:
            self.unload_ollama_model(model['name'])

        time.sleep(self.cooldown_sec)

    # ==================== Service Management ====================

    def unload_stt(self) -> bool:
        """Unload STT model"""
        try:
            logger.info("Unloading STT model")
            response = requests.post(
                f"{self.stt_url}/api/v1/unload",
                timeout=self.service_timeout_sec,
            )

            if response.status_code == 200:
                self.unregister_model('whisper')
                if self.active_model_hint == 'whisper':
                    self.active_model_hint = None
                self.aggressive_cleanup()
                return True

        except Exception as e:
            logger.error(f"Error unloading STT: {e}")

        return False

    def unload_tts(self) -> bool:
        """Unload TTS model"""
        try:
            logger.info("Unloading TTS model")
            response = requests.post(
                f"{self.tts_url}/api/v1/unload",
                timeout=self.service_timeout_sec,
            )

            if response.status_code == 200:
                self.unregister_model('piper')
                if self.active_model_hint == 'piper':
                    self.active_model_hint = None
                self.aggressive_cleanup()
                return True

        except Exception as e:
            logger.error(f"Error unloading TTS: {e}")

        return False

    def unload_image_gen(self) -> bool:
        """Unload image generation model"""
        try:
            logger.info("Unloading Image Gen model")
            response = requests.post(
                f"{self.image_url}/api/v1/unload",
                timeout=self.image_timeout_sec,
            )

            if response.status_code == 200:
                self.unregister_model('sd_turbo')
                if self.active_model_hint == 'sd_turbo':
                    self.active_model_hint = None
                self.aggressive_cleanup()
                return True

        except Exception as e:
            logger.error(f"Error unloading Image Gen: {e}")

        return False

    # ==================== Coordination ====================

    def unload_by_priority(self, required_mb: int):
        """Unload models by priority until enough VRAM available"""
        with self.lock:
            logger.info(f"Need {required_mb}MB, unloading by priority...")
            self.sync_ollama_registry()

            models_to_unload = self.get_models_by_priority()

            for model_name in models_to_unload:
                if self.is_vram_available(required_mb):
                    break

                model_info = self.loaded_models[model_name]

                if model_info.type == ModelType.LLM:
                    self.unload_ollama_model(model_name)
                elif model_info.type == ModelType.STT:
                    self.unload_stt()
                elif model_info.type == ModelType.TTS:
                    self.unload_tts()
                elif model_info.type == ModelType.IMAGE_GEN:
                    self.unload_image_gen()

                time.sleep(1)

            self.aggressive_cleanup()
            time.sleep(self.cooldown_sec)

    def unload_all(self):
        """Emergency: unload all models"""
        with self.lock:
            logger.warning("Emergency unload: unloading ALL models")

            self.unload_all_ollama_models()
            self.unload_stt()
            self.unload_tts()
            self.unload_image_gen()

            # PATCH v1.3: Оптимізований cleanup - тільки один gc.collect тут
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect() 
            
            time.sleep(self.cooldown_sec)

            self.loaded_models.clear()
            self.active_model_hint = None

            vram = self.get_vram_usage_mb()
            logger.info(f"All models unloaded. VRAM: {vram}MB")

    # ==================== Preparation Methods ====================

    def prepare_for_llm(self, model_name: str, required_mb: int):
        """Prepare VRAM for LLM loading"""
        with self.lock:
            logger.info(f"Preparing for LLM: {model_name} ({required_mb}MB)")
            self.sync_ollama_registry()
            self.active_model_hint = model_name

            current = self.get_vram_usage_mb()
            logger.info(f"Current VRAM: {current}MB")

            if not self.is_vram_available(required_mb):
                logger.info("Insufficient VRAM, unloading models...")
                self.unload_by_priority(required_mb)

            # Verify
            if not self.verify_vram_freed(self.threshold_mb - required_mb):
                raise Exception(f"Cannot free enough VRAM for {model_name}")

            final = self.get_vram_usage_mb()
            free = self.get_vram_free_mb()
            logger.info(f"VRAM ready: {final}MB used, {free}MB free")

    def prepare_for_stt(self, required_mb: int = 400):
        """Prepare VRAM for STT"""
        with self.lock:
            logger.info(f"Preparing for STT ({required_mb}MB)")
            self.active_model_hint = 'whisper'

            if not self.is_vram_available(required_mb):
                self.unload_by_priority(required_mb)

            if not self.verify_vram_freed(self.threshold_mb - required_mb):
                raise Exception("Cannot free enough VRAM for STT")

    def prepare_for_tts(self, required_mb: int = 100):
        """Prepare VRAM for TTS (CPU mode, minimal VRAM)"""
        logger.info(f"Preparing for TTS ({required_mb}MB, CPU mode)")
        self.active_model_hint = 'piper'
        # TTS runs on CPU, minimal prep needed

    def prepare_for_image_gen(self, required_mb: int = 3200):
        """Prepare VRAM for image generation"""
        with self.lock:
            logger.info(f"Preparing for Image Gen ({required_mb}MB)")
            self.active_model_hint = 'sd_turbo'

            # ALWAYS unload everything for image gen
            self.unload_all()
            self.active_model_hint = 'sd_turbo'

            # Verify
            if not self.verify_vram_freed(self.threshold_mb - required_mb):
                raise Exception("Insufficient VRAM for image gen")

            current = self.get_vram_usage_mb()
            free = self.get_vram_free_mb()
            logger.info(f"VRAM: {current}MB used, {free}MB free")

    # ==================== Monitoring Loop ====================

    def monitor_loop(self):
        """Continuous VRAM monitoring"""
        logger.info("Starting VRAM monitor loop")

        while True:
            try:
                status = self.get_vram_status()

                if status['used_mb'] > self.critical_mb:
                    logger.error(f"🚨 CRITICAL: {status['used_mb']}MB > {self.critical_mb}MB")
                    self.unload_by_priority(1000)
                elif status['used_mb'] > self.threshold_mb:
                    logger.warning(f"⚠️ WARNING: {status['used_mb']}MB > {self.threshold_mb}MB")
                    self.unload_by_priority(500)

                time.sleep(self.check_interval_sec)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(self.check_interval_sec)

    def __del__(self):
        """Cleanup on destruction"""
        try:
            pynvml.nvmlShutdown()
        except:
            pass

# ==================== Global Instance ====================

orchestrator = VRAMOrchestrator()

# ==================== FastAPI Application ====================

app = FastAPI(title="VRAM Orchestrator API", version="1.3")

# CORS Middleware for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PATCH v1.3: Змінено async def → def для уникнення блокування event loop (FastAPI auto-ThreadPool)

@app.get("/status")
def get_status():
    """Get current VRAM status"""
    return orchestrator.get_vram_status()

@app.post("/prepare/llm")
def prepare_llm(request: PrepareRequest):
    """Prepare for LLM loading"""
    try:
        orchestrator.prepare_for_llm(request.model_name, request.required_mb)
        return {"status": "ready", "vram": orchestrator.get_vram_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prepare/stt")
def prepare_stt():
    """Prepare for STT"""
    try:
        orchestrator.prepare_for_stt()
        return {"status": "ready", "vram": orchestrator.get_vram_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prepare/tts")
def prepare_tts():
    """Prepare for TTS"""
    try:
        orchestrator.prepare_for_tts()
        return {"status": "ready", "vram": orchestrator.get_vram_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prepare/image")
def prepare_image():
    """Prepare for image generation"""
    try:
        orchestrator.prepare_for_image_gen()
        return {"status": "ready", "vram": orchestrator.get_vram_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unload/all")
def unload_all():
    """Emergency: unload all models"""
    orchestrator.unload_all()
    return {"status": "unloaded", "vram": orchestrator.get_vram_status()}

@app.get("/health")
def health():
    """Health check"""
    status = orchestrator.get_vram_status()
    return {
        "status": "ok" if status['status'] != 'critical' else "degraded",
        "vram": status
    }

# ==================== Main ====================

if __name__ == "__main__":
    # Start monitoring in background
    monitor_thread = threading.Thread(target=orchestrator.monitor_loop, daemon=True)
    monitor_thread.start()

    # Start API server
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
