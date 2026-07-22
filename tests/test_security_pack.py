import json
from pathlib import Path

from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput
from promptguard.packs import resolve_rules

EVAL = Path(__file__).resolve().parents[1] / "eval" / "security_cases.jsonl"


def test_security_pack_rule_ids():
    rules = resolve_rules(profile="security")
    ids = {r["id"] for r in rules}
    assert {"PG016", "PG017", "PG018"} <= ids


def test_security_eval_cases():
    for line in EVAL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        prompt = PromptInput(name=case["id"], content=case["prompt"], source="eval")
        report = audit_prompts([prompt], source="eval", profile="security")
        found = {f.id for f in report.findings}
        expected = set(case["expected"])
        if case["kind"] == "true_positive":
            assert expected <= found, case["id"]
        else:
            assert found.isdisjoint(expected) or not expected
            # for true_negative with empty expected, no security findings preferred
            if not expected:
                assert not found, f"{case['id']} unexpected {found}"
