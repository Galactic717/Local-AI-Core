"""
Central configuration loader for all services.
Loads settings from YAML config files and environment variables.
"""

import os
from pathlib import Path

import yaml

from src.utils.runtime_paths import bundled_path, writable_path

PROJECT_ROOT = bundled_path()
CONFIG_DIR = bundled_path("config")


def load_yaml_config(filename: str) -> dict:
    """Load a YAML config file from the config directory."""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_env(key: str, default: str) -> str:
    """Get environment variable with default."""
    return os.getenv(key, default)


def get_env_int(key: str, default: int) -> int:
    """Get environment variable as int with default."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_float(key: str, default: float) -> float:
    """Get environment variable as float with default."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """Get environment variable as bool with default."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


# ─── Ollama Config ──────────────────────────────────────────

_ollama_cache: dict | None = None


def load_ollama_config() -> dict:
    """Load ollama_config.yaml (cached)."""
    global _ollama_cache
    if _ollama_cache is None:
        _ollama_cache = load_yaml_config("ollama_config.yaml")
    return _ollama_cache


def get_service_url(service_name: str) -> str:
    """Get service URL from config with env override."""
    env_key = f"{service_name.upper()}_URL"
    env_val = os.getenv(env_key)
    if env_val:
        return env_val
    cfg = load_ollama_config()
    services = cfg.get("services", {})
    return services.get(service_name, f"http://localhost:{get_default_port(service_name)}")


def get_default_port(service_name: str) -> int:
    """Get default port for a service from config or fallback."""
    port_map = {
        "ollama": 11434,
        "stt": 8001,
        "tts": 8002,
        "image_gen": 8003,
        "orchestrator": 8004,
    }
    cfg = load_ollama_config()
    services = cfg.get("services", {})
    url = services.get(service_name, "")
    if url:
        try:
            return int(url.rsplit(":", 1)[1])
        except (ValueError, IndexError):
            pass
    return port_map.get(service_name, 8000)


# ─── STT Config ─────────────────────────────────────────────

_stt_cache: dict | None = None


def load_stt_config() -> dict:
    """Load stt_config.yaml (cached)."""
    global _stt_cache
    if _stt_cache is None:
        _stt_cache = load_yaml_config("stt_config.yaml")
    return _stt_cache


def get_stt_config() -> dict:
    """Get merged STT config (YAML + env overrides)."""
    cfg = load_stt_config()
    return {
        "model_name": get_env("STT_MODEL", cfg.get("model", {}).get("name", "base")),
        "device": get_env("STT_DEVICE", cfg.get("model", {}).get("device", "cuda")),
        "compute_type": get_env("STT_COMPUTE_TYPE", cfg.get("model", {}).get("compute_type", "int8")),
        "port": get_env_int("STT_SERVICE_PORT", cfg.get("api", {}).get("port", 8001)),
        "max_audio_size_mb": get_env_int("STT_MAX_AUDIO_MB", cfg.get("api", {}).get("max_audio_size_mb", 25)),
        "default_language": get_env("STT_LANGUAGE", cfg.get("language", {}).get("default", "uk")),
        "beam_size": cfg.get("performance", {}).get("beam_size", 5),
        "max_vram_mb": cfg.get("vram", {}).get("max_usage_mb", 400),
        "unload_after_sec": cfg.get("vram", {}).get("unload_after_sec", 60),
    }


# ─── TTS Config ─────────────────────────────────────────────

_tts_cache: dict | None = None


def load_tts_config() -> dict:
    """Load tts_config.yaml (cached)."""
    global _tts_cache
    if _tts_cache is None:
        _tts_cache = load_yaml_config("tts_config.yaml")
    return _tts_cache


def get_tts_config() -> dict:
    """Get merged TTS config (YAML + env overrides)."""
    cfg = load_tts_config()
    return {
        "model_name": get_env("TTS_MODEL", cfg.get("model", {}).get("name", "uk_UA-lada-x_low")),
        "device": get_env("TTS_DEVICE", cfg.get("model", {}).get("device", "cpu")),
        "port": get_env_int("TTS_SERVICE_PORT", cfg.get("api", {}).get("port", 8002)),
        "max_text_length": get_env_int("TTS_MAX_TEXT", cfg.get("api", {}).get("max_text_length", 5000)),
        "output_format": get_env("TTS_FORMAT", cfg.get("api", {}).get("output_format", "wav")),
        "sample_rate": get_env_int("TTS_SAMPLE_RATE", cfg.get("api", {}).get("sample_rate", 22050)),
        "length_scale": get_env_float("TTS_LENGTH_SCALE", cfg.get("performance", {}).get("length_scale", 1.0)),
        "noise_scale": get_env_float("TTS_NOISE_SCALE", cfg.get("performance", {}).get("noise_scale", 0.667)),
        "noise_w": get_env_float("TTS_NOISE_W", cfg.get("performance", {}).get("noise_w", 0.8)),
        "sentence_silence": get_env_float("TTS_SILENCE", cfg.get("performance", {}).get("sentence_silence", 0.2)),
        "max_vram_mb": cfg.get("vram", {}).get("max_usage_mb", 100),
        "unload_after_sec": cfg.get("vram", {}).get("unload_after_sec", 120),
    }


# ─── Image Gen Config ───────────────────────────────────────

_image_cache: dict | None = None


def load_image_config() -> dict:
    """Load image_gen_config.yaml (cached)."""
    global _image_cache
    if _image_cache is None:
        _image_cache = load_yaml_config("image_gen_config.yaml")
    return _image_cache


def get_image_config() -> dict:
    """Get merged Image Gen config (YAML + env overrides)."""
    cfg = load_image_config()
    return {
        "model_name": get_env("SD_MODEL", cfg.get("model", {}).get("name", "stabilityai/sd-turbo")),
        "variant": get_env("SD_VARIANT", cfg.get("model", {}).get("variant", "fp16")),
        "device": get_env("SD_DEVICE", cfg.get("model", {}).get("device", "cuda")),
        "port": get_env_int("IMAGE_SERVICE_PORT", cfg.get("api", {}).get("port", 8003)),
        "max_prompt_length": get_env_int("SD_MAX_PROMPT", cfg.get("api", {}).get("max_prompt_length", 500)),
        "default_width": cfg.get("performance", {}).get("width", 512),
        "default_height": cfg.get("performance", {}).get("height", 512),
        "num_steps": cfg.get("performance", {}).get("num_inference_steps", 1),
        "guidance_scale": cfg.get("performance", {}).get("guidance_scale", 0.0),
        "enable_attention_slicing": cfg.get("performance", {}).get("enable_attention_slicing", True),
        "enable_vae_slicing": cfg.get("performance", {}).get("enable_vae_slicing", True),
        "max_vram_mb": cfg.get("vram", {}).get("max_usage_mb", 3200),
        "unload_immediately": cfg.get("vram", {}).get("unload_immediately", True),
        "force_cleanup": cfg.get("vram", {}).get("force_cleanup", True),
    }


# ─── Services Config (combined) ─────────────────────────────

_services_cache: dict | None = None


def load_services_config() -> dict:
    """Load services_config.yaml if it exists, otherwise build from ollama_config."""
    global _services_cache
    if _services_cache is None:
        svc_cfg = load_yaml_config("services_config.yaml")
        if svc_cfg:
            _services_cache = svc_cfg
        else:
            ollama_cfg = load_ollama_config()
            _services_cache = {
                "urls": ollama_cfg.get("services", {}),
                "ports": {
                    name: get_default_port(name)
                    for name in ["ollama", "stt", "tts", "image_gen", "orchestrator"]
                },
            }
    return _services_cache


# ─── Logging Config ─────────────────────────────────────────

_logging_cache: dict | None = None


def load_logging_config() -> dict:
    """Load logging_config.yaml if it exists, otherwise build defaults."""
    global _logging_cache
    if _logging_cache is None:
        log_cfg = load_yaml_config("logging_config.yaml")
        if log_cfg:
            _logging_cache = log_cfg
        else:
            _logging_cache = {
                "level": get_env("LOG_LEVEL", "INFO"),
                "format": get_env("LOG_FORMAT", "json"),
                "rotation": get_env("LOG_ROTATION", "10MB"),
                "logs_dir": str(writable_path("logs")),
            }
    return _logging_cache
