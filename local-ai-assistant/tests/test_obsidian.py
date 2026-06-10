import pytest
import os
import tempfile
from pathlib import Path
from src.services.obsidian_service import ObsidianService

def test_obsidian_service_creation_and_write():
    """Verify that ObsidianService can create and write to notes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = ObsidianService(tmpdir)
        
        # Test creating a note
        note_title = "TestNote"
        note_content = "This is a test note."
        path = service.create_note(note_title, note_content, folder="AI_Notes")
        
        assert path is not ""
        assert os.path.exists(path)
        
        # Verify content
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == note_content

def test_obsidian_service_read():
    """Verify that ObsidianService can read notes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Manually create a note
        target_dir = Path(tmpdir) / "Notes"
        target_dir.mkdir()
        with open(target_dir / "ReadTest.md", "w", encoding="utf-8") as f:
            f.write("Readable content")
            
        service = ObsidianService(tmpdir)
        content = service.read_note("ReadTest")
        assert content == "Readable content"
