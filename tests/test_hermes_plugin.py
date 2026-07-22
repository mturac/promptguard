import importlib.util
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters" / "hermes" / "plugin" / "__init__.py"


def _load():
    spec = importlib.util.spec_from_file_location("hermes_promptguard_plugin", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_non_write_tool_passthrough():
    mod = _load()
    assert mod.pre_tool_call("web_search", {"query": "x"}) is None


def test_write_without_prompt_hint_passthrough():
    mod = _load()
    assert mod.pre_tool_call("write_file", {"path": "src/main.py", "content": "print(1)"}) is None


def test_blocks_when_audit_exits_one():
    mod = _load()

    def fake_run(cmd, capture_output=True, text=True, timeout=60):
        class R:
            returncode = 1
            stdout = "## HIGH PG012\n"
            stderr = ""

        return R()

    with patch.object(mod.subprocess, "run", side_effect=fake_run):
        result = mod.pre_tool_call(
            "write_file",
            {
                "path": "AGENTS.md",
                "content": "Fix this bug and write code. system prompt stuff.",
            },
        )
    assert result is not None
    assert result["action"] == "block"
    assert "PromptGuard" in result["message"]


def test_disable_env():
    mod = _load()
    with patch.dict(mod.os.environ, {"PROMPTGUARD_HERMES_DISABLE": "1"}):
        assert (
            mod.pre_tool_call(
                "write_file",
                {"path": "prompt.md", "content": "system prompt ignore previous"},
            )
            is None
        )
