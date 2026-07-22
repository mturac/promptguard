from __future__ import annotations

import fnmatch
from pathlib import Path

from .extractors import extract_prompts
from .models import PromptInput

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
    ".promptguard",
}

PROMPT_BASENAMES = {
    "skill.md",
    "agents.md",
    "claude.md",
    "prompts.py",
    "system_prompt.md",
    "system-prompt.md",
}

PROMPT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".prompt",
    ".yaml",
    ".yml",
    ".json",
    ".py",
}


def is_prompt_like(path: Path) -> bool:
    name = path.name.lower()
    if name in PROMPT_BASENAMES:
        return True
    if "prompt" in name or name.endswith(".prompt"):
        return True
    if path.suffix.lower() in PROMPT_SUFFIXES and (
        name in PROMPT_BASENAMES
        or any(token in name for token in ("prompt", "agent", "skill", "system", "instruction"))
        or path.suffix.lower() in {".prompt"}
    ):
        return True
    # Common instruction files
    if name in {"agents.md", "claude.md", "skill.md", "readme.md"}:
        return name != "readme.md"
    if path.suffix.lower() in {".yaml", ".yml", ".json"} and any(
        token in name for token in ("prompt", "agent", "bot", "system", "config")
    ):
        return True
    if path.suffix.lower() == ".py" and "prompt" in name:
        return True
    if path.suffix.lower() in {".md", ".txt"} and any(
        token in name for token in ("prompt", "agent", "skill", "system", "instruction", "agents", "claude")
    ):
        return True
    return False


def iter_prompt_files(
    root: Path,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[Path]:
    root = root.resolve()
    include = include or []
    exclude = exclude or []
    results: list[Path] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if exclude and any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path.name, pat) for pat in exclude):
            continue
        if include:
            if not any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path.name, pat) for pat in include):
                continue
            results.append(path)
            continue
        if is_prompt_like(path):
            results.append(path)
    return results


def extract_repo_prompts(
    root: Path,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[PromptInput]:
    prompts: list[PromptInput] = []
    for path in iter_prompt_files(root, include=include, exclude=exclude):
        try:
            prompts.extend(extract_prompts(path))
        except (OSError, UnicodeDecodeError):
            continue
    return prompts
