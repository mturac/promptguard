from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

Severity = Literal["critical", "high", "medium", "low", "info"]


@dataclass(frozen=True)
class PromptInput:
    name: str
    content: str
    source: str
    line: int | None = None


@dataclass(frozen=True)
class Finding:
    id: str
    severity: Severity
    category: str
    title: str
    evidence: str
    impact: str
    recommendation: str
    contract: str
    fix_draft: str
    clarifying_questions: list[str]
    clarification_contract: str
    approval_contract: str
    source: str
    line: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    created_at: str
    source: str
    prompts_checked: int
    findings: list[Finding]

    @classmethod
    def create(cls, source: str, prompts_checked: int, findings: list[Finding]) -> "AuditReport":
        return cls(
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
            prompts_checked=prompts_checked,
            findings=findings,
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["findings"] = [finding.to_dict() for finding in self.findings]
        return data
