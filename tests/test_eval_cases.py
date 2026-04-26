import json
import subprocess
import sys
from pathlib import Path

from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput


CASES = Path("eval/cases.jsonl")


def load_cases():
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_true_positive_cases():
    for case in load_cases():
        if case["kind"] != "true_positive":
            continue
        prompt = PromptInput(name=case["id"], content=case["prompt"], source="eval/cases.jsonl")
        report = audit_prompts([prompt], source="eval/cases.jsonl")
        found = {finding.id for finding in report.findings}
        assert set(case["expected"]).issubset(found), case["id"]


def test_true_negative_cases():
    for case in load_cases():
        if case["kind"] != "true_negative":
            continue
        prompt = PromptInput(name=case["id"], content=case["prompt"], source="eval/cases.jsonl")
        report = audit_prompts([prompt], source="eval/cases.jsonl")
        assert report.findings == [], case["id"]


def test_cli_audits_stdin_before_write():
    result = subprocess.run(
        [sys.executable, "-m", "promptguard", "audit", "-", "--format", "table"],
        input="Bana rapor hazırla.",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "PG007" in result.stdout
