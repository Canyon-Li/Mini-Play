"""Mini-play renderer: DSL → Markdown / HTML.

Usage:
    python render.py markdown plays/<name>.yaml
    python render.py html plays/<name>.yaml
    python render.py markdown plays/<name>.yaml --out custom.md

Output defaults to plays/build/<slug>.<ext>.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"
DEFAULT_OUT = HERE / "plays" / "build"

from schema import load_play


def _slugify(title: str) -> str:
    """Make a filesystem-friendly slug from a (Chinese) title."""
    s = re.sub(r"[\\/:*?\"<>|]+", "_", title.strip())
    s = re.sub(r"\s+", "_", s)
    return s or "play"


def _build_env(fmt: str) -> Environment:
    """Escape only for HTML. Templates end in .j2, so select_autoescape's
    extension matching would silently disable escaping for them."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=(fmt == "html"),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def _trim_end(s: str) -> str:
        return (s or "").rstrip()

    env.filters["trim_end"] = _trim_end
    env.filters["rstrip"] = _trim_end
    return env


def _appearances_map(play) -> dict[str, list[str]]:
    """Map each character name to the list of act titles where they speak."""
    result: dict[str, list[str]] = {ch.name: [] for ch in play.characters}
    for ch in play.characters:
        for alias in ch.aliases:
            result.setdefault(alias, [])
    for act in play.acts:
        speakers_in_act: set[str] = set()
        for beat in act.beats:
            who = getattr(beat, "who", None)
            if who is not None:
                speakers_in_act.add(who)
        for who in speakers_in_act:
            result.setdefault(who, []).append(act.title)
    return result


def render(play_path: str | Path, fmt: str, out_path: str | Path | None = None) -> Path:
    play = load_play(play_path)
    env = _build_env(fmt)
    template_name = {"markdown": "markdown.j2", "html": "html.j2"}.get(fmt)
    if template_name is None:
        raise ValueError(f"unsupported format: {fmt} (expected markdown or html)")
    template = env.get_template(template_name)

    extra = {"appearances": _appearances_map(play)}
    if play.closing.table:
        headers = play.closing.table.headers
        extra["table_header"] = "| " + " | ".join(headers) + " |"
        extra["table_separator"] = "|" + "---|" * len(headers)

    rendered = template.render(play=play, **extra)

    slug = _slugify(play.title)
    ext = "md" if fmt == "markdown" else "html"
    if out_path is None:
        out = DEFAULT_OUT / f"{slug}.{ext}"
    else:
        out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a mini-play DSL file.")
    parser.add_argument("format", choices=["markdown", "html"], help="output format")
    parser.add_argument("play", help="path to .yaml play file")
    parser.add_argument("--out", default=None, help="output file path (default: plays/build/<slug>.<ext>)")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        out = render(args.play, args.format, args.out)
    except Exception as e:
        print(f"RENDER FAILED: {e}", file=sys.stderr)
        return 1
    print(f"OK: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
