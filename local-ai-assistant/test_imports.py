# Test Service Imports

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("Testing service imports...")
print("=" * 60)

try:
    from src.core.orchestrator import orchestrator
    print("[OK] src.core.orchestrator")
except Exception as e:
    print(f"[FAIL] src.core.orchestrator: {e}")

try:
    from src.services.stt_service import app as stt_app
    print("[OK] src.services.stt_service")
except Exception as e:
    print(f"[FAIL] src.services.stt_service: {e}")

try:
    from src.services.tts_service import app as tts_app
    print("[OK] src.services.tts_service")
except Exception as e:
    print(f"[FAIL] src.services.tts_service: {e}")

try:
    from src.services.image_service import app as image_app
    print("[OK] src.services.image_service")
except Exception as e:
    print(f"[FAIL] src.services.image_service: {e}")

try:
    from src.services.brain_router import app as router_app
    print("[OK] src.services.brain_router")
except Exception as e:
    print(f"[FAIL] src.services.brain_router: {e}")

print("=" * 60)
print("Import test complete!")
