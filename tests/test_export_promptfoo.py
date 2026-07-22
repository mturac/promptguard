from pathlib import Path

from promptguard.cli import main
from promptguard.export_promptfoo import export_promptfoo_yaml


def test_export_yaml_contains_cases(tmp_path: Path):
    src = tmp_path / "cases.jsonl"
    src.write_text(
        '{"id":"tp1","kind":"true_positive","prompt":"Fix this bug","expected":["PG012"],"rationale":"r"}\n',
        encoding="utf-8",
    )
    out = tmp_path / "pf.yaml"
    text = export_promptfoo_yaml(src, out)
    assert out.exists()
    assert "tp1" in text
    assert "Fix this bug" in text
    assert "PG012" in text
    assert "providers:" in text
    assert "tests:" in text


def test_cli_export_stdout(tmp_path: Path, capsys):
    src = tmp_path / "cases.jsonl"
    src.write_text(
        '{"id":"x","prompt":"hi","expected":[]}\n',
        encoding="utf-8",
    )
    code = main(["export-promptfoo", str(src)])
    assert code == 0
    out = capsys.readouterr().out
    assert "description: PromptGuard eval export" in out
