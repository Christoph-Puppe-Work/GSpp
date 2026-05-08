import pytest
from shared.prompts import load_prompt
from pathlib import Path

def test_load_prompt_with_frontmatter(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "test_prompt.md"
    prompt_file.write_text("---\nkey: value\n---\nHello World", encoding="utf-8")

    # Monkeypatch _PROMPTS_DIR in shared.prompts
    import shared.prompts
    original_dir = shared.prompts._PROMPTS_DIR
    shared.prompts._PROMPTS_DIR = prompt_dir

    try:
        content = load_prompt("test_prompt")
        assert content == "Hello World"
    finally:
        shared.prompts._PROMPTS_DIR = original_dir

def test_load_prompt_no_frontmatter(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "plain_prompt.md"
    prompt_file.write_text("Just text", encoding="utf-8")

    import shared.prompts
    original_dir = shared.prompts._PROMPTS_DIR
    shared.prompts._PROMPTS_DIR = prompt_dir

    try:
        content = load_prompt("plain_prompt")
        assert content == "Just text"
    finally:
        shared.prompts._PROMPTS_DIR = original_dir
