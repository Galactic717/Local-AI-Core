import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_ROOT = Path(os.getenv("LOCAL_AI_BUNDLED_ROOT", str(PROJECT_ROOT)))
RUNTIME_ROOT = Path(os.getenv("LOCAL_AI_RUNTIME_ROOT", str(BUNDLED_ROOT)))


def bundled_path(*parts: str) -> Path:
    return BUNDLED_ROOT.joinpath(*parts)


def writable_path(*parts: str) -> Path:
    return RUNTIME_ROOT.joinpath(*parts)


def ensure_writable_dir(*parts: str) -> Path:
    path = writable_path(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundled_or_writable_dir(*parts: str) -> Path:
    bundled = bundled_path(*parts)
    if bundled.exists():
        return bundled

    writable = writable_path(*parts)
    writable.mkdir(parents=True, exist_ok=True)
    return writable
