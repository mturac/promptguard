from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .models import PromptInput

PROMPT_KEYS = frozenset(
    {
        "system",
        "system_prompt",
        "prompt",
        "instructions",
        "instruction",
    }
)

AGENT_INSTRUCTION_NAMES = frozenset(
    {
        "skill.md",
        "agents.md",
        "claude.md",
    }
)

FENCE_RE = re.compile(
    r"```(?P<label>[^\n`]*)\n(?P<body>.*?)```",
    re.DOTALL | re.IGNORECASE,
)

HEADING_RE = re.compile(
    r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$",
    re.MULTILINE,
)

FENCE_LABEL_HINTS = ("system", "prompt", "instruction", "instructions")
HEADING_HINTS = ("system", "prompt", "instruction", "instructions", "role", "boundaries")


def extract_prompts(path: Path) -> list[PromptInput]:
    if str(path) == "-":
        import sys

        return [PromptInput(name="stdin", content=sys.stdin.read(), source="stdin", line=1)]

    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    name_l = path.name.lower()

    if suffix == ".py":
        extracted = _extract_python_prompts(path, text)
        if extracted:
            return extracted

    if suffix == ".json":
        extracted = _extract_json_prompts(path, text)
        if extracted is not None:
            return extracted

    if suffix in {".yaml", ".yml"}:
        extracted = _extract_yaml_prompts(path, text)
        if extracted is not None:
            return extracted

    if name_l in AGENT_INSTRUCTION_NAMES or any(n in name_l for n in ("skill.md", "agents.md", "claude.md")):
        return _extract_markdown_segments(path, text, always_whole=True)

    if suffix in {".md", ".markdown", ".txt"}:
        segments = _extract_markdown_segments(path, text, always_whole=True)
        return segments

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


def _extract_json_prompts(path: Path, text: str) -> list[PromptInput] | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    found: list[PromptInput] = []
    _walk_mapping_for_prompts(data, path, found, path_keys=())
    return found  # empty list means no prompt keys — do not invent whole-file content


def _walk_mapping_for_prompts(
    node: object,
    path: Path,
    out: list[PromptInput],
    path_keys: tuple[str, ...],
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_s = str(key)
            next_keys = path_keys + (key_s,)
            if key_s.lower() in PROMPT_KEYS and isinstance(value, str) and value.strip():
                out.append(
                    PromptInput(
                        name=".".join(next_keys),
                        content=value,
                        source=str(path),
                        line=1,
                    )
                )
            else:
                _walk_mapping_for_prompts(value, path, out, next_keys)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _walk_mapping_for_prompts(item, path, out, path_keys + (str(idx),))


def _extract_yaml_prompts(path: Path, text: str) -> list[PromptInput] | None:
    """Lightweight YAML extractor for common prompt keys (no PyYAML dependency)."""
    found: list[PromptInput] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([ \t]*)([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        indent, key, rest = m.group(1), m.group(2), m.group(3).strip()
        if key.lower() not in PROMPT_KEYS:
            i += 1
            continue
        line_no = i + 1
        if rest in {"|", ">", "|-", ">-"}:
            block_indent = len(indent)
            body_lines: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    body_lines.append("")
                    i += 1
                    continue
                leading = len(nxt) - len(nxt.lstrip(" "))
                if leading <= block_indent and nxt.strip():
                    break
                # strip one indent level beyond key indent (2 spaces typical)
                body_lines.append(nxt[block_indent + 2 :] if leading >= block_indent + 2 else nxt.lstrip())
                i += 1
            content = "\n".join(body_lines).strip("\n")
            if content.strip():
                found.append(PromptInput(name=key, content=content, source=str(path), line=line_no))
            continue
        if rest.startswith('"') and rest.endswith('"') and len(rest) >= 2:
            content = rest[1:-1]
        elif rest.startswith("'") and rest.endswith("'") and len(rest) >= 2:
            content = rest[1:-1]
        else:
            content = rest
        if content:
            found.append(PromptInput(name=key, content=content, source=str(path), line=line_no))
        i += 1
    return found


def _extract_markdown_segments(path: Path, text: str, *, always_whole: bool) -> list[PromptInput]:
    prompts: list[PromptInput] = []
    if always_whole and text.strip():
        prompts.append(PromptInput(name=path.name, content=text, source=str(path), line=1))

    for m in FENCE_RE.finditer(text):
        label = (m.group("label") or "").strip().lower()
        body = m.group("body").strip("\n")
        if not body.strip():
            continue
        if label and any(h in label for h in FENCE_LABEL_HINTS):
            line = text[: m.start()].count("\n") + 1
            name = label.split()[0] if label else "fenced"
            prompts.append(PromptInput(name=name, content=body, source=str(path), line=line))

    # Heading sections whose title matches instruction hints
    matches = list(HEADING_RE.finditer(text))
    for idx, m in enumerate(matches):
        title = m.group("title").strip().lower()
        if not any(h in title for h in HEADING_HINTS):
            continue
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        if not body.strip():
            continue
        line = text[: m.start()].count("\n") + 1
        prompts.append(
            PromptInput(
                name=m.group("title").strip(),
                content=body,
                source=str(path),
                line=line,
            )
        )

    if prompts:
        return prompts
    return [PromptInput(name=path.name, content=text, source=str(path), line=1)]
