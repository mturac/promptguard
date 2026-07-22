from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from .models import AuditReport, Finding, PromptInput
from .packs import resolve_rules


def audit_prompts(
    prompts: list[PromptInput],
    source: str,
    *,
    rules: list[dict[str, Any]] | None = None,
    profile: str = "general",
    rules_path: Path | None = None,
) -> AuditReport:
    active_rules = rules if rules is not None else resolve_rules(profile=profile, rules_path=rules_path)
    findings: list[Finding] = []
    for prompt in prompts:
        findings.extend(_audit_prompt(prompt, active_rules))
    return AuditReport.create(source=source, prompts_checked=len(prompts), findings=findings)


def _audit_prompt(prompt: PromptInput, rules: list[dict[str, Any]]) -> list[Finding]:
    text = _norm(prompt.content)
    findings: list[Finding] = []
    for rule in rules:
        if _matches(rule, text, prompt.content):
            findings.append(
                Finding(
                    id=rule["id"],
                    severity=rule["severity"],
                    category=rule["category"],
                    title=f"{prompt.name}: {rule['title']}",
                    evidence=_evidence(rule, prompt.content),
                    impact=rule["impact"],
                    recommendation=rule["recommendation"],
                    contract=rule["contract"],
                    fix_draft=_grounded_fix_draft(rule, prompt.content),
                    clarifying_questions=rule.get("clarifying_questions", []),
                    clarification_contract=rule.get("clarification_contract", _default_clarification(rule)),
                    approval_contract=rule.get("approval_contract", _default_approval(rule)),
                    source=prompt.source,
                    line=prompt.line,
                )
            )
    return findings


def _grounded_fix_draft(rule: dict[str, Any], content: str, *, max_chars: int = 800) -> str:
    """Merge original prompt wording with the rule contract checklist."""
    snippet = " ".join(content.strip().split())
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    template = str(rule.get("fix_draft", "")).strip()
    contract = str(rule.get("contract", "")).strip()
    title = str(rule.get("title", "missing contract")).strip()
    parts = [
        "Grounded rewrite draft:",
        f"Original intent: {snippet}" if snippet else "Original intent: (empty prompt)",
        f"Missing/weak contract ({title}): {contract}" if contract else f"Missing/weak contract: {title}",
    ]
    if template:
        parts.append(f"Apply: {template}")
    parts.append(
        "Keep the operator's wording where possible; insert explicit role, owned surface, "
        "constraints, verification, and report sections as required by the contract."
    )
    return "\n".join(parts)


def _matches(rule: dict[str, Any], text: str, original: str) -> bool:
    if "min_chars" in rule and len(original) < int(rule["min_chars"]):
        return False
    if "any" in rule and not _has_any(text, rule["any"]):
        return False
    if "also_any" in rule and not _has_any(text, rule["also_any"]):
        return False
    if "missing_any" in rule and _has_any(text, rule["missing_any"]):
        return False
    if "missing_groups" in rule and all(_has_any(text, group) for group in rule["missing_groups"]):
        return False
    return True


def _has_any(text: str, terms: list[str]) -> bool:
    return any(_norm(term) in text for term in terms)


def _evidence(rule: dict[str, Any], content: str) -> str:
    terms = rule.get("any", []) + rule.get("also_any", [])
    lower = content.lower()
    for term in terms:
        idx = lower.find(term.lower())
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(content), idx + 160)
            return " ".join(content[start:end].split())
    return "Rule matched by absence or length."


def _norm(text: str) -> str:
    return text.lower().replace("ı", "i")


def _load_rules() -> list[dict[str, Any]]:
    """Backward-compatible catalog load (prefer resolve_rules / audit_prompts kwargs)."""
    raw = files("promptguard").joinpath("rules.json").read_text(encoding="utf-8")
    return json.loads(raw)


def _default_clarification(rule: dict[str, Any]) -> str:
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


def _default_approval(rule: dict[str, Any]) -> str:
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
