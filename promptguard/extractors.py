from __future__ import annotations

import ast
from pathlib import Path

from .models import PromptInput


def extract_prompts(path: Path) -> list[PromptInput]:
    if str(path) == "-":
        import sys

        return [PromptInput(name="stdin", content=sys.stdin.read(), source="stdin", line=1)]

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        extracted = _extract_python_prompts(path, text)
        if extracted:
            return extracted

    return [PromptInput(name=path.name, content=text, source=str(path), line=1)]


def _extract_python_prompts(path: Path, text: str) -> list[PromptInput]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    prompts: list[PromptInput] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "PROMPTS" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        for key, value in zip(node.value.keys, node.value.values):
            name = _literal_str(key) or f"prompt_at_{getattr(value, 'lineno', 1)}"
            content = _literal_str(value)
            if content:
                prompts.append(
                    PromptInput(
                        name=name,
                        content=content,
                        source=str(path),
                        line=getattr(value, "lineno", None),
                    )
                )
    return prompts


def _literal_str(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None
    return value if isinstance(value, str) else None
