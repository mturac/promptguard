#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit_prompt import audit, extract_prompts, render

SKIP_DIRS = {
    ".git",
    ".next",
    ".promptguard",
    ".pytest_cache",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "tmp",
}

PROMPT_HINTS = (
    "agents.md",
    "claude.md",
    "prompt",
    "agent",
    "router",
    "evaluator",
    "system",
)

EXTENSIONS = {".md", ".txt", ".py", ".json", ".yaml", ".yml"}


def main() -> int:
    parser = argparse.ArgumentParser(prog="audit_repo.py")
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--format", choices=["markdown", "json", "table"], default="markdown")
    args = parser.parse_args()

    files = list(prompt_files(args.root))
    all_findings = []
    prompts_checked = 0
    for file_path in files:
        prompts = extract_prompts(file_path)
        prompts_checked += len(prompts)
        all_findings.extend(audit(prompts))

    print(render(all_findings, args.format, args.root, prompts_checked))
    return 1 if all_findings else 0


def prompt_files(root: Path):
    root = root.resolve()
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        lower = path.name.lower()
        if any(hint in lower for hint in PROMPT_HINTS):
            yield path


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
