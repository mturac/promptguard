import json
from pathlib import Path

from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput
from promptguard.report import render_report


def test_sarif_shape_for_findings():
    prompt = PromptInput(name="code", content="Fix this bug and write code.", source="src/p.md", line=3)
    report = audit_prompts([prompt], source="src/p.md", profile="coding-agent")
    assert report.findings
    payload = json.loads(render_report(report, "sarif"))
    assert payload["version"] == "2.1.0"
    assert payload["runs"]
    run = payload["runs"][0]
    assert run["tool"]["driver"]["name"] == "PromptGuard"
    assert run["tool"]["driver"]["rules"]
    result = run["results"][0]
    assert "ruleId" in result
    assert result["level"] in {"error", "warning", "note"}
    assert "message" in result and "text" in result["message"]
    loc = result["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "src/p.md"
    assert loc["region"]["startLine"] == 3


def test_cli_sarif_format(tmp_path: Path, capsys):
    from promptguard.cli import main

    sample = tmp_path / "AGENTS.md"
    sample.write_text("Fix this bug and write code.", encoding="utf-8")
    code = main(["audit", str(sample), "--profile", "coding-agent", "--format", "sarif", "--fail-on", "none"])
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["version"] == "2.1.0"
