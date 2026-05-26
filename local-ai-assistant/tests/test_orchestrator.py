"""
Basic test for Orchestrator
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_import_orchestrator():
    """Test that orchestrator can be imported"""
    from src.core.orchestrator import VRAMOrchestrator
    assert VRAMOrchestrator is not None

def test_orchestrator_init():
    """Test orchestrator initialization"""
    from src.core.orchestrator import VRAMOrchestrator

    # This will fail if NVML not available, but that's expected in test env
    try:
        orch = VRAMOrchestrator()
        assert orch.threshold_mb == 5200
    except Exception as e:
        # Expected in non-GPU environment
        assert "NVML" in str(e) or "CUDA" in str(e)

if __name__ == "__main__":
    test_import_orchestrator()
    test_orchestrator_init()
    print("✅ Basic tests passed")
