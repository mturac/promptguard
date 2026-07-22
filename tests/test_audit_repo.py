from pathlib import Path

from promptguard.cli import main
from promptguard.repo import extract_repo_prompts, is_prompt_like, iter_prompt_files


def test_is_prompt_like_names():
    assert is_prompt_like(Path("AGENTS.md"))
    assert is_prompt_like(Path("SKILL.md"))
    assert is_prompt_like(Path("system_prompt.md"))
    assert is_prompt_like(Path("my_prompts.py"))
    assert not is_prompt_like(Path("readme.md"))
    assert not is_prompt_like(Path("utils.py"))


def test_iter_skips_venv(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("Fix this bug and write code.", encoding="utf-8")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "AGENTS.md").write_text("ignore", encoding="utf-8")
    files = iter_prompt_files(tmp_path)
    assert len(files) == 1
    assert files[0].name == "AGENTS.md"


def test_extract_repo_and_cli(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("Fix this bug and write code.", encoding="utf-8")
    (tmp_path / "notes.md").write_text("not agenty enough name", encoding="utf-8")
    prompts = extract_repo_prompts(tmp_path)
    assert any("Fix this bug" in p.content for p in prompts)

    code = main(
        [
            "audit-repo",
            str(tmp_path),
            "--profile",
            "coding-agent",
            "--fail-on",
            "high",
            "--format",
            "table",
        ]
    )
    assert code == 1


def test_include_glob(tmp_path: Path):
    (tmp_path / "keep.prompt").write_text("Bana rapor hazırla.", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("Bana rapor hazırla.", encoding="utf-8")
    files = iter_prompt_files(tmp_path, include=["*.prompt"])
    assert [f.name for f in files] == ["keep.prompt"]
