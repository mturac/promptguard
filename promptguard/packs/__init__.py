from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from promptguard.models import Finding

SEVERITY_RANK: dict[str, int] = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
}

FAIL_ON_LEVELS = ("critical", "high", "medium", "low", "info", "none")

BUILTIN_PROFILES = ("general", "coding-agent", "system", "security")


class PackError(ValueError):
    """Invalid profile, pack file, or rules payload."""


def list_profiles() -> list[str]:
    return list(BUILTIN_PROFILES)


def load_catalog_rules() -> list[dict[str, Any]]:
    raw = files("promptguard").joinpath("rules.json").read_text(encoding="utf-8")
    rules = json.loads(raw)
    if not isinstance(rules, list):
        raise PackError("rules.json must be a JSON array of rule objects")
    return rules


def load_rules_file(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PackError(f"rules file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PackError(f"invalid rules JSON: {path}: {exc}") from exc

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rules"), list):
        return data["rules"]
    raise PackError(f"rules file must be a JSON array or object with 'rules': {path}")


def _load_pack_meta(profile: str) -> dict[str, Any]:
    if profile not in BUILTIN_PROFILES:
        known = ", ".join(BUILTIN_PROFILES)
        raise PackError(f"unknown profile '{profile}'. Known profiles: {known}")
    try:
        raw = files("promptguard.packs").joinpath(f"{profile}.json").read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PackError(f"pack metadata missing for profile '{profile}'") from exc
    meta = json.loads(raw)
    if not isinstance(meta, dict):
        raise PackError(f"pack {profile}.json must be a JSON object")
    return meta


def resolve_rules(*, profile: str = "general", rules_path: Path | None = None) -> list[dict[str, Any]]:
    """Load rules then apply profile enable-filter.

    Precedence:
    - Base rules come from --rules PATH if set, else package rules.json catalog.
    - Profile pack metadata filters by rule_ids when present (list).
    - Profile 'general' enables the full loaded catalog (rule_ids null / omitted).
    - Profile 'security' may point at extra_rules file; empty rule_ids yields no rules until filled.
    """
    base = load_rules_file(rules_path) if rules_path is not None else load_catalog_rules()
    meta = _load_pack_meta(profile)

    extra_name = meta.get("extra_rules")
    if extra_name:
        extra_raw = files("promptguard.packs").joinpath(extra_name).read_text(encoding="utf-8")
        extra = json.loads(extra_raw)
        if not isinstance(extra, list):
            raise PackError(f"extra_rules {extra_name} must be a JSON array")
        by_id = {r["id"]: r for r in base if isinstance(r, dict) and "id" in r}
        for rule in extra:
            by_id[rule["id"]] = rule
        base = list(by_id.values())

    rule_ids = meta.get("rule_ids", None)
    if rule_ids is None:
        return base
    if not isinstance(rule_ids, list):
        raise PackError(f"pack {profile}: rule_ids must be a list or null")
    allowed = set(rule_ids)
    return [rule for rule in base if rule.get("id") in allowed]


def exit_code_for_findings(findings: list[Finding], fail_on: str | None) -> int:
    """Map findings + fail-on policy to process exit code.

    fail_on None: legacy — any finding → 1
    fail_on 'none': always 0
    otherwise: 1 if any finding severity rank >= threshold
    """
    if fail_on is None:
        return 1 if findings else 0
    if fail_on == "none":
        return 0
    if fail_on not in SEVERITY_RANK:
        raise PackError(f"invalid --fail-on '{fail_on}'. Choose from: {', '.join(FAIL_ON_LEVELS)}")
    threshold = SEVERITY_RANK[fail_on]
    for finding in findings:
        rank = SEVERITY_RANK.get(finding.severity, 0)
        if rank >= threshold:
            return 1
    return 0
