from __future__ import annotations

import argparse
from pathlib import Path

from .auditor import audit_prompts
from .extractors import extract_prompts
from .report import render_report
from .store import save_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptguard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit prompt contracts")
    audit.add_argument("path", type=Path, help="file path or - for stdin")
    audit.add_argument("--format", choices=["markdown", "json", "table", "csv"], default="markdown")
    audit.add_argument("--save", action="store_true", help="append report to .promptguard/reports.jsonl")

    args = parser.parse_args(argv)
    if args.command == "audit":
        prompts = extract_prompts(args.path)
        report = audit_prompts(prompts, source=str(args.path))
        print(render_report(report, args.format))
        if args.save:
            saved_to = save_report(report)
            print(f"\nSaved: {saved_to}")
        return 1 if report.findings else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
