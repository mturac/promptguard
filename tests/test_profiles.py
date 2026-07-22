from pathlib import Path

import pytest

from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput
from promptguard.packs import PackError, list_profiles, resolve_rules


def test_list_profiles_includes_builtins():
    profiles = list_profiles()
    assert "general" in profiles
    assert "coding-agent" in profiles
    assert "system" in profiles
    assert "security" in profiles


def test_unknown_profile_errors():
    with pytest.raises(PackError, match="unknown profile"):
        resolve_rules(profile="nope")


def test_general_includes_core_catalog():
    rules = resolve_rules(profile="general")
    ids = {r["id"] for r in rules}
    assert "PG001" in ids
    assert "PG012" in ids
    assert "PG015" in ids


def test_coding_agent_includes_responsibility_and_risk():
    rules = resolve_rules(profile="coding-agent")
    ids = {r["id"] for r in rules}
    assert {"PG011", "PG012", "PG015"} <= ids
    assert "PG001" not in ids


def test_system_includes_safety_and_override():
    rules = resolve_rules(profile="system")
    ids = {r["id"] for r in rules}
    assert {"PG001", "PG002", "PG004", "PG008", "PG010"} <= ids
    assert "PG012" not in ids


def test_security_profile_loads_pg016_plus():
    rules = resolve_rules(profile="security")
    ids = {r["id"] for r in rules}
    assert {"PG016", "PG017", "PG018"} <= ids


def test_coding_profile_fires_pg012_on_vague_coding_prompt():
    prompt = PromptInput(name="code", content="Fix this bug and write code.", source="t")
    report = audit_prompts([prompt], source="t", profile="coding-agent")
    assert any(f.id == "PG012" for f in report.findings)
    assert not any(f.id == "PG001" for f in report.findings)


def test_system_profile_skips_coding_responsibility_rule():
    prompt = PromptInput(name="code", content="Fix this bug and write code.", source="t")
    report = audit_prompts([prompt], source="t", profile="system")
    assert not any(f.id == "PG012" for f in report.findings)


def test_external_rules_filtered_by_profile(tmp_path: Path):
    rules_path = tmp_path / "custom.json"
    rules_path.write_text(
        """
        [
          {"id": "PG012", "severity": "high", "category": "responsibility_contract",
           "title": "coding", "any": ["write code"], "missing_groups": [["responsible"]],
           "impact": "i", "recommendation": "r", "contract": "c", "fix_draft": "f"},
          {"id": "PG001", "severity": "high", "category": "conflict",
           "title": "priv", "any": ["confidential"], "also_any": ["management"],
           "impact": "i", "recommendation": "r", "contract": "c", "fix_draft": "f"}
        ]
        """,
        encoding="utf-8",
    )
    rules = resolve_rules(profile="coding-agent", rules_path=rules_path)
    assert {r["id"] for r in rules} == {"PG012"}
