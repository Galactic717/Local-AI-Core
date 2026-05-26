import tempfile
import unittest
from pathlib import Path

from src.agent.local_agent import LocalAgentToolbox, ToolError, parse_agent_json


class LocalAgentToolboxTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "demo.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        self.toolbox = LocalAgentToolbox(workspace_roots=[self.root])

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_file_returns_numbered_excerpt(self):
        result = self.toolbox.read_file("demo.txt", start_line=2, end_line=3)
        self.assertEqual(result["start_line"], 2)
        self.assertIn("2: beta", result["content"])
        self.assertIn("3: gamma", result["content"])

    def test_replace_in_file_updates_text(self):
        result = self.toolbox.replace_in_file("demo.txt", "beta", "delta")
        self.assertEqual(result["replacements"], 1)
        self.assertIn("delta", (self.root / "demo.txt").read_text(encoding="utf-8"))

    def test_path_outside_workspace_is_rejected(self):
        with self.assertRaises(ToolError):
            self.toolbox.read_file(str(Path(self.root.parent) / "outside.txt"))


class ParseAgentJsonTests(unittest.TestCase):
    def test_parse_json_from_fence(self):
        parsed = parse_agent_json(
            """```json
            {"action":"final","response":"done"}
            ```"""
        )
        self.assertEqual(parsed["action"], "final")
        self.assertEqual(parsed["response"], "done")


if __name__ == "__main__":
    unittest.main()
