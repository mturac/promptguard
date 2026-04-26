import json
from pathlib import Path

from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput


CASES = Path("eval/technical_cases.jsonl")


def load_cases():
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_technical_cases():
    for case in load_cases():
        prompt = PromptInput(name=case["id"], content=case["prompt"], source=str(CASES))
        report = audit_prompts([prompt], source=str(CASES))
        found = {finding.id for finding in report.findings}
        assert set(case["expected"]).issubset(found), case["id"]
