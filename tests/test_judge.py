import json
from unittest.mock import MagicMock, patch

import pytest

from promptguard.judge import JudgeError, annotate_findings_with_judge, _parse_notes
from promptguard.models import Finding


def _f() -> Finding:
    return Finding(
        id="PG012",
        severity="high",
        category="c",
        title="t",
        evidence="e",
        impact="base impact",
        recommendation="r",
        contract="c",
        fix_draft="f",
        clarifying_questions=[],
        clarification_contract="cc",
        approval_contract="ac",
        source="s",
        line=1,
    )


def test_parse_notes_json():
    notes = _parse_notes('{"notes":[{"id":"PG012","note":"missing role","priority":1}]}')
    assert notes[0]["id"] == "PG012"


def test_annotate_appends_judge_note():
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {"notes": [{"id": "PG012", "note": "add owner surface", "priority": 1}]}
                    )
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch.dict(
        "os.environ",
        {"TURAC_LLM_ROUTER_URL": "http://localhost:8000", "TURAC_LLM_ROUTER_KEY": "k"},
        clear=False,
    ):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            out = annotate_findings_with_judge([_f()], prompt_excerpt="Fix bug")
    assert "judge" in out[0].impact
    assert "add owner surface" in out[0].impact


def test_judge_error_on_network_fail():
    with patch.dict(
        "os.environ",
        {"TURAC_LLM_ROUTER_URL": "http://localhost:8000", "TURAC_LLM_ROUTER_KEY": "k"},
        clear=False,
    ):
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(JudgeError):
                annotate_findings_with_judge([_f()], prompt_excerpt="x")
