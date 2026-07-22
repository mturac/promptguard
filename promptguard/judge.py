from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .models import Finding

DEFAULT_ROUTER = "http://localhost:8000"
DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"


class JudgeError(RuntimeError):
    """LLM judge call failed."""


def judge_enabled() -> bool:
    return bool(os.environ.get("TURAC_LLM_ROUTER_URL") or os.environ.get("TURAC_LLM_ROUTER_KEY"))


def annotate_findings_with_judge(
    findings: list[Finding],
    *,
    prompt_excerpt: str,
    timeout_s: float = 30.0,
) -> list[Finding]:
    """Opt-in second pass: ask router to rank/comment findings.

    Default product path stays offline. Requires:
      TURAC_LLM_ROUTER_URL (default http://localhost:8000)
      TURAC_LLM_ROUTER_KEY (Bearer)
    """
    if not findings:
        return findings
    base = os.environ.get("TURAC_LLM_ROUTER_URL", DEFAULT_ROUTER).rstrip("/")
    key = os.environ.get("TURAC_LLM_ROUTER_KEY", "")
    model = os.environ.get("PROMPTGUARD_JUDGE_MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PromptGuard judge. Given a prompt excerpt and static findings, "
                    "return JSON only: {\"notes\":[{\"id\":\"PG012\",\"note\":\"...\",\"priority\":1}]}. "
                    "Do not invent rule ids. Keep notes short. priority 1=most important."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "prompt_excerpt": prompt_excerpt[:4000],
                        "findings": [
                            {
                                "id": f.id,
                                "severity": f.severity,
                                "title": f.title,
                                "contract": f.contract,
                            }
                            for f in findings
                        ],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "max_tokens": 800,
        "temperature": 0,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise JudgeError(f"judge request failed: {exc}") from exc

    content = (
        raw.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    notes = _parse_notes(content)
    if not notes:
        return findings

    by_id = {n["id"]: n for n in notes if "id" in n}
    enriched: list[Finding] = []
    for finding in findings:
        note = by_id.get(finding.id)
        if not note:
            enriched.append(finding)
            continue
        priority = note.get("priority", "")
        note_text = str(note.get("note", "")).strip()
        extra = f" [judge p{priority}] {note_text}" if note_text else f" [judge p{priority}]"
        enriched.append(
            Finding(
                id=finding.id,
                severity=finding.severity,
                category=finding.category,
                title=finding.title,
                evidence=finding.evidence,
                impact=finding.impact + extra,
                recommendation=finding.recommendation,
                contract=finding.contract,
                fix_draft=finding.fix_draft,
                clarifying_questions=finding.clarifying_questions,
                clarification_contract=finding.clarification_contract,
                approval_contract=finding.approval_contract,
                source=finding.source,
                line=finding.line,
            )
        )
    return enriched


def _parse_notes(content: str) -> list[dict[str, Any]]:
    text = content.strip()
    if not text:
        return []
    # strip markdown fences if present
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return []
        else:
            return []
    notes = data.get("notes") if isinstance(data, dict) else None
    return notes if isinstance(notes, list) else []
