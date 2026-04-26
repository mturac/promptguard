#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from audit_prompt import Prompt, audit, render

TRIGGERS = (
    "prompt",
    "system prompt",
    "agent prompt",
    "router",
    "tool call",
    "function call",
    "llm",
    "chatbot",
    "claude",
    "codex",
    "opencode",
    "openclaw",
    "gpt",
)

PROMPT_FILE_HINTS = (
    "prompt",
    "agent",
    "router",
    "evaluator",
    "system",
    "claude.md",
    "agents.md",
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    event = payload.get("hook_event_name")
    if event == "UserPromptSubmit":
        return on_user_prompt(payload)
    if event == "PostToolUse":
        return on_post_tool(payload)
    return 0


def on_user_prompt(payload: dict) -> int:
    prompt = payload.get("prompt", "")
    if not is_prompt_related(prompt):
        return 0

    findings = audit([Prompt("user_message", prompt, "UserPromptSubmit", None)])
    context = [
        "PromptGuard active: treat any prompt/system prompt in this request as a contract audit target.",
        "When relevant, report: Severity | Evidence | Impact | Missing/Conflicting Contract | Fix Draft.",
    ]
    if findings:
        context.append(render(findings, "table", Path("UserPromptSubmit"), 1))

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "\n\n".join(context),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def on_post_tool(payload: dict) -> int:
    tool_name = payload.get("tool_name", "")
    if tool_name not in {"Write", "Edit", "MultiEdit"}:
        return 0

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0

    path = Path(file_path)
    if not should_audit_file(path) or not path.exists():
        return 0

    from audit_prompt import extract_prompts

    findings = audit(extract_prompts(path))
    if not findings:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "PromptGuard findings after prompt-like file edit:\n\n"
                    + render(findings, "table", path, 1),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def is_prompt_related(text: str) -> bool:
    low = text.lower()
    return any(trigger in low for trigger in TRIGGERS)


def should_audit_file(path: Path) -> bool:
    low = str(path).lower()
    if any(part in low for part in ("/node_modules/", "/dist/", "/build/", "/.next/", "/coverage/")):
        return False
    return path.suffix in {".md", ".txt", ".py", ".json", ".yaml", ".yml"} and any(
        hint in low for hint in PROMPT_FILE_HINTS
    )


if __name__ == "__main__":
    raise SystemExit(main())
