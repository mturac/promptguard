from pathlib import Path

from promptguard.cli import main


def test_tui_noninteractive_exit(tmp_path: Path, capsys):
    p = tmp_path / "x.md"
    p.write_text("Fix this bug and write code.", encoding="utf-8")
    code = main(["tui", str(p), "--profile", "coding-agent"])
    assert code == 1
    out = capsys.readouterr().out
    assert "PG012" in out or "findings" in out.lower()
