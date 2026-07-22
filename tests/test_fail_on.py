from promptguard.cli import main
from promptguard.models import Finding
from promptguard.packs import exit_code_for_findings


def _finding(severity: str, rule_id: str = "PG012") -> Finding:
    return Finding(
        id=rule_id,
        severity=severity,  # type: ignore[arg-type]
        category="test",
        title="t",
        evidence="e",
        impact="i",
        recommendation="r",
        contract="c",
        fix_draft="f",
        clarifying_questions=[],
        clarification_contract="cc",
        approval_contract="ac",
        source="s",
        line=1,
    )


def test_legacy_any_finding_fails():
    assert exit_code_for_findings([_finding("low")], None) == 1
    assert exit_code_for_findings([], None) == 0


def test_fail_on_none_always_zero():
    assert exit_code_for_findings([_finding("critical")], "none") == 0


def test_fail_on_high_ignores_low():
    assert exit_code_for_findings([_finding("low")], "high") == 0
    assert exit_code_for_findings([_finding("high")], "high") == 1
    assert exit_code_for_findings([_finding("critical")], "high") == 1


def test_fail_on_medium_catches_medium():
    assert exit_code_for_findings([_finding("medium")], "medium") == 1
    assert exit_code_for_findings([_finding("low")], "medium") == 0


def test_cli_unknown_profile_exit_2(tmp_path):
    sample = tmp_path / "p.txt"
    sample.write_text("hello", encoding="utf-8")
    code = main(["audit", str(sample), "--profile", "does-not-exist"])
    assert code == 2


def test_cli_profile_and_fail_on_with_file(tmp_path):
    sample = tmp_path / "p.txt"
    sample.write_text("Fix this bug and write code.", encoding="utf-8")
    code = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--fail-on",
            "high",
            "--format",
            "table",
        ]
    )
    assert code == 1

    code_low_gate = main(
        [
            "audit",
            str(sample),
            "--profile",
            "system",
            "--fail-on",
            "high",
            "--format",
            "table",
        ]
    )
    # system profile should not fire PG012 on coding prompt
    assert code_low_gate == 0
