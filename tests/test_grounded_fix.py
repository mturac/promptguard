from promptguard.auditor import audit_prompts, _grounded_fix_draft
from promptguard.models import PromptInput


def test_grounded_fix_contains_original_substring():
    content = "Prod auth refresh bug UNIQUE_TOKEN_42 — fixler misin akşama deploy."
    prompt = PromptInput(name="bug", content=content, source="t")
    report = audit_prompts([prompt], source="t", profile="coding-agent")
    assert report.findings
    drafts = " ".join(f.fix_draft for f in report.findings)
    assert "UNIQUE_TOKEN_42" in drafts
    assert "Grounded rewrite draft" in drafts
    assert "Original intent" in drafts


def test_grounded_helper_shortens_long_prompt():
    rule = {
        "title": "t",
        "contract": "c",
        "fix_draft": "template fix",
    }
    long = "word " * 500
    draft = _grounded_fix_draft(rule, long, max_chars=100)
    assert "…" in draft
    assert "template fix" in draft
    assert len(draft) < len(long) + 200
