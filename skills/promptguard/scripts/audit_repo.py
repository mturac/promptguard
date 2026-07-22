#!/usr/bin/env python3
"""Skill entrypoint for repo audit — delegates to promptguard audit-repo."""
from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> None:
    here = Path(__file__).resolve()
    repo_root = here.parents[3] if len(here.parents) >= 4 else here.parent
    if (repo_root / "promptguard").is_dir() and str(repo_root) not in sys.path:
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

    argv = list(sys.argv[1:])
    if not argv or argv[0].startswith("-"):
        argv = ["audit-repo", ".", *argv]
    elif argv[0] != "audit-repo":
        argv = ["audit-repo", *argv]
    return pg_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
