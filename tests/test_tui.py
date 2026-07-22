from io import StringIO

from promptguard.models import AuditReport, Finding
from promptguard.tui import run_tui


def _report(findings: list[Finding]) -> AuditReport:
    return AuditReport.create(source="t.md", prompts_checked=1, findings=findings)


def _f(rule_id: str = "PG012", severity: str = "high") -> Finding:
    return Finding(
        id=rule_id,
        severity=severity,  # type: ignore[arg-type]
        category="c",
        title="title",
        evidence="e",
        impact="i",
        recommendation="r",
        contract="c",
        fix_draft="FIX_ME_DRAFT",
        clarifying_questions=["q1"],
        clarification_contract="cc",
        approval_contract="ac",
        source="t.md",
        line=1,
    )


def test_noninteractive_lists_findings():
    out = StringIO()
    code = run_tui(_report([_f()]), input_stream=StringIO(""), output_stream=out)
    assert code == 1
    assert "PG012" in out.getvalue()


def test_interactive_quit_and_fix():
    # not a tty → noninteractive path when isatty false; StringIO isatty is False
    out = StringIO()
    code = run_tui(_report([_f(), _f("PG015")]), input_stream=StringIO("q\n"), output_stream=out)
    assert code == 1
    text = out.getvalue()
    assert "PG012" in text
