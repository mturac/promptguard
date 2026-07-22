from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .accept_risk import AcceptRiskError, append_acceptances, filter_accepted_findings
from .auditor import audit_prompts
from .baseline import diff_findings, load_baseline_findings, render_baseline_diff
from .export_promptfoo import export_promptfoo_yaml
from .extractors import extract_prompts
from .judge import JudgeError, annotate_findings_with_judge
from .models import AuditReport
from .packs import FAIL_ON_LEVELS, PackError, exit_code_for_findings, list_profiles, resolve_rules
from .repo import extract_repo_prompts
from .report import render_report
from .store import save_report
from .tui import run_tui

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
        "--baseline",
        type=Path,
        default=None,
        help="JSON/JSONL report to diff against (new/fixed/unchanged)",
    )
    parser.add_argument(
        "--fail-on-new",
        action="store_true",
        help="with --baseline, exit 1 if any new finding appears",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="opt-in LLM second pass via turac-llm-router (TURAC_LLM_ROUTER_URL/KEY)",
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


def _build_report(args: argparse.Namespace) -> tuple[AuditReport, str]:
    rules = resolve_rules(profile=args.profile, rules_path=args.rules)
    if args.command in {"audit", "tui"}:
        prompts = extract_prompts(args.path)
        source = str(args.path)
    else:
        root = args.root if getattr(args, "root", None) is not None else Path(".")
        include = getattr(args, "include", None) or None
        exclude = getattr(args, "exclude", None) or None
        prompts = extract_repo_prompts(root, include=include, exclude=exclude)
        source = str(root)

    report = audit_prompts(prompts, source=source, rules=rules)

    if getattr(args, "accept_risk", None):
        append_acceptances(args.accept_risk, source=source)

    findings = report.findings
    if getattr(args, "apply_accepted", False):
        findings = filter_accepted_findings(findings)

    if getattr(args, "judge", False):
        excerpt = "\n\n".join(p.content for p in prompts)[:4000]
        findings = annotate_findings_with_judge(findings, prompt_excerpt=excerpt)

    report = AuditReport.create(
        source=report.source,
        prompts_checked=report.prompts_checked,
        findings=findings,
    )
    return report, source


def _run_audit_flow(args: argparse.Namespace) -> int:
    try:
        report, _source = _build_report(args)
    except PackError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2
    except AcceptRiskError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2
    except JudgeError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2

    print(render_report(report, args.format))

    baseline_diff = None
    if args.baseline is not None:
        try:
            baseline = load_baseline_findings(args.baseline)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"promptguard: cannot load baseline {args.baseline}: {exc}", file=sys.stderr)
            return 2
        baseline_diff = diff_findings(report.findings, baseline)
        print()
        print(render_baseline_diff(baseline_diff, "json" if args.format == "json" else "markdown"))

    if args.save:
        saved_to = save_report(report)
        print(f"\nSaved: {saved_to}")

    if args.fail_on_new:
        if baseline_diff is None:
            print("promptguard: --fail-on-new requires --baseline", file=sys.stderr)
            return 2
        return 1 if baseline_diff.new else 0

    try:
        return exit_code_for_findings(report.findings, args.fail_on)
    except PackError as exc:
        print(f"promptguard: {exc}", file=sys.stderr)
        return 2


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

    tui = subparsers.add_parser("tui", help="interactive finding review (minimal TUI)")
    tui.add_argument("path", type=Path, help="file path or - for stdin")
    tui.add_argument("--profile", default="coding-agent", help="rule pack profile")
    tui.add_argument("--rules", type=Path, default=None)
    tui.add_argument("--apply-accepted", action="store_true")
    tui.add_argument("--judge", action="store_true")

    exp = subparsers.add_parser(
        "export-promptfoo",
        help="export eval JSONL to a promptfoo YAML skeleton",
    )
    exp.add_argument("input", type=Path, help="eval JSONL path")
    exp.add_argument("-o", "--output", type=Path, default=None, help="output YAML path (default: stdout)")

    args = parser.parse_args(argv)

    if args.command in {"audit", "audit-repo"}:
        return _run_audit_flow(args)

    if args.command == "tui":
        # Normalize namespace for _build_report
        args.accept_risk = []
        args.apply_accepted = bool(args.apply_accepted)
        args.judge = bool(args.judge)
        try:
            report, _ = _build_report(args)
        except (PackError, JudgeError) as exc:
            print(f"promptguard: {exc}", file=sys.stderr)
            return 2
        return run_tui(report)

    if args.command == "export-promptfoo":
        try:
            yaml_text = export_promptfoo_yaml(args.input, args.output)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            print(f"promptguard: export failed: {exc}", file=sys.stderr)
            return 2
        if args.output is None:
            print(yaml_text, end="")
        else:
            print(f"Wrote {args.output}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
