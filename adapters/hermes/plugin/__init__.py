"""Hermes plugin: block prompt-like writes that fail PromptGuard contracts."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

WRITE_TOOLS = {
    "write_file",
    "write",
    "edit",
    "patch",
    "apply_patch",
    "create_file",
    "update_file",
    "replace",
    "search_replace",
}

PROMPT_HINTS = (
    "prompt",
    "system prompt",
    "agent",
    "router",
    "orchestrator",
    "evaluator",
    "instruction",
    "instructions",
    "claude.md",
    "agents.md",
    "skill.md",
    "prompts.py",
    "soul.md",
)


def _norm(value: Any) -> str:
    return str(value or "").lower().replace("ı", "i")


def _has_prompt_hint(text: str) -> bool:
    lowered = _norm(text)
    return any(h in lowered for h in PROMPT_HINTS)


def _collect_strings(value: Any, out: list[str] | None = None) -> list[str]:
    if out is None:
        out = []
    if isinstance(value, str):
        if len(value) > 40 or _has_prompt_hint(value):
            out.append(value)
        return out
    if isinstance(value, dict):
        for k, v in value.items():
            key = _norm(k)
            if key in {
                "content",
                "text",
                "prompt",
                "instruction",
                "instructions",
                "system",
                "message",
                "new_string",
                "newstring",
                "replacement",
                "value",
                "body",
            } and isinstance(v, str):
                out.append(v)
            else:
                _collect_strings(v, out)
    elif isinstance(value, list):
        for item in value:
            _collect_strings(item, out)
    return out


def _skill_audit_script() -> Path | None:
    home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    candidates = [
        home / "skills" / "promptguard" / "scripts" / "audit_prompt.py",
        Path.home() / ".hermes" / "skills" / "promptguard" / "scripts" / "audit_prompt.py",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def _run_audit(content: str) -> tuple[int, str]:
    """Return (exit_code, report_text). Exit 1 means blocking findings."""
    profile = os.environ.get("PROMPTGUARD_PROFILE", "coding-agent")
    fail_on = os.environ.get("PROMPTGUARD_FAIL_ON", "high")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(content)
        tmp = Path(handle.name)
    try:
        # Prefer installed package CLI
        cmd = [
            sys.executable,
            "-m",
            "promptguard",
            "audit",
            str(tmp),
            "--profile",
            profile,
            "--fail-on",
            fail_on,
            "--format",
            "markdown",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode in (0, 1) and (proc.stdout or proc.returncode == 0):
            return proc.returncode, proc.stdout or ""

        script = _skill_audit_script()
        if script is None:
            return 0, ""
        cmd = [
            sys.executable,
            str(script),
            str(tmp),
            "--profile",
            profile,
            "--fail-on",
            fail_on,
            "--format",
            "markdown",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout or proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("promptguard audit failed: %s", exc)
        return 0, ""
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def pre_tool_call(tool_name: str, args: dict, task_id: str = "", **kwargs: Any):
    if os.environ.get("PROMPTGUARD_HERMES_DISABLE") == "1":
        return None
    name = _norm(tool_name)
    if name not in WRITE_TOOLS and not name.endswith("write") and "patch" not in name and "edit" not in name:
        return None

    haystack = json.dumps(args or {}, ensure_ascii=False)
    path_hint = ""
    for key in ("path", "file_path", "filepath", "file", "target"):
        if isinstance((args or {}).get(key), str):
            path_hint = str(args[key])
            break
    if not _has_prompt_hint(haystack) and not _has_prompt_hint(path_hint):
        return None

    chunks = _collect_strings(args or {})
    if path_hint and Path(path_hint).is_file():
        try:
            chunks.append(Path(path_hint).read_text(encoding="utf-8", errors="replace")[:50000])
        except OSError:
            pass
    content = "\n\n---\n\n".join(chunks).strip()
    if not content:
        return None

    code, report = _run_audit(content)
    if code != 1:
        return None

    message = (
        "PromptGuard blocked this prompt-like write "
        f"(profile={os.environ.get('PROMPTGUARD_PROFILE', 'coding-agent')}, "
        f"fail-on={os.environ.get('PROMPTGUARD_FAIL_ON', 'high')}). "
        "Report findings to the user; get approval or a fixed draft before writing.\n\n"
        + (report[:3500] if report else "(no report body)")
    )
    logger.warning("promptguard blocked tool=%s task=%s", tool_name, task_id)
    return {"action": "block", "message": message}


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", pre_tool_call)
