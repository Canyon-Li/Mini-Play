"""Mini-play DSL schema and validator.

Defines the pydantic models for the mini-play YAML DSL and provides a CLI
entry point for standalone validation + soft lint:

    python schema.py plays/<name>.yaml           # validate, then lint (WARN lines)
    python schema.py plays/<name>.yaml --strict  # lint warnings cause exit 1

The schema is the single source of truth for what a play looks like.
Renderers consume validated Play objects, never raw YAML.
"""

from __future__ import annotations

import argparse
import sys
from enum import Enum
from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Emotion(str, Enum):
    CONFUSED = "困惑"
    SURPRISED = "惊讶"
    PROUD = "得意"
    HELPLESS = "无奈"
    EXCITED = "兴奋"
    CALM = "平静"
    ANXIOUS = "焦虑"
    THINKING = "思考"


class AsideVariant(str, Enum):
    NOTE = "note"
    WARNING = "warning"
    INSIGHT = "insight"


class BeatLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["line"]
    who: str
    emotion: Emotion | None = None
    text: str


class BeatThought(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["thought"]
    who: str
    text: str


class BeatStageDirection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["stage_direction"]
    text: str
    label: str | None = None


class BeatAside(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["aside"]
    variant: AsideVariant = AsideVariant.NOTE
    text: str


class BeatCode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["code"]
    lang: str
    title: str | None = None
    text: str


class BeatTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["transition"]
    text: str


Beat = Union[
    BeatLine,
    BeatThought,
    BeatStageDirection,
    BeatAside,
    BeatCode,
    BeatTransition,
]


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    persona: str
    aliases: list[str] = Field(default_factory=list)
    backstory: str | None = None
    appearance: str | None = None


class Act(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    scene: str | None = None
    beats: list[Beat] = Field(min_length=1)


class ClosingTable(BaseModel):
    model_config = ConfigDict(extra="forbid")
    headers: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(default_factory=list)


class Closing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table: ClosingTable | None = None
    thesis: str


class RenderMetaHtml(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aside_collapse_default: bool = True
    theme: Literal["light", "dark"] = "light"


class RenderMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    html: RenderMetaHtml = Field(default_factory=RenderMetaHtml)


class Play(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    scene: str
    characters: list[Character] = Field(min_length=1)
    acts: list[Act] = Field(min_length=1)
    closing: Closing
    render_meta: RenderMeta = Field(default_factory=RenderMeta)

    @model_validator(mode="after")
    def _check_speaker_references(self) -> Play:
        names: set[str] = set()
        for ch in self.characters:
            names.add(ch.name)
            names.update(ch.aliases)
        for act in self.acts:
            for beat in act.beats:
                who = getattr(beat, "who", None)
                if who is not None and who not in names:
                    raise ValueError(
                        f"beat in act '{act.title}' references unknown speaker "
                        f"'{who}'. Known: {sorted(names)}"
                    )
        return self

    def alias_to_character(self) -> dict[str, Character]:
        """Map every speakable name (canonical or alias) to its character."""
        mapping: dict[str, Character] = {}
        for ch in self.characters:
            mapping[ch.name] = ch
            for alias in ch.aliases:
                mapping[alias] = ch
        return mapping

    def character_appearances(self) -> dict[str, list[str]]:
        """For each character (canonical name), the act titles where they speak.

        Beats addressed to an alias count toward the character, so HTML
        character cards never miss acts spoken under a nickname.
        """
        mapping = self.alias_to_character()
        result: dict[str, list[str]] = {ch.name: [] for ch in self.characters}
        for act in self.acts:
            speakers: set[str] = set()
            for beat in act.beats:
                who = getattr(beat, "who", None)
                if who is not None and who in mapping:
                    speakers.add(mapping[who].name)
            for name in speakers:
                result[name].append(act.title)
        return result


def load_play(path: str | Path) -> Play:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"play file not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Play.model_validate(raw)


MONOLOGUE_LIMIT = 4  # consecutive speaker beats by the same character in one act
THESIS_LIMIT = 100  # characters


def lint_play(play: Play) -> list[str]:
    """Check the soft lint rules from SKILL.md; return human-readable warnings."""
    warnings: list[str] = []
    alias_to_char = play.alias_to_character()
    appearances = play.character_appearances()

    # rule 1: no character defined but never speaking
    for ch in play.characters:
        if not appearances[ch.name]:
            warnings.append(f"角色「{ch.name}」定义了但从未发言（裸登场）")

    # rule 2: no monologue run of MONOLOGUE_LIMIT+ consecutive speaker beats in one act
    for act in play.acts:
        current, run = None, 0
        for beat in act.beats:
            who = getattr(beat, "who", None)
            if who is None or who not in alias_to_char:
                # a non-speaker beat (stage_direction / aside / code / transition)
                # breaks the run, same as a different speaker
                current, run = None, 0
                continue
            canon = alias_to_char[who].name
            if canon == current:
                run += 1
            else:
                current, run = canon, 1
            if run >= MONOLOGUE_LIMIT:
                warnings.append(
                    f"幕「{act.title}」：{canon} 连续独白 {run} 条"
                    f"（≥{MONOLOGUE_LIMIT}，建议拆成对话或插入舞台说明）"
                )
                current, run = None, 0

    # rule 3: closing table covers every character that spoke.
    # Only applies when the table is a roles table (first header mentions 角色);
    # a play may legitimately close with a different table shape (e.g. steps).
    table = play.closing.table
    if table is not None and table.headers and "角色" in table.headers[0]:
        listed: set[str] = set()
        for row in table.rows:
            if row:
                cell = row[0]
                listed.add(alias_to_char[cell].name if cell in alias_to_char else cell)
        missing = [ch.name for ch in play.characters if appearances[ch.name] and ch.name not in listed]
        if missing:
            warnings.append("谢幕表未覆盖登场角色：" + "、".join(missing))

    # rule 4: thesis length
    if len(play.closing.thesis) > THESIS_LIMIT:
        warnings.append(f"thesis 长度 {len(play.closing.thesis)} 字（建议 ≤ {THESIS_LIMIT}）")

    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and lint a mini-play DSL file.")
    parser.add_argument("play", help="path to .yaml play file")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on lint warnings")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        play = load_play(args.play)
    except Exception as e:
        print(f"INVALID: {e}", file=sys.stderr)
        return 1
    print(f"OK: {play.title} ({len(play.acts)} acts, {len(play.characters)} characters)")
    warnings = lint_play(play)
    for w in warnings:
        print(f"WARN: {w}")
    if warnings and args.strict:
        print(f"LINT FAILED: {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
