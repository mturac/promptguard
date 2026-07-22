from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .accept_risk import AcceptRiskError, append_acceptances, filter_accepted_findings
from .auditor import audit_prompts
from .extractors import extract_prompts
from .models import AuditReport
from .packs import FAIL_ON_LEVELS, PackError, exit_code_for_findings, list_profiles, resolve_rules
from .repo import extract_repo_prompts
from .report import render_report
from .store import save_report

FORMATS = ["markdown", "json", "table", "csv", "sarif"]


def _add_shared_audit_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        default="general",
        help=f"rule pack profile ({', '.join(list_profiles())})",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="path to JSON rules array (or object with rules key); profile filters enabled ids",
    )
    parser.add_argument(
        "--fail-on",
        default=None,
        choices=list(FAIL_ON_LEVELS),
        help="exit 1 only when a finding is at least this severity; omit for legacy any-finding fail",
    )
    parser.add_argument(
        "--accept-risk",
        action="append",
        default=[],
        metavar="ID:reason",
        help="record intentional risk acceptance (repeatable)",
    )
    parser.add_argument(
        "--apply-accepted",
        action="store_true",
        help="omit findings matching .promptguard/accepted-risks.jsonl (rule id + source path)",
    )
    parser.add_argument("--format", choices=FORMATS, default="markdown")
    parser.add_argument("--save", action="store_true", help="append report to .promptguard/reports.jsonl")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptguard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit prompt contracts")
    audit.add_argument("path", type=Path, help="file path or - for stdin")
    _add_shared_audit_flags(audit)

    repo = subparsers.add_parser("audit-repo", help="audit prompt-like files under a directory")
    repo.add_argument("root", nargs="?", type=Path, default=Path("."), help="repo root (default: .)")
    repo.add_argument("--include", action="append", default=[], help="glob include (repeatable)")
    repo.add_argument("--exclude", action="append", default=[], help="glob exclude (repeatable)")
    _add_shared_audit_flags(repo)

    args = parser.parse_args(argv)
    if args.command not in {"audit", "audit-repo"}:
        return 0

    try:
        rules = resolve_rules(profile=args.profile, rules_path=args.rules)
    except PackError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2

    if args.command == "audit":
        prompts = extract_prompts(args.path)
        source = str(args.path)
    else:
        root = args.root if args.root is not None else Path(".")
        prompts = extract_repo_prompts(root, include=args.include or None, exclude=args.exclude or None)
        source = str(root)

    report = audit_prompts(prompts, source=source, rules=rules)

    if args.accept_risk:
        try:
            append_acceptances(args.accept_risk, source=source)
        except AcceptRiskError as exc:
            print(f"promptguard: {exc}", file=sys.stderr)
            return 2

    findings = report.findings
    if args.apply_accepted:
        findings = filter_accepted_findings(findings)
        report = AuditReport.create(
            source=report.source,
            prompts_checked=report.prompts_checked,
            findings=findings,
        )

    print(render_report(report, args.format))
    if args.save:
        saved_to = save_report(report)
        print(f"\nSaved: {saved_to}")
    try:
        return exit_code_for_findings(report.findings, args.fail_on)
    except PackError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
