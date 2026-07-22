from __future__ import annotations

import sys
from typing import TextIO

from .accept_risk import append_acceptances
from .models import AuditReport, Finding
from .store import save_report


def run_tui(
    report: AuditReport,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    """Minimal interactive review UI (docs/TUI.md subset).

    Non-interactive streams: print table and return exit 1 if any high+ finding.
    Interactive: j/k navigate, f fix draft, a accept risk, s save, q quit.
    """
    inp = input_stream or sys.stdin
    out = output_stream or sys.stdout
    findings = list(report.findings)

    if not inp.isatty() or not out.isatty():
        return _noninteractive(report, findings, out)

    if not findings:
        out.write("No findings. Prompt contracts look complete.\n")
        return 0

    idx = 0
    out.write(_banner(report, findings))
    while True:
        idx = max(0, min(idx, len(findings) - 1))
        out.write(_list_panel(findings, idx))
        out.write(_detail_panel(findings[idx]))
        out.write("[j/k] move  [f] fix draft  [a] accept risk  [s] save  [q] quit\n> ")
        out.flush()
        line = inp.readline()
        if not line:
            break
        cmd = line.strip().lower()
        if cmd in {"q", "quit"}:
            break
        if cmd in {"j", "n", "down"}:
            idx = min(len(findings) - 1, idx + 1)
            continue
        if cmd in {"k", "p", "up"}:
            idx = max(0, idx - 1)
            continue
        if cmd in {"f", "fix"}:
            out.write("\n--- Fix draft ---\n")
            out.write(findings[idx].fix_draft)
            out.write("\n---------------\n")
            continue
        if cmd in {"a", "accept"}:
            out.write("Reason for accepting this risk: ")
            out.flush()
            reason = inp.readline().strip()
            if not reason:
                out.write("Empty reason ignored.\n")
                continue
            append_acceptances([f"{findings[idx].id}:{reason}"], source=findings[idx].source)
            out.write(f"Recorded accept-risk for {findings[idx].id}\n")
            continue
        if cmd in {"s", "save"}:
            path = save_report(report)
            out.write(f"Saved: {path}\n")
            continue
        out.write("Unknown command.\n")

    blocking = sum(1 for f in findings if f.severity in {"critical", "high"})
    return 1 if blocking else 0


def _noninteractive(report: AuditReport, findings: list[Finding], out: TextIO) -> int:
    out.write(
        f"PromptGuard TUI (non-interactive)  source={report.source}  "
        f"findings={len(findings)}\n"
    )
    for f in findings:
        loc = f"{f.source}:{f.line}" if f.line else f.source
        out.write(f"{f.severity.upper():8} {f.id:6} {loc}  {f.title}\n")
    blocking = sum(1 for f in findings if f.severity in {"critical", "high"})
    return 1 if blocking else 0


def _banner(report: AuditReport, findings: list[Finding]) -> str:
    blocking = sum(1 for f in findings if f.severity in {"critical", "high"})
    return (
        f"\n┌─ PromptGuard ──────────────────────────────────────────────\n"
        f"│ Source: {report.source}\n"
        f"│ Findings: {len(findings)}    Blocking (high+): {blocking}\n"
        f"└────────────────────────────────────────────────────────────\n"
    )


def _list_panel(findings: list[Finding], idx: int) -> str:
    lines = ["Findings:\n"]
    for i, f in enumerate(findings):
        mark = ">" if i == idx else " "
        lines.append(f" {mark} {f.severity.upper():8} {f.id}  {f.title[:60]}\n")
    return "".join(lines)


def _detail_panel(finding: Finding) -> str:
    return (
        f"\nDetail · {finding.id}\n"
        f"  Evidence: {finding.evidence}\n"
        f"  Contract: {finding.contract}\n"
        f"  Ask: {' | '.join(finding.clarifying_questions) or '-'}\n"
        f"  Approval: {finding.approval_contract}\n"
    )
