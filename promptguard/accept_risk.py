from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Finding

DEFAULT_ACCEPT_STORE = Path(".promptguard/accepted-risks.jsonl")


class AcceptRiskError(ValueError):
    """Invalid accept-risk flag payload."""


def parse_accept_risk(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise AcceptRiskError(f"invalid --accept-risk '{spec}' (expected ID:reason)")
    rule_id, reason = spec.split(":", 1)
    rule_id = rule_id.strip()
    reason = reason.strip()
    if not rule_id:
        raise AcceptRiskError(f"invalid --accept-risk '{spec}' (empty rule id)")
    if not reason:
        raise AcceptRiskError(f"invalid --accept-risk '{spec}' (empty reason)")
    return rule_id, reason


def append_acceptances(
    specs: list[str],
    *,
    source: str,
    path: Path = DEFAULT_ACCEPT_STORE,
) -> list[dict]:
    records: list[dict] = []
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as handle:
        for spec in specs:
            rule_id, reason = parse_accept_risk(spec)
            record = {
                "rule_id": rule_id,
                "reason": reason,
                "source": source,
                "timestamp": now,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            records.append(record)
    return records


def load_acceptances(path: Path = DEFAULT_ACCEPT_STORE) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def filter_accepted_findings(
    findings: list[Finding],
    *,
    path: Path = DEFAULT_ACCEPT_STORE,
) -> list[Finding]:
    accepted = load_acceptances(path)
    if not accepted:
        return findings
    keys = {(str(r.get("rule_id")), str(r.get("source"))) for r in accepted}
    return [f for f in findings if (f.id, f.source) not in keys]
