from __future__ import annotations

import csv
import json
from io import StringIO

from .models import AuditReport


def render_report(report: AuditReport, fmt: str = "markdown") -> str:
    if fmt == "json":
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    if fmt == "csv":
        return _csv(report)
    if fmt == "table":
        return _table(report)
    return _markdown(report)


def _markdown(report: AuditReport) -> str:
    lines = [
        "# PromptGuard Audit",
        "",
        f"- Source: `{report.source}`",
        f"- Prompts checked: {report.prompts_checked}",
        f"- Findings: {len(report.findings)}",
        "",
    ]
    for finding in report.findings:
        loc = f"{finding.source}:{finding.line}" if finding.line else finding.source
        lines.extend(
            [
                f"## {finding.severity.upper()} · {finding.category} · {finding.id}",
                f"**Location:** `{loc}`",
                f"**Issue:** {finding.title}",
                f"**Evidence:** {finding.evidence}",
                f"**Impact:** {finding.impact}",
                f"**Contract:** {finding.contract}",
                f"**Clarification contract:** {finding.clarification_contract}",
                f"**Ask:** {_ask(finding.clarifying_questions)}",
                f"**Approval:** {finding.approval_contract}",
                f"**Fix draft:** {finding.fix_draft}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def _table(report: AuditReport) -> str:
    rows = ["severity | category | id | issue", "--- | --- | --- | ---"]
    for finding in report.findings:
        rows.append(f"{finding.severity} | {finding.category} | {finding.id} | {finding.title}")
    return "\n".join(rows)


def _csv(report: AuditReport) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "source",
            "line",
            "severity",
            "category",
            "id",
            "issue",
            "evidence",
            "impact",
            "contract",
            "clarification_contract",
            "questions",
            "approval_contract",
            "fix_draft",
        ]
    )
    for finding in report.findings:
        writer.writerow(
            [
                finding.source,
                finding.line or "",
                finding.severity,
                finding.category,
                finding.id,
                finding.title,
                finding.evidence,
                finding.impact,
                finding.contract,
                finding.clarification_contract,
                _ask(finding.clarifying_questions),
                finding.approval_contract,
                finding.fix_draft,
            ]
        )
    return output.getvalue().strip()


def _ask(questions: list[str]) -> str:
    return " | ".join(questions) if questions else "No clarification needed; apply the contract fix."
