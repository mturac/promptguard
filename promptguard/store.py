from __future__ import annotations

import json
from pathlib import Path

from .models import AuditReport

DEFAULT_STORE = Path(".promptguard/reports.jsonl")


def save_report(report: AuditReport, path: Path = DEFAULT_STORE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")
    return path
