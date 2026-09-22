"""Mini-play DSL schema and validator.

Defines the pydantic models for the mini-play YAML DSL and provides a CLI
entry point for standalone validation:

    python schema.py plays/<name>.yaml

The schema is the single source of truth for what a play looks like.
Renderers consume validated Play objects, never raw YAML.
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


HERE = Path(__file__).parent


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
    beats: list[Beat] = Field(default_factory=list)


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

    @field_validator("acts")
    @classmethod
    def _acts_non_empty_beats(cls, v: list[Act]) -> list[Act]:
        for act in v:
            if not act.beats:
                raise ValueError(f"act '{act.title}' has no beats")
        return v

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

    def speaker_appearances(self) -> dict[str, list[tuple[str, int]]]:
        """For each character name, list (act_title, count) of speaking beats."""
        result: dict[str, list[tuple[str, int]]] = {ch.name: [] for ch in self.characters}
        for ch in self.characters:
            for alias in ch.aliases:
                result.setdefault(alias, [])
        for act in self.acts:
            local: dict[str, int] = {}
            for beat in act.beats:
                who = getattr(beat, "who", None)
                if who is not None:
                    local[who] = local.get(who, 0) + 1
            for who, count in local.items():
                result.setdefault(who, []).append((act.title, count))
        return result


def load_play(path: str | Path) -> Play:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"play file not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Play.model_validate(raw)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python schema.py <play.yaml>", file=sys.stderr)
        return 2
    try:
        play = load_play(args[0])
    except Exception as e:
        print(f"INVALID: {e}", file=sys.stderr)
        return 1
    print(f"OK: {play.title} ({len(play.acts)} acts, {len(play.characters)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
