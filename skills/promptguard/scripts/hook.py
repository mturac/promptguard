#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def _bootstrap() -> None:
    here = Path(__file__).resolve()
    # skills/promptguard/scripts → repo root is parents[3]
    repo_root = here.parents[3] if len(here.parents) >= 4 else here.parent
    if (repo_root / "promptguard").is_dir() and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


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
    "skill.md",
)


def main() -> int:
    _bootstrap()
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

    from promptguard.auditor import audit_prompts
    from promptguard.models import PromptInput
    from promptguard.report import render_report

    report = audit_prompts(
        [PromptInput("user_message", prompt, "UserPromptSubmit", None)],
        source="UserPromptSubmit",
        profile="coding-agent",
    )
    context = [
        "PromptGuard active (profile=coding-agent): treat prompt/system prompt as contract audit targets.",
        "When relevant, report: Severity | Evidence | Impact | Missing/Conflicting Contract | Fix Draft.",
    ]
    if report.findings:
        context.append(render_report(report, "table"))

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

    from promptguard.auditor import audit_prompts
    from promptguard.extractors import extract_prompts
    from promptguard.report import render_report

    prompts = extract_prompts(path)
    report = audit_prompts(prompts, source=str(path), profile="coding-agent")
    if not report.findings:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "PromptGuard findings after write (profile=coding-agent, fail-on high recommended):\n\n"
                        + render_report(report, "table")
                    ),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def is_prompt_related(text: str) -> bool:
    lowered = text.lower()
    return any(t in lowered for t in TRIGGERS)


def should_audit_file(path: Path) -> bool:
    name = path.name.lower()
    return any(h in name for h in PROMPT_FILE_HINTS) or path.suffix.lower() in {
        ".md",
        ".prompt",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
    }


if __name__ == "__main__":
    raise SystemExit(main())
