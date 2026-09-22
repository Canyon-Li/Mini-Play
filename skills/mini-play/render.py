"""Mini-play renderer: DSL → Markdown / HTML.

Usage:
    python render.py markdown plays/<name>.yaml
    python render.py html plays/<name>.yaml
    python render.py markdown plays/<name>.yaml --out custom.md

Output defaults to <play_dir>/<slug>.<ext>, next to the source YAML.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from schema import lint_play, load_play

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"


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
    return env


def render(play_path: str | Path, fmt: str, out_path: str | Path | None = None) -> Path:
    play = load_play(play_path)
    for w in lint_play(play):
        print(f"WARN: {w}", file=sys.stderr)
    env = _build_env(fmt)
    template_name = {"markdown": "markdown.j2", "html": "html.j2"}.get(fmt)
    if template_name is None:
        raise ValueError(f"unsupported format: {fmt} (expected markdown or html)")
    template = env.get_template(template_name)

    extra = {"appearances": play.character_appearances()}
    if play.closing.table:
        headers = play.closing.table.headers
        extra["table_header"] = "| " + " | ".join(headers) + " |"
        extra["table_separator"] = "|" + "---|" * len(headers)

    rendered = template.render(play=play, **extra)

    slug = _slugify(play.title)
    ext = "md" if fmt == "markdown" else "html"
    if out_path is None:
        out = Path(play_path).parent / f"{slug}.{ext}"
    else:
        out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a mini-play DSL file.")
    parser.add_argument("format", choices=["markdown", "html"], help="output format")
    parser.add_argument("play", help="path to .yaml play file")
    parser.add_argument("--out", default=None, help="output file path (default: <play_dir>/<slug>.<ext>)")
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
