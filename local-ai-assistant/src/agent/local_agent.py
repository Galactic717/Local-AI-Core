"""
Local agent runtime with tool use, file editing, shell commands, and web access.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

from src.utils.config_loader import get_service_url, load_services_config
from src.utils.logger import setup_logger
from src.utils.runtime_paths import bundled_path, ensure_writable_dir

LOGS_DIR = ensure_writable_dir("logs")
DATA_DIR = ensure_writable_dir("data")

logger = setup_logger("local_agent", LOGS_DIR / "local_agent.log")

OLLAMA_URL = get_service_url("ollama")
ORCHESTRATOR_URL = get_service_url("orchestrator")
MODEL_REQUIREMENTS_MB = load_services_config().get("model_requirements_mb", {})

DEFAULT_MAX_STEPS = int(os.getenv("LOCAL_AI_AGENT_MAX_STEPS", "6"))
DEFAULT_COMMAND_TIMEOUT_SEC = int(os.getenv("LOCAL_AI_COMMAND_TIMEOUT_SEC", "20"))
MAX_TOOL_OUTPUT_CHARS = int(os.getenv("LOCAL_AI_MAX_TOOL_OUTPUT_CHARS", "12000"))
MAX_HISTORY_MESSAGES = int(os.getenv("LOCAL_AI_MAX_HISTORY_MESSAGES", "12"))
MEMORY_FILE = DATA_DIR / "agent_memory.md"


class ToolError(RuntimeError):
    """Raised when a tool cannot complete safely or successfully."""


@dataclass
class ToolEvent:
    type: str
    tool: str
    status: str
    summary: str


@dataclass
class AgentRunResult:
    model: str
    response: str
    events: List[Dict[str, str]]


def _truncate_text(value: str, limit: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}\n\n[truncated {len(value) - limit} chars]"


def _clean_html(value: str) -> str:
    without_scripts = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.IGNORECASE)
    without_styles = re.sub(r"<style[\s\S]*?</style>", " ", without_scripts, flags=re.IGNORECASE)
    text_only = re.sub(r"<[^>]+>", " ", without_styles)
    compact = re.sub(r"\s+", " ", html.unescape(text_only))
    return compact.strip()


def _infer_workspace_roots() -> List[Path]:
    env_roots = os.getenv("LOCAL_AI_WORKSPACE_ROOTS", "").strip()
    raw_roots: List[str] = [part for part in env_roots.split(os.pathsep) if part] if env_roots else []

    if not raw_roots:
        bundled_root = bundled_path()
        raw_roots = [str(bundled_root.parent if bundled_root.name == "local-ai-assistant" else bundled_root)]

    roots: List[Path] = []
    seen: set[str] = set()
    for raw_root in raw_roots:
        resolved = Path(raw_root).resolve()
        key = str(resolved).lower()
        if resolved.exists() and key not in seen:
            seen.add(key)
            roots.append(resolved)

    if not roots:
        fallback = bundled_path().resolve()
        roots.append(fallback)

    return roots


def parse_agent_json(raw_content: str) -> Dict[str, Any]:
    """Parse the model output into an action JSON object."""
    content = raw_content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content, flags=re.IGNORECASE).strip()
        if content.endswith("```"):
            content = content[:-3].strip()

    for candidate in (content,):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                parsed.setdefault("args", {})
                return parsed
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise ValueError(f"Model did not return JSON: {raw_content[:200]}")

    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON action must be an object.")
    parsed.setdefault("args", {})
    return parsed


class LocalAgentToolbox:
    """Runtime toolbox available to the local agent."""

    def __init__(self, workspace_roots: Optional[List[Path]] = None):
        roots = workspace_roots or _infer_workspace_roots()
        self.workspace_roots = [root.resolve() for root in roots]
        self.primary_root = self.workspace_roots[0]
        self.memory_file = MEMORY_FILE

    def tool_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_roots",
                "description": "List allowed workspace roots.",
                "args": {},
            },
            {
                "name": "list_files",
                "description": "List files or directories inside a workspace root.",
                "args": {"path": "string", "recursive": "bool", "max_entries": "int"},
            },
            {
                "name": "read_file",
                "description": "Read a text file with line numbers.",
                "args": {"path": "string", "start_line": "int", "end_line": "int"},
            },
            {
                "name": "search_files",
                "description": "Search text inside files.",
                "args": {
                    "query": "string",
                    "path": "string",
                    "glob": "string",
                    "case_sensitive": "bool",
                    "max_results": "int",
                },
            },
            {
                "name": "write_file",
                "description": "Write or append text to a file.",
                "args": {"path": "string", "content": "string", "append": "bool"},
            },
            {
                "name": "replace_in_file",
                "description": "Replace exact text in a file.",
                "args": {
                    "path": "string",
                    "find_text": "string",
                    "replace_text": "string",
                    "count": "int",
                },
            },
            {
                "name": "run_command",
                "description": "Run a PowerShell command in a workspace directory.",
                "args": {"command": "string", "cwd": "string", "timeout_sec": "int"},
            },
            {
                "name": "web_search",
                "description": "Search the web for fresh information.",
                "args": {"query": "string", "limit": "int"},
            },
            {
                "name": "fetch_url",
                "description": "Fetch and summarize the text content of a URL.",
                "args": {"url": "string", "max_chars": "int"},
            },
            {
                "name": "read_memory",
                "description": "Read saved long-term notes.",
                "args": {},
            },
            {
                "name": "remember_note",
                "description": "Save a durable note to local memory.",
                "args": {"note": "string"},
            },
        ]

    def available_tool_names(self) -> List[str]:
        return [tool["name"] for tool in self.tool_specs()]

    def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        handler = getattr(self, tool_name, None)
        if handler is None or not callable(handler):
            raise ToolError(f"Unknown tool: {tool_name}")

        result = handler(**args)
        if not isinstance(result, dict):
            result = {"result": result}
        result["ok"] = True
        result["tool"] = tool_name
        return result

    def summarize(self, tool_name: str, payload: Dict[str, Any], ok: bool) -> str:
        if not ok:
            return f"{tool_name} failed: {payload.get('error', 'unknown error')}"

        if tool_name == "list_roots":
            return f"Workspace roots: {len(payload.get('roots', []))}"
        if tool_name == "list_files":
            return f"Listed {len(payload.get('entries', []))} entries in {payload.get('path', '.')}"
        if tool_name == "read_file":
            return f"Read {payload.get('path')} lines {payload.get('start_line')}-{payload.get('end_line')}"
        if tool_name == "search_files":
            return f"Found {len(payload.get('matches', []))} matches for {payload.get('query')!r}"
        if tool_name == "write_file":
            return f"Wrote {payload.get('path')}"
        if tool_name == "replace_in_file":
            return f"Updated {payload.get('path')} with {payload.get('replacements')} replacements"
        if tool_name == "run_command":
            return f"Command exited with code {payload.get('exit_code')} in {payload.get('cwd')}"
        if tool_name == "web_search":
            return f"Found {len(payload.get('results', []))} web results"
        if tool_name == "fetch_url":
            return f"Fetched {payload.get('url')}"
        if tool_name == "read_memory":
            return "Read local memory"
        if tool_name == "remember_note":
            return "Saved note to local memory"
        return f"Completed {tool_name}"

    def list_roots(self) -> Dict[str, Any]:
        return {"roots": [str(root) for root in self.workspace_roots]}

    def _resolve_path(self, raw_path: str = ".", allow_missing: bool = False) -> Path:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = self.primary_root / candidate

        resolved = candidate.resolve(strict=False)
        if not any(self._is_within(resolved, root) for root in self.workspace_roots):
            raise ToolError(f"Path is outside allowed workspace roots: {raw_path}")
        if not allow_missing and not resolved.exists():
            raise ToolError(f"Path does not exist: {raw_path}")
        return resolved

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _display_path(self, path: Path) -> str:
        for root in self.workspace_roots:
            try:
                return str(path.relative_to(root))
            except ValueError:
                continue
        return str(path)

    def list_files(self, path: str = ".", recursive: bool = False, max_entries: int = 200) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if target.is_file():
            return {
                "path": self._display_path(target),
                "entries": [
                    {
                        "path": self._display_path(target),
                        "type": "file",
                        "size_bytes": target.stat().st_size,
                    }
                ],
                "truncated": False,
            }

        iterator: Iterable[Path] = target.rglob("*") if recursive else target.iterdir()
        entries: List[Dict[str, Any]] = []
        truncated = False

        for item in iterator:
            entries.append(
                {
                    "path": self._display_path(item),
                    "type": "dir" if item.is_dir() else "file",
                    "size_bytes": item.stat().st_size if item.is_file() else 0,
                }
            )
            if len(entries) >= max_entries:
                truncated = True
                break

        entries.sort(key=lambda entry: (entry["type"] != "dir", entry["path"].lower()))
        return {
            "path": self._display_path(target),
            "entries": entries,
            "truncated": truncated,
        }

    def read_file(self, path: str, start_line: int = 1, end_line: int = 200) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if not target.is_file():
            raise ToolError(f"Not a file: {path}")

        content = target.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        total_lines = len(lines)
        start = max(1, start_line)
        end = max(start, min(end_line, total_lines if total_lines else 1))
        excerpt = [f"{line_no:4}: {lines[line_no - 1]}" for line_no in range(start, end + 1) if line_no - 1 < total_lines]

        return {
            "path": self._display_path(target),
            "start_line": start,
            "end_line": end,
            "total_lines": total_lines,
            "content": _truncate_text("\n".join(excerpt)),
        }

    def search_files(
        self,
        query: str,
        path: str = ".",
        glob: str = "*",
        case_sensitive: bool = False,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        target = self._resolve_path(path)
        files = [target] if target.is_file() else list(target.rglob(glob))
        needle = query if case_sensitive else query.lower()
        matches: List[Dict[str, Any]] = []
        truncated = False

        for file_path in files:
            if not file_path.is_file():
                continue
            try:
                if file_path.stat().st_size > 1_000_000:
                    continue
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for line_no, line in enumerate(text.splitlines(), start=1):
                haystack = line if case_sensitive else line.lower()
                if needle in haystack:
                    matches.append(
                        {
                            "path": self._display_path(file_path),
                            "line": line_no,
                            "content": line.strip(),
                        }
                    )
                    if len(matches) >= max_results:
                        truncated = True
                        break
            if truncated:
                break

        return {
            "query": query,
            "matches": matches,
            "truncated": truncated,
        }

    def write_file(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        target = self._resolve_path(path, allow_missing=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(target, mode, encoding="utf-8", newline="") as handle:
            handle.write(content)

        return {
            "path": self._display_path(target),
            "bytes_written": len(content.encode("utf-8")),
            "append": append,
        }

    def replace_in_file(self, path: str, find_text: str, replace_text: str, count: int = 1) -> Dict[str, Any]:
        if not find_text:
            raise ToolError("find_text must not be empty")

        target = self._resolve_path(path)
        original = target.read_text(encoding="utf-8", errors="replace")
        replacements = original.count(find_text) if count <= 0 else min(original.count(find_text), count)
        if replacements == 0:
            raise ToolError(f"Text not found in {path}")

        updated = original.replace(find_text, replace_text, count if count > 0 else original.count(find_text))
        target.write_text(updated, encoding="utf-8", newline="")

        return {
            "path": self._display_path(target),
            "replacements": replacements,
        }

    def run_command(self, command: str, cwd: str = ".", timeout_sec: int = DEFAULT_COMMAND_TIMEOUT_SEC) -> Dict[str, Any]:
        working_dir = self._resolve_path(cwd)
        if not working_dir.is_dir():
            raise ToolError(f"cwd is not a directory: {cwd}")

        try:
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=str(working_dir),
                capture_output=True,
                text=True,
                timeout=max(1, timeout_sec),
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            return {
                "cwd": self._display_path(working_dir),
                "command": command,
                "exit_code": None,
                "timed_out": True,
                "stdout": _truncate_text(stdout),
                "stderr": _truncate_text(stderr),
            }

        return {
            "cwd": self._display_path(working_dir),
            "command": command,
            "exit_code": completed.returncode,
            "timed_out": False,
            "stdout": _truncate_text(completed.stdout),
            "stderr": _truncate_text(completed.stderr),
        }

    def web_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        response.raise_for_status()

        results: List[Dict[str, str]] = []
        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )

        for match in pattern.finditer(response.text):
            href = html.unescape(match.group("href"))
            if "duckduckgo.com/l/?" in href:
                parsed = urlparse(href)
                href = unquote(parse_qs(parsed.query).get("uddg", [href])[0])
            title = re.sub(r"\s+", " ", _clean_html(match.group("title")))
            if title and href:
                results.append({"title": title, "url": href})
            if len(results) >= max(1, limit):
                break

        return {
            "query": query,
            "results": results,
        }

    def fetch_url(self, url: str, max_chars: int = 5000) -> Dict[str, Any]:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        text = response.text
        content_type = response.headers.get("content-type", "")
        if "html" in content_type.lower():
            text = _clean_html(text)

        if len(text.strip()) < 200 and response.headers.get("content-type", "").lower().startswith("text/html"):
            fallback_url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"
            fallback = requests.get(fallback_url, headers=headers, timeout=20)
            if fallback.ok and fallback.text.strip():
                text = fallback.text

        return {
            "url": response.url,
            "status_code": response.status_code,
            "content": _truncate_text(text.strip(), max_chars),
        }

    def read_memory(self) -> Dict[str, Any]:
        if not self.memory_file.exists():
            return {"content": "", "exists": False}

        return {
            "content": _truncate_text(self.memory_file.read_text(encoding="utf-8", errors="replace"), 8000),
            "exists": True,
        }

    def remember_note(self, note: str) -> Dict[str, Any]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.memory_file, "a", encoding="utf-8", newline="") as handle:
            handle.write(f"- [{timestamp}] {note.strip()}\n")

        return {"saved": True, "path": str(self.memory_file)}


def _prepare_model(model_name: str) -> None:
    required_mb = MODEL_REQUIREMENTS_MB.get(model_name, 3500)
    try:
        requests.post(
            f"{ORCHESTRATOR_URL}/prepare/llm",
            json={"model_name": model_name, "required_mb": required_mb},
            timeout=20,
        ).raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Orchestrator prepare failed for %s: %s", model_name, exc)


def _call_ollama(model_name: str, messages: List[Dict[str, str]]) -> str:
    _prepare_model(model_name)
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 8192},
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("message", {}).get("content", "").strip()


def _memory_hint() -> str:
    if not MEMORY_FILE.exists():
        return "No saved long-term notes yet."
    content = MEMORY_FILE.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        return "No saved long-term notes yet."
    return _truncate_text(content, 2000)


def _build_system_prompt(toolbox: LocalAgentToolbox) -> str:
    tool_lines = []
    for tool in toolbox.tool_specs():
        arg_text = ", ".join(f"{key}: {value}" for key, value in tool["args"].items()) or "no args"
        tool_lines.append(f"- {tool['name']}: {tool['description']} Args: {arg_text}.")

    roots = "\n".join(f"- {root}" for root in toolbox.workspace_roots)
    tools_text = "\n".join(tool_lines)

    return (
        "You are an elite Senior Software Engineer and autonomous AI agent.\n"
        "You have full access to the user's local filesystem, terminal, and web search.\n"
        "Behaviors:\n"
        "- Think step-by-step. Break complex tasks into small, verifiable steps.\n"
        "- Read files first to understand the context, then plan, then write code.\n"
        "- ALWAYS verify your code changes by running tests or scripts if appropriate.\n"
        "- Write clean, robust, production-grade code.\n"
        "- Never claim you ran a command or changed a file unless you successfully used the tool.\n"
        "- Answer the user in Ukrainian if they write in Ukrainian, but your internal logic, commands, and code MUST remain in English.\n"
        "- ONLY use one tool at a time.\n"
        "- Do NOT use markdown code blocks for your JSON output.\n\n"
        "Allowed workspace roots:\n"
        f"{roots}\n\n"
        "Saved long-term notes:\n"
        f"{_memory_hint()}\n\n"
        "Available tools:\n"
        f"{tools_text}\n\n"
        "Return ONLY a JSON object in this format to call a tool:\n"
        '{"action":"read_file","args":{"path":"src/App.tsx","start_line":1,"end_line":50},"reason":"Reading file to understand context"}\n'
        "To provide your final answer to the user:\n"
        '{"action":"final","response":"Your detailed response here."}'
    )


def _normalize_history(messages: List[dict]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for message in messages[-MAX_HISTORY_MESSAGES:]:
        role = str(message.get("role", "user"))
        content = message.get("content", "")
        if isinstance(content, list):
            content = "\n".join(str(part) for part in content)
        normalized.append({"role": role, "content": str(content)})
    return normalized


def run_agent_session(
    messages: List[dict],
    model_name: str,
    max_steps: int = DEFAULT_MAX_STEPS,
    toolbox: Optional[LocalAgentToolbox] = None,
) -> AgentRunResult:
    toolbox = toolbox or LocalAgentToolbox()
    conversation = [{"role": "system", "content": _build_system_prompt(toolbox)}, *_normalize_history(messages)]
    events: List[Dict[str, str]] = []

    for step in range(max_steps):
        raw_reply = _call_ollama(model_name, conversation)
        logger.info("Agent step %s using model %s", step + 1, model_name)

        try:
            action_payload = parse_agent_json(raw_reply)
        except Exception as exc:
            conversation.extend(
                [
                    {"role": "assistant", "content": raw_reply},
                    {
                        "role": "user",
                        "content": (
                            "Your previous reply was not valid JSON. "
                            "Reply with JSON only using either action=final or a tool name."
                        ),
                    },
                ]
            )
            logger.warning("Agent returned invalid JSON: %s", exc)
            continue

        action_name = str(action_payload.get("action", "")).strip()
        args = action_payload.get("args", {}) or {}

        if action_name == "final":
            response = str(action_payload.get("response", "")).strip()
            if not response:
                response = "Task complete."
            return AgentRunResult(model=model_name, response=response, events=events)

        if action_name not in toolbox.available_tool_names():
            conversation.extend(
                [
                    {"role": "assistant", "content": raw_reply},
                    {
                        "role": "user",
                        "content": (
                            f"Unknown action '{action_name}'. Use one of: "
                            f"{', '.join(toolbox.available_tool_names())}, or final."
                        ),
                    },
                ]
            )
            continue

        try:
            result = toolbox.execute(action_name, args if isinstance(args, dict) else {})
            event = ToolEvent(
                type="tool",
                tool=action_name,
                status="ok",
                summary=toolbox.summarize(action_name, result, ok=True),
            )
            tool_result_text = json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            error_payload = {"ok": False, "tool": action_name, "error": str(exc)}
            event = ToolEvent(
                type="tool",
                tool=action_name,
                status="error",
                summary=toolbox.summarize(action_name, error_payload, ok=False),
            )
            tool_result_text = json.dumps(error_payload, ensure_ascii=False, indent=2)

        events.append(asdict(event))
        conversation.extend(
            [
                {"role": "assistant", "content": raw_reply},
                {
                    "role": "user",
                    "content": (
                        f"TOOL RESULT for {action_name}:\n"
                        f"{_truncate_text(tool_result_text)}\n\n"
                        "If the task is now complete, return action=final. Otherwise call the next tool."
                    ),
                },
            ]
        )

    return AgentRunResult(
        model=model_name,
        response=(
            "I reached the local step limit before finishing. "
            "I can continue if you want, but the core tools are active."
        ),
        events=events,
    )
