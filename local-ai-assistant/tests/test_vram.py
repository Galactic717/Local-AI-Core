import pytest
from src.core.orchestrator import VRAMOrchestrator

def test_vram_orchestrator_initialization():
    """Verify that the VRAM orchestrator initializes without crashing."""
    orchestrator = VRAMOrchestrator()
    assert orchestrator.get_vram_total_mb() > 0
    assert orchestrator.get_vram_free_mb() >= 0
    assert orchestrator.get_vram_percent() >= 0.0

def test_vram_status():
    """Verify the VRAM status dictionary format."""
    orchestrator = VRAMOrchestrator()
    status = orchestrator.get_vram_status()
    assert "total" in status
    assert "used" in status
    assert "free" in status
    assert "percent" in status
