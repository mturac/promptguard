from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Finding


@dataclass(frozen=True)
class BaselineDiff:
    new: list[Finding]
    fixed: list[dict[str, Any]]
    unchanged: list[Finding]


def finding_key(finding: Finding | dict[str, Any]) -> tuple[str, str, int | None]:
    if isinstance(finding, Finding):
        return (finding.id, finding.source, finding.line)
    return (
        str(finding.get("id", "")),
        str(finding.get("source", "")),
        finding.get("line"),
    )


def load_baseline_findings(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # Prefer single JSON document; fall back to JSONL last successful report line.
    try:
        obj = json.loads(text)
        findings = _extract_findings(obj)
        if findings or isinstance(obj, (dict, list)):
            return findings
    except json.JSONDecodeError:
        pass
    last: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        last = _extract_findings(obj)
    return last


def _extract_findings(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        findings = obj.get("findings")
        if isinstance(findings, list):
            return [x for x in findings if isinstance(x, dict)]
    return []


def diff_findings(current: list[Finding], baseline: list[dict[str, Any]]) -> BaselineDiff:
    base_map = {finding_key(f): f for f in baseline}
    cur_map = {finding_key(f): f for f in current}
    new = [cur_map[k] for k in cur_map.keys() - base_map.keys()]
    fixed = [base_map[k] for k in base_map.keys() - cur_map.keys()]
    unchanged = [cur_map[k] for k in cur_map.keys() & base_map.keys()]
    return BaselineDiff(new=new, fixed=fixed, unchanged=unchanged)


def render_baseline_diff(diff: BaselineDiff, fmt: str = "markdown") -> str:
    if fmt == "json":
        payload = {
            "new": [f.to_dict() for f in diff.new],
            "fixed": diff.fixed,
            "unchanged": [f.to_dict() for f in diff.unchanged],
            "counts": {
                "new": len(diff.new),
                "fixed": len(diff.fixed),
                "unchanged": len(diff.unchanged),
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
    lines = [
        "# Baseline diff",
        "",
        f"- New: {len(diff.new)}",
        f"- Fixed: {len(diff.fixed)}",
        f"- Unchanged: {len(diff.unchanged)}",
        "",
    ]
    if diff.new:
        lines.append("## New")
        for f in diff.new:
            loc = f"{f.source}:{f.line}" if f.line else f.source
            lines.append(f"- `{f.id}` ({f.severity}) {loc} — {f.title}")
        lines.append("")
    if diff.fixed:
        lines.append("## Fixed")
        for f in diff.fixed:
            rid = f.get("id", "?")
            src = f.get("source", "?")
            line = f.get("line")
            loc = f"{src}:{line}" if line is not None else src
            lines.append(f"- `{rid}` {loc}")
        lines.append("")
    if diff.unchanged:
        lines.append("## Unchanged")
        for f in diff.unchanged:
            loc = f"{f.source}:{f.line}" if f.line else f.source
            lines.append(f"- `{f.id}` {loc}")
        lines.append("")
    return "\n".join(lines).strip()
