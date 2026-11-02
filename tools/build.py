#!/usr/bin/env python3
"""Assemble the static site.

Each file in tools/pages/ is a page body with a small front-matter block:

    ---
    title: Page title
    description: Meta description
    ---
    <section>...</section>

The body is wrapped in tools/layout.html and written to site/<name>.html.
Run:  python3 tools/build.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / "site"
LAYOUT = (ROOT / "layout.html").read_text(encoding="utf-8")


def inline_emblem(css_class: str) -> str:
    """The traced emblem (site/images/emblem.svg) inlined so CSS can animate its parts."""
    svg = (SITE / "images/emblem.svg").read_text(encoding="utf-8")
    svg = svg.replace("<svg ", f'<svg class="{css_class}" ', 1)
    return svg


def build_page(src: Path) -> None:
    raw = src.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"{src.name}: missing front matter")
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    body = m.group(2)

    slug = src.stem
    canonical = "" if slug == "index" else f"{slug}.html"
    html = LAYOUT
    html = html.replace("{{title}}", meta["title"])
    html = html.replace("{{description}}", meta["description"])
    html = html.replace("{{canonical}}", canonical)
    html = html.replace("{{slug}}", slug)
    body = body.replace("{{emblem-svg}}", inline_emblem("emblem emblem--hero"))
    html = html.replace("{{body}}", body.rstrip("\n"))
    html = re.sub(
        r"\{\{active:([a-z-]+)\}\}",
        lambda mm: 'aria-current="page"' if mm.group(1) == slug else "",
        html,
    )
    html = re.sub(r" +(?=>)", "", html)  # tidy trailing spaces left by empty tokens
    (SITE / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"built  site/{slug}.html")


if __name__ == "__main__":
    SITE.mkdir(exist_ok=True)
    for page in sorted((ROOT / "pages").glob("*.html")):
        build_page(page)
