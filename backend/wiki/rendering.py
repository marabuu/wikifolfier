"""Markdown -> HTML rendering and internal link extraction.

The very same renderer is used by the API, by the editor preview and by the
importer, so preview and final page are guaranteed to be identical.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import bleach
import markdown as markdown_lib

ALLOWED_TAGS = [
    "p", "br", "hr", "em", "strong", "i", "b", "u", "sup", "sub", "code", "pre",
    "blockquote", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "span", "div",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "class", "data-page-slug"],
    "img": ["src", "alt", "title", "width", "height"],
    "td": ["colspan", "rowspan", "align", "class"],
    "th": ["colspan", "rowspan", "align", "class", "scope"],
    "span": ["class"],
    "div": ["class"],
    "code": ["class"],
}

WIKIDOT_INTERNAL_PREFIXES = ("/", "#")


@dataclass
class RenderResult:
    html: str
    internal_links: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CompendiumMarkdown(markdown_lib.Markdown):
    """Markdown with tables + fenced code blocks enabled."""

    def __init__(self):
        super().__init__(extensions=["extra", "sane_lists", "nl2br"])


_md = CompendiumMarkdown()

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _reset():
    _md.reset()


def render(markdown_text: str, base_path: str = "") -> RenderResult:
    """Render markdown to sanitized HTML and collect internal link references."""
    text = markdown_text or ""
    _reset()
    html = _md.convert(text)
    cleaned = bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=False
    )

    internal: list[tuple[str, str]] = []
    for label, href in LINK_RE.findall(text):
        if href.startswith(WIKIDOT_INTERNAL_PREFIXES) or not re.match(r"^[a-z]+://", href):
            if href.startswith("/"):
                slug = href.strip("/").split("/")[-1]
                internal.append((slug, label))

    return RenderResult(html=cleaned, internal_links=internal)


def strip_html(html: str, limit: int = 220) -> str:
    text = bleach.clean(html or "", tags=[], strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]