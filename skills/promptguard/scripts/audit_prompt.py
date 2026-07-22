#!/usr/bin/env python3
"""Skill entrypoint: prefer installed promptguard package; fallback to package path."""
from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> None:
    # Repo layout: skills/promptguard/scripts → ../../../promptguard package
    here = Path(__file__).resolve()
    repo_root = here.parents[3] if len(here.parents) >= 4 else here.parent
    candidate = repo_root / "promptguard"
    if candidate.is_dir() and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def main() -> int:
    _bootstrap()
    try:
        from promptguard.cli import main as pg_main
    except ImportError:
        print(
            "promptguard package not importable. Install with: pip install -e .",
            file=sys.stderr,
        )
        return 2

    # Map skill CLI: audit_prompt.py PATH [flags] → promptguard audit PATH [flags]
    argv = ["audit", *sys.argv[1:]]
    return pg_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
