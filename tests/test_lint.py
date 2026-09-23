"""Soft lint rule tests."""
from __future__ import annotations

from schema import lint_play, load_play, main


def line(who: str, n: int = 1) -> list[dict]:
    return [{"type": "line", "who": who, "text": f"line {i}"} for i in range(n)]


def warnings_of(build_play, **kw) -> list[str]:
    return lint_play(load_play(build_play(**kw)))


def test_mute_character_flagged(build_play):
    w = warnings_of(
        build_play,
        characters=[{"name": "A", "persona": "p"}, {"name": "Ghost", "persona": "p"}],
    )
    assert any("Ghost" in x and "裸登场" in x for x in w)


def test_monologue_run_flagged(build_play):
    w = warnings_of(build_play, acts=[{"title": "第一幕", "beats": line("A", 4)}])
    assert any("连续独白 4 条" in x for x in w)


def test_stage_direction_breaks_monologue_run(build_play):
    beats = line("A", 3) + [{"type": "stage_direction", "text": "灯光变暗"}] + line("A", 3)
    w = warnings_of(build_play, acts=[{"title": "第一幕", "beats": beats}])
    assert not any("独白" in x for x in w)


def test_long_thesis_flagged(build_play):
    w = warnings_of(build_play, thesis="长" * 101)
    assert any("thesis" in x for x in w)


def test_closing_table_coverage(build_play):
    w = warnings_of(
        build_play,
        characters=[{"name": "A", "persona": "p"}, {"name": "B", "persona": "q"}],
        acts=[{"title": "第一幕", "beats": line("A") + line("B")}],
        table={"headers": ["角色", "做什么"], "rows": [["A", "提问"]]},
    )
    assert any("谢幕表未覆盖登场角色：B" in x for x in w)


def test_non_role_closing_table_skips_coverage(build_play):
    w = warnings_of(
        build_play,
        characters=[{"name": "A", "persona": "p"}, {"name": "B", "persona": "q"}],
        acts=[{"title": "第一幕", "beats": line("A") + line("B")}],
        table={"headers": ["Graph 的步骤", "痛点"], "rows": [["step1", "x"]]},
    )
    assert not any("谢幕表" in x for x in w)


def test_cli_strict_exit_code(build_play):
    assert main([str(build_play())]) == 0
    dirty = str(build_play(thesis="长" * 101))
    assert main([dirty]) == 0
    assert main([dirty, "--strict"]) == 1
