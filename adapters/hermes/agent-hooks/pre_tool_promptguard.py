#!/usr/bin/env python3
"""Shell-hook entry for Hermes pre_tool_call (optional alternative to the plugin).

Wire in ~/.hermes/config.yaml:

hooks:
  pre_tool_call:
    - matcher: "write_file|write|patch|edit|search_replace"
      command: "~/.hermes/agent-hooks/pre_tool_promptguard.py"
      timeout: 60
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if os.environ.get("PROMPTGUARD_HERMES_DISABLE") == "1":
        print("{}")
        return 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    blob = json.dumps(tool_input, ensure_ascii=False)
    path = ""
    for key in ("path", "file_path", "filepath", "file"):
        if isinstance(tool_input.get(key), str):
            path = tool_input[key]
            break
    hints = ("prompt", "agent", "skill.md", "agents.md", "instruction", "system")
    lowered = (blob + " " + path).lower()
    if not any(h in lowered for h in hints):
        print("{}")
        return 0

    content_parts: list[str] = []
    for key in ("content", "text", "new_string", "replacement", "body", "prompt"):
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            content_parts.append(val)
    if path and Path(path).is_file():
        try:
            content_parts.append(Path(path).read_text(encoding="utf-8", errors="replace")[:50000])
        except OSError:
            pass
    content = "\n\n".join(content_parts).strip()
    if not content:
        print("{}")
        return 0

    profile = os.environ.get("PROMPTGUARD_PROFILE", "coding-agent")
    fail_on = os.environ.get("PROMPTGUARD_FAIL_ON", "high")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(content)
        tmp = Path(handle.name)
    try:
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
        if proc.returncode == 1:
            reason = (proc.stdout or "PromptGuard findings")[:3000]
            print(
                json.dumps(
                    {
                        "action": "block",
                        "message": f"PromptGuard blocked write ({tool}):\n{reason}",
                    },
                    ensure_ascii=False,
                )
            )
            return 0
    except (OSError, subprocess.TimeoutExpired):
        pass
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
