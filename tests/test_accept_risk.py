from pathlib import Path

import pytest

from promptguard.accept_risk import (
    AcceptRiskError,
    append_acceptances,
    filter_accepted_findings,
    parse_accept_risk,
)
from promptguard.cli import main
from promptguard.models import Finding


def test_parse_rejects_empty_reason():
    with pytest.raises(AcceptRiskError, match="empty reason"):
        parse_accept_risk("PG012:")


def test_append_and_filter(tmp_path: Path, monkeypatch):
    store = tmp_path / "accepted-risks.jsonl"
    monkeypatch.chdir(tmp_path)
    # write via absolute path
    append_acceptances(["PG012:ship deadline"], source="src/a.md", path=store)
    findings = [
        Finding(
            id="PG012",
            severity="high",
            category="c",
            title="t",
            evidence="e",
            impact="i",
            recommendation="r",
            contract="c",
            fix_draft="f",
            clarifying_questions=[],
            clarification_contract="cc",
            approval_contract="ac",
            source="src/a.md",
            line=1,
        ),
        Finding(
            id="PG015",
            severity="high",
            category="c",
            title="t",
            evidence="e",
            impact="i",
            recommendation="r",
            contract="c",
            fix_draft="f",
            clarifying_questions=[],
            clarification_contract="cc",
            approval_contract="ac",
            source="src/a.md",
            line=1,
        ),
    ]
    filtered = filter_accepted_findings(findings, path=store)
    assert [f.id for f in filtered] == ["PG015"]


def test_cli_accept_risk_empty_reason(tmp_path: Path):
    sample = tmp_path / "p.md"
    sample.write_text("Fix this bug and write code.", encoding="utf-8")
    code = main(["audit", str(sample), "--accept-risk", "PG012:", "--fail-on", "none"])
    assert code == 2


def test_cli_apply_accepted(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sample = tmp_path / "p.md"
    sample.write_text("Fix this bug and write code.", encoding="utf-8")
    code1 = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--accept-risk",
            "PG012:temporary",
            "--fail-on",
            "none",
            "--format",
            "table",
        ]
    )
    assert code1 == 0
    code2 = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--apply-accepted",
            "--fail-on",
            "high",
            "--format",
            "table",
        ]
    )
    # PG015 may still fire; if only PG012 was accepted, exit may still be 1
    # Accept both PG012 and PG015 for clean exit
    main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--accept-risk",
            "PG015:temporary",
            "--fail-on",
            "none",
            "--format",
            "table",
        ]
    )
    code3 = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--apply-accepted",
            "--fail-on",
            "high",
            "--format",
            "table",
        ]
    )
    assert code3 == 0
    assert code2 in (0, 1)
