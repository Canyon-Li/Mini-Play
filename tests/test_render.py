"""Renderer output-location and escaping tests."""
from __future__ import annotations

from pathlib import Path

from render import render

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "mini-play"
EXAMPLES = sorted((SKILL_DIR / "plays").glob("*.yaml"))


def test_output_defaults_next_to_source(build_play):
    p = build_play(title="落点")
    assert render(p, "html") == p.parent / "落点.html"
    assert render(p, "markdown") == p.parent / "落点.md"


def test_out_override(build_play, tmp_path):
    custom = tmp_path / "custom.html"
    assert render(build_play(), "html", custom) == custom
    assert custom.exists()


def test_html_escapes_script_and_ampersand(build_play):
    p = build_play(
        acts=[{
            "title": "第一幕",
            "beats": [
                {"type": "line", "who": "A", "text": "包含 <script>alert(1)</script> 和 & 符号"},
                {"type": "code", "lang": "python", "text": "a & b < c"},
            ],
        }],
    )
    html = render(p, "html").read_text(encoding="utf-8")
    assert "<script>alert" not in html  # the template's own <script> tag is fine
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&amp;amp;" not in html  # no double escaping
    assert "a &amp; b &lt; c" in html


def test_markdown_stays_raw(build_play):
    p = build_play(
        acts=[{
            "title": "第一幕",
            "beats": [
                {"type": "line", "who": "A", "text": "包含 <b> 和 & 符号"},
                {"type": "code", "lang": "python", "text": "a & b < c"},
            ],
        }],
    )
    md = render(p, "markdown").read_text(encoding="utf-8")
    assert "包含 <b> 和 & 符号" in md
    assert "a & b < c" in md


def test_example_plays_render_both_formats(tmp_path):
    assert EXAMPLES, "example plays not found"
    for src in EXAMPLES:
        for fmt, ext in [("html", "html"), ("markdown", "md")]:
            out = render(src, fmt, tmp_path / f"{src.stem}.{ext}")
            assert len(out.read_text(encoding="utf-8")) > 500
