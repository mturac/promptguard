from pathlib import Path

from promptguard.extractors import extract_prompts

FIXTURES = Path(__file__).parent / "fixtures" / "extractors"


def test_agents_md_extracts_whole_and_sections():
    path = FIXTURES / "AGENTS.md"
    prompts = extract_prompts(path)
    names = {p.name for p in prompts}
    assert path.name in names or "AGENTS.md" in names
    assert any("system" in p.name.lower() or "You are the coding agent" in p.content for p in prompts)
    assert any("Verify with pytest" in p.content for p in prompts)
    assert all(p.line is not None and p.line >= 1 for p in prompts)


def test_json_prompt_keys_nested():
    path = FIXTURES / "config.json"
    prompts = extract_prompts(path)
    contents = {p.content for p in prompts}
    assert "You are a router." in contents
    assert "Route carefully." in contents
    assert all(p.source == str(path) for p in prompts)


def test_json_without_prompt_keys_returns_empty():
    path = FIXTURES / "empty.json"
    prompts = extract_prompts(path)
    assert prompts == []


def test_yaml_block_and_inline_prompt_keys():
    path = FIXTURES / "bot.yaml"
    prompts = extract_prompts(path)
    by_name = {p.name: p for p in prompts}
    assert "system" in by_name
    assert "You are system." in by_name["system"].content
    assert "Stay on topic." in by_name["system"].content
    assert by_name["prompt"].content == "short prompt"
    assert by_name["system"].line is not None


def test_python_prompts_dict_still_works(tmp_path: Path):
    py = tmp_path / "prompts.py"
    py.write_text(
        'PROMPTS = {"router": "You must route with schema."}\n',
        encoding="utf-8",
    )
    prompts = extract_prompts(py)
    assert len(prompts) == 1
    assert prompts[0].name == "router"
    assert "route" in prompts[0].content


def test_plain_text_fallback(tmp_path: Path):
    p = tmp_path / "notes.txt"
    p.write_text("plain content", encoding="utf-8")
    prompts = extract_prompts(p)
    assert len(prompts) == 1
    assert prompts[0].content == "plain content"
