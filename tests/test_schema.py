"""Schema validation and character/alias resolution tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from schema import lint_play, load_play

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "mini-play"
EXAMPLES = sorted((SKILL_DIR / "plays").glob("*.yaml"))


def test_example_plays_validate_and_lint_clean():
    assert EXAMPLES, "example plays not found"
    for p in EXAMPLES:
        play = load_play(p)
        assert lint_play(play) == []


def test_empty_beats_rejected(build_play):
    p = build_play(acts=[{"title": "第一幕", "beats": []}])
    with pytest.raises(ValidationError):
        load_play(p)


def test_unknown_speaker_rejected(build_play):
    p = build_play(
        acts=[{"title": "第一幕", "beats": [{"type": "line", "who": "幽灵", "text": "hi"}]}],
    )
    with pytest.raises(ValidationError):
        load_play(p)


def test_typo_field_rejected(build_play):
    p = build_play(characters=[{"name": "A", "persona": "主角", "perso": "typo"}])
    with pytest.raises(ValidationError):
        load_play(p)


def test_alias_beats_count_toward_canonical_character(build_play):
    p = build_play(
        characters=[{"name": "LLM", "persona": "p", "aliases": ["大模型"]}],
        acts=[{"title": "第一幕", "beats": [{"type": "line", "who": "大模型", "text": "hi"}]}],
    )
    assert load_play(p).character_appearances() == {"LLM": ["第一幕"]}
