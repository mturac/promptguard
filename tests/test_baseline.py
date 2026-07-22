import json
from pathlib import Path

from promptguard.auditor import audit_prompts
from promptguard.baseline import diff_findings, load_baseline_findings
from promptguard.cli import main
from promptguard.models import Finding, PromptInput


def _f(rule_id: str, source: str = "a.md", line: int | None = 1) -> Finding:
    return Finding(
        id=rule_id,
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
        source=source,
        line=line,
    )


def test_diff_new_fixed_unchanged():
    baseline = [
        {"id": "PG012", "source": "a.md", "line": 1},
        {"id": "PG015", "source": "a.md", "line": 1},
    ]
    current = [_f("PG012"), _f("PG011")]
    d = diff_findings(current, baseline)
    assert {f.id for f in d.new} == {"PG011"}
    assert {f["id"] for f in d.fixed} == {"PG015"}
    assert {f.id for f in d.unchanged} == {"PG012"}


def test_load_jsonl_last_report(tmp_path: Path):
    path = tmp_path / "reports.jsonl"
    path.write_text(
        json.dumps({"findings": [{"id": "PG001", "source": "x", "line": 1}]})
        + "\n"
        + json.dumps({"findings": [{"id": "PG012", "source": "y", "line": 2}]})
        + "\n",
        encoding="utf-8",
    )
    loaded = load_baseline_findings(path)
    assert loaded[0]["id"] == "PG012"


def test_cli_baseline_fail_on_new(tmp_path: Path):
    sample = tmp_path / "p.md"
    sample.write_text("Fix this bug and write code.", encoding="utf-8")
    # baseline empty → all current findings are new
    base = tmp_path / "base.json"
    base.write_text(json.dumps({"findings": []}), encoding="utf-8")
    code = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--baseline",
            str(base),
            "--fail-on-new",
            "--format",
            "table",
        ]
    )
    assert code == 1

    # baseline equals current keys → no new
    report = audit_prompts(
        [PromptInput(name="p", content="Fix this bug and write code.", source=str(sample), line=1)],
        source=str(sample),
        profile="coding-agent",
    )
    base.write_text(json.dumps({"findings": [f.to_dict() for f in report.findings]}), encoding="utf-8")
    code2 = main(
        [
            "audit",
            str(sample),
            "--profile",
            "coding-agent",
            "--baseline",
            str(base),
            "--fail-on-new",
            "--format",
            "table",
        ]
    )
    assert code2 == 0
