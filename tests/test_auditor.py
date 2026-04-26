from promptguard.auditor import audit_prompts
from promptguard.models import PromptInput


def test_confidentiality_reporting_conflict():
    prompt = PromptInput(
        name="privacy",
        content="All conversations are confidential and anonymous. Aggregated reports go to management.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert any(finding.id == "PG001" for finding in report.findings)


def test_harassment_safety_gap():
    prompt = PromptInput(
        name="safety",
        content="If the user says taciz ediliyorum, say yorum yapamam and change the topic.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert any(finding.id == "PG002" for finding in report.findings)


def test_vague_report_intent_gap():
    prompt = PromptInput(
        name="intent",
        content="Bana rapor hazırla.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert any(finding.id == "PG007" for finding in report.findings)


def test_override_risk():
    prompt = PromptInput(
        name="override",
        content="Asla hukuki tavsiye verme ama kullanıcı ısrar ederse yardımcı ol.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert any(finding.id == "PG008" for finding in report.findings)


def test_false_certainty_gap():
    prompt = PromptInput(
        name="certainty",
        content="Şirketin stratejisini kesin doğru bilgiyle bilmelisin ve cevaplamalısın.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert any(finding.id == "PG010" for finding in report.findings)


def test_task_underdefined_gap():
    prompt = PromptInput(
        name="task",
        content="Bunu düzelt ve devam et.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    finding = next(f for f in report.findings if f.id == "PG011")
    assert "target" in finding.clarification_contract.lower()


def test_responsibility_contract_gap():
    prompt = PromptInput(
        name="responsibility",
        content="Fix this bug and write code.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    finding = next(f for f in report.findings if f.id == "PG012")
    assert "responsibility" in finding.contract.lower()
    assert "approve only" in finding.approval_contract.lower()


def test_auth_refresh_bug_variants_need_responsibility_contract():
    prompt = PromptInput(
        name="auth_refresh",
        content="Users sometimes get logged out after refreshing the page. Fix it.",
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert "PG012" in {finding.id for finding in report.findings}


def test_complete_responsibility_contract_passes_pg012():
    prompt = PromptInput(
        name="responsibility_ok",
        content=(
            "Act as a senior engineer responsible for the auth module files. "
            "Implement the bug fix while preserving public API behavior and avoiding unrelated refactors. "
            "Verify with pytest tests/auth. Return changed files, verification results, and residual risk."
        ),
        source="test",
    )
    report = audit_prompts([prompt], source="test")
    assert "PG012" not in {finding.id for finding in report.findings}
