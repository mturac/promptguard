#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Prompt:
    name: str
    content: str
    source: str
    line: int | None = None


@dataclass
class Finding:
    id: str
    severity: str
    category: str
    title: str
    evidence: str
    impact: str
    contract: str
    fix_draft: str
    clarifying_questions: list[str]
    clarification_contract: str
    approval_contract: str
    source: str
    line: int | None


def main() -> int:
    parser = argparse.ArgumentParser(prog="audit_prompt.py")
    parser.add_argument("path", type=Path)
    parser.add_argument("--format", choices=["markdown", "json", "table"], default="markdown")
    args = parser.parse_args()

    prompts = extract_prompts(args.path)
    findings = audit(prompts)
    print(render(findings, args.format, args.path, len(prompts)))
    return 1 if findings else 0


def extract_prompts(path: Path) -> list[Prompt]:
    if str(path) == "-":
        import sys

        return [Prompt("stdin", sys.stdin.read(), "stdin", 1)]

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        prompts = extract_python_prompts(path, text)
        if prompts:
            return prompts
    return [Prompt(path.name, text, str(path), 1)]


def extract_python_prompts(path: Path, text: str) -> list[Prompt]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    prompts: list[Prompt] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "PROMPTS" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            name = literal_str(key) or f"prompt_at_{getattr(value, 'lineno', 1)}"
            content = literal_str(value)
            if content:
                prompts.append(Prompt(name, content, str(path), getattr(value, "lineno", None)))
    return prompts


def literal_str(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (SyntaxError, ValueError):
        return None
    return value if isinstance(value, str) else None


def audit(prompts: list[Prompt]) -> list[Finding]:
    rules = load_rules()
    findings: list[Finding] = []
    for prompt in prompts:
        text = norm(prompt.content)
        for rule in rules:
            if matches(rule, text, prompt.content):
                findings.append(
                    Finding(
                        id=rule["id"],
                        severity=rule["severity"],
                        category=rule["category"],
                        title=f"{prompt.name}: {rule['title']}",
                        evidence=evidence(rule, prompt.content),
                        impact=rule["impact"],
                        contract=rule["contract"],
                        fix_draft=rule["fix_draft"],
                        clarifying_questions=rule.get("clarifying_questions", []),
                        clarification_contract=rule.get("clarification_contract", default_clarification(rule)),
                        approval_contract=rule.get("approval_contract", default_approval(rule)),
                        source=prompt.source,
                        line=prompt.line,
                    )
                )
    return findings


def matches(rule: dict[str, Any], text: str, original: str) -> bool:
    if "min_chars" in rule and len(original) < int(rule["min_chars"]):
        return False
    if "any" in rule and not has_any(text, rule["any"]):
        return False
    if "also_any" in rule and not has_any(text, rule["also_any"]):
        return False
    if "missing_any" in rule and has_any(text, rule["missing_any"]):
        return False
    if "missing_groups" in rule and all(has_any(text, group) for group in rule["missing_groups"]):
        return False
    return True


def has_any(text: str, terms: list[str]) -> bool:
    return any(norm(term) in text for term in terms)


def evidence(rule: dict[str, Any], content: str) -> str:
    for term in rule.get("any", []) + rule.get("also_any", []):
        idx = content.lower().find(term.lower())
        if idx >= 0:
            return " ".join(content[max(0, idx - 80): min(len(content), idx + 160)].split())
    return "Rule matched by absence."


def render(findings: list[Finding], fmt: str, source: Path, prompts_checked: int) -> str:
    if fmt == "json":
        return json.dumps(
            {"source": str(source), "prompts_checked": prompts_checked, "findings": [asdict(f) for f in findings]},
            ensure_ascii=False,
            indent=2,
        )
    if fmt == "table":
        rows = ["severity | category | id | issue", "--- | --- | --- | ---"]
        rows.extend(f"{f.severity} | {f.category} | {f.id} | {f.title}" for f in findings)
        return "\n".join(rows)

    lines = [f"# PromptGuard Audit\n\nSource: `{source}`\nPrompts checked: {prompts_checked}\nFindings: {len(findings)}\n"]
    for finding in findings:
        loc = f"{finding.source}:{finding.line}" if finding.line else finding.source
        lines.append(
            f"## {finding.severity.upper()} · {finding.category} · {finding.id}\n"
            f"Location: `{loc}`\n"
            f"Evidence: {finding.evidence}\n"
            f"Impact: {finding.impact}\n"
            f"Contract: {finding.contract}\n"
            f"Clarification contract: {finding.clarification_contract}\n"
            f"Ask: {ask(finding.clarifying_questions)}\n"
            f"Approval: {finding.approval_contract}\n"
            f"Fix draft: {finding.fix_draft}\n"
        )
    return "\n".join(lines).strip()


def load_rules() -> list[dict[str, Any]]:
    rules_path = Path(__file__).resolve().parents[1] / "references" / "rules.json"
    return json.loads(rules_path.read_text(encoding="utf-8"))


def ask(questions: list[str]) -> str:
    return " | ".join(questions) if questions else "No clarification needed; apply the contract fix."


def default_clarification(rule: dict[str, Any]) -> str:
    category = rule.get("category", "contract")
    defaults = {
        "intent_gap": "Do not produce the deliverable yet. First collect the missing decision points for task, scope, data, output, and success criteria.",
        "conflict": "Do not choose one instruction silently. Ask which rule has priority or define a precedence rule.",
        "override_risk": "Do not let later exceptions weaken hard boundaries. Ask for rule priority and allowed exceptions.",
        "context_retention": "Do not assume long context remains usable. Ask what must persist, what can be ignored, and how old context should be summarized.",
        "false_certainty": "Do not answer as if unknown facts are known. Ask for source data or define unknown/fallback behavior.",
        "output_contract": "Do not return free-form output. Ask for format, length, language, and fallback shape.",
    }
    return defaults.get(category, "Ask for the missing contract before relying on this prompt behavior.")


def default_approval(rule: dict[str, Any]) -> str:
    category = rule.get("category", "contract")
    defaults = {
        "responsibility_contract": "Approve only when owner role, responsibility boundary, constraints, verification, and final accountability output are explicit.",
        "task_underdefined": "Approve only when target, scope, acceptance criteria, verification command, and stopping condition are explicit.",
        "intent_gap": "Approve only when scope, data, audience, format, and success criteria are explicit.",
        "output_contract": "Approve only when output format, length, language, and insufficient-data behavior are explicit.",
        "override_risk": "Approve only when rule precedence and allowed exceptions are explicit.",
        "context_retention": "Approve only when durable state, relevant context, and summarization/truncation behavior are explicit.",
        "false_certainty": "Approve only when source of truth and unknown behavior are explicit.",
    }
    return defaults.get(category, "Approve only when the missing contract is explicit enough to verify.")


def norm(text: str) -> str:
    return text.lower().replace("ı", "i")


if __name__ == "__main__":
    raise SystemExit(main())
