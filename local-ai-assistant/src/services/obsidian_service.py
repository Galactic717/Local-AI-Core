# src/services/obsidian_service.py
import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("Obsidian-Service")

class ObsidianService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            logger.error(f"Vault path {vault_path} does not exist!")
            raise FileNotFoundError(f"Obsidian Vault not found at {vault_path}")

    def search_notes(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Шукає нотатки, що містять ключове слово."""
        results = []
        # Шукаємо всі .md файли
        md_files = list(self.vault_path.rglob("*.md"))
        
        count = 0
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query.lower() in content.lower() or query.lower() in file_path.name.lower():
                        results.append({
                            "title": file_path.stem,
                            "path": str(file_path),
                            "excerpt": content[:200] + "..."
                        })
                        count += 1
                        if count >= limit:
                            break
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        return results

    def read_note(self, note_title: str) -> Optional[str]:
        """Читає вміст нотатки за її назвою."""
        # Намагаємося знайти файл у всьому Vault
        files = list(self.vault_path.rglob(f"{note_title}.md"))
        if not files:
            return None
        
        try:
            with open(files[0], "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading note {note_title}: {e}")
            return None

    def create_note(self, title: str, content: str, folder: str = "AI_Notes") -> str:
        """Створює нову нотатку у вказаній папці."""
        target_dir = self.vault_path / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / f"{title}.md"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return str(file_path)
        except Exception as e:
            logger.error(f"Error creating note {title}: {e}")
            return ""

    def append_to_note(self, title: str, content: str) -> bool:
        """Додає текст у кінець існуючої нотатки."""
        files = list(self.vault_path.rglob(f"{title}.md"))
        if not files:
            return False
            
        try:
            with open(files[0], "a", encoding="utf-8") as f:
                f.write(f"\n\n--- Added by AI on {Path(__file__).stem} ---\n{content}")
            return True
        except Exception as e:
            logger.error(f"Error appending to note {title}: {e}")
            return False
