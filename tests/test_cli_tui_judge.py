from pathlib import Path
from unittest.mock import patch

from promptguard.cli import main


def test_tui_noninteractive_exit(tmp_path: Path, capsys):
    p = tmp_path / "x.md"
    p.write_text("Fix this bug and write code.", encoding="utf-8")
    code = main(["tui", str(p), "--profile", "coding-agent"])
    assert code == 1
    out = capsys.readouterr().out
    assert "PG012" in out or "findings" in out.lower()


def test_audit_judge_flag_calls_annotator(tmp_path: Path):
    p = tmp_path / "x.md"
    p.write_text("Fix this bug and write code.", encoding="utf-8")
    with patch("promptguard.cli.annotate_findings_with_judge", side_effect=lambda findings, **kw: findings) as mocked:
        code = main(["audit", str(p), "--profile", "coding-agent", "--judge", "--fail-on", "none", "--format", "table"])
        assert code == 0
        assert mocked.called
