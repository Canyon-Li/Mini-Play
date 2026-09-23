"""Shared pytest fixtures for the mini-play test suite."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "mini-play"
sys.path.insert(0, str(SKILL_DIR))


@pytest.fixture
def build_play(tmp_path):
    """Write a play YAML from Python structures and return its path."""

    def _build(
        *,
        title: str = "测试剧本",
        characters: list | None = None,
        acts: list | None = None,
        thesis: str = "一句话点题",
        table: dict | None = None,
        name: str = "play.yaml",
    ) -> Path:
        doc = {
            "title": title,
            "scene": "场景",
            "characters": characters or [{"name": "A", "persona": "主角"}],
            "acts": acts or [{"title": "第一幕", "beats": [{"type": "line", "who": "A", "text": "你好"}]}],
            "closing": {"thesis": thesis},
        }
        if table:
            doc["closing"]["table"] = table
        path = tmp_path / name
        path.write_text(yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")
        return path

    return _build
