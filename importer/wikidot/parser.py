"""Wikidot -> AST -> Markdown conversion.

Deliberately modular: one module per construct. Anything not understood is
reported as a warning and its original text is preserved — content is never
silently dropped.
"""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass, field

from .modules import handle_module

log = logging.getLogger("importer.parser")


@dataclass
class Warning_:
    construct: str
    snippet: str
    page: str = ""


@dataclass
class ParseResult:
    markdown: str
    links: list[tuple[str, str]] = field(default_factory=list)  # (slug, text)
    images: list[str] = field(default_factory=list)
    subtitle: str = ""
    source_label: str = ""
    warnings: list[Warning_] = field(default_factory=list)
    unknown_constructs: list[str] = field(default_factory=list)


# --- individual construct handlers ------------------------------------

HEADING_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
LINK_RE = re.compile(r"<a\b[^>]*href=\"(?P<href>[^\"]*)\"[^>]*>(?P<text>.*?)</a>", re.IGNORECASE | re.DOTALL)
IMG_RE = re.compile(r"<img\b[^>]*src=\"(?P<src>[^\"]*)\"[^>]*>", re.IGNORECASE)
BOLD_RE = re.compile(r"<b>(.*?)</b>", re.IGNORECASE | re.DOTALL)
ITALIC_RE = re.compile(r"<i>(.*?)</i>", re.IGNORECASE | re.DOTALL)
BOLD2_RE = re.compile(r"\*\*\*(.*?)\*\*\*", re.DOTALL)
ITALIC2_RE = re.compile(r"//(.*?)//", re.DOTALL)
WIKIDOT_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
WIKIDOT_ITALIC_RE = re.compile(r"//(.+?)//", re.DOTALL)

MODULE_RE = re.compile(
    r"<div\s[^>]*class=\"[^\"]*\bmodule\b[^\"]*\"[^>]*data-options="
    r"(?P<quote>[\"'])(?P<opts>.*?)(?P=quote)[^>]*>(?P<body>.*?)</div>",
    re.IGNORECASE | re.DOTALL,
)

TABLE_RE = re.compile(r"<table[^>]*>(?P<body>.*?)</table>", re.IGNORECASE | re.DOTALL)
TR_RE = re.compile(r"<tr[^>]*>(?P<body>.*?)</tr>", re.IGNORECASE | re.DOTALL)
TH_RE = re.compile(r"<th[^>]*>(?P<body>.*?)</th>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td[^>]*>(?P<body>.*?)</td>", re.IGNORECASE | re.DOTALL)

LIST_RE = re.compile(r"<(ul|ol)[^>]*>(?P<body>.*?)</\1>", re.IGNORECASE | re.DOTALL)
LI_RE = re.compile(r"<li[^>]*>(?P<body>.*?)</li>", re.IGNORECASE | re.DOTALL)

DIV_RE = re.compile(r"<(div|span)[^>]*>(?P<body>.*?)</\1>", re.IGNORECASE | re.DOTALL)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
HR_RE = re.compile(r"<hr\s*/?>", re.IGNORECASE)
PARA_RE = re.compile(r"<p[^>]*>(?P<body>.*?)</p>", re.IGNORECASE | re.DOTALL)

# Wikidot component tags -> plain text (we keep the content).
COMPONENT_RE = re.compile(r"<(percent|color|size|span)[^>]*>", re.IGNORECASE)


def _cell_text(text: str) -> str:
    """Table cell text: keeps bold/italic markers, drops tags."""
    text = BOLD_RE.sub(r"**\1**", text)
    text = ITALIC_RE.sub(r"*\1*", text)
    return strip_tags(text)


def strip_tags(text: str) -> str:
    text = COMPONENT_RE.sub("", text)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()
class WikidotParser:
    """Converts a raw Wikidot page body into Markdown."""

    def parse(self, raw_html: str, page_path: str = "") -> ParseResult:
        result = ParseResult(markdown="")
        text = raw_html or ""

        # Modules carry data in data-options; we keep their text and flag them.
        def module_repl(match: re.Match) -> str:
            options = html.unescape(match.group("opts") or "")
            class_match = re.search(r'class="([^"]*)"', match.group(0))
            class_name = class_match.group(1) if class_match else "module"
            handled = handle_module(class_name, options, strip_tags(match.group("body")))
            if handled.understood:
                return handled.markdown
            result.unknown_constructs.append(handled.name)
            result.warnings.append(Warning_(handled.name, handled.markdown[:120], page_path))
            return handled.markdown

        text = MODULE_RE.sub(module_repl, text)

        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
        if title_match:
            captions = re.findall(
                r'<div[^>]*class="[^"]*caption[^"]*"[^>]*>(.*?)</div>',
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if captions:
                result.subtitle = strip_tags(captions[0])
            text = text.replace(title_match.group(0), "", 1)

        plain = strip_tags(text)
        source_match = re.search(r"Source:\s*([A-Za-z0-9'’. ]{3,60})", plain)
        if source_match:
            result.source_label = source_match.group(1).strip()

        def img_repl(match: re.Match) -> str:
            src = match.group("src")
            result.images.append(src)
            return f"\n![{src.rsplit('/', 1)[-1]}]({src})\n"

        text = IMG_RE.sub(img_repl, text)

        def link_repl(match: re.Match) -> str:
            href = html.unescape(match.group("href"))
            label = strip_tags(match.group("text"))
            if href.startswith("http"):
                return f"[{label}]({href})"
            slug = href.strip("/").split("/")[-1]
            if slug.startswith("#") or not slug:
                return label
            from .links import path_to_slug

            normalized = path_to_slug(slug)
            if normalized:
                result.links.append((normalized, label))
            return f"[{label}](/{normalized})"

        text = LINK_RE.sub(link_repl, text)
        text = TABLE_RE.sub(self._table_to_markdown, text)
        text = LIST_RE.sub(self._list_to_markdown, text)
        text = HEADING_RE.sub(self._heading_to_markdown, text)
        text = BOLD_RE.sub(r"**\1**", text)
        text = ITALIC_RE.sub(r"*\1*", text)
        text = BOLD2_RE.sub(r"**\1**", text)
        text = ITALIC2_RE.sub(r"*\1*", text)
        text = PARA_RE.sub(lambda m: f"\n\n{strip_tags(m.group('body'))}\n\n", text)
        text = DIV_RE.sub(lambda m: m.group("body"), text)
        text = BR_RE.sub("\n", text)
        text = HR_RE.sub("\n---\n", text)
        text = strip_tags(text)

        result.markdown = self._tidy(text)
        return result

    @staticmethod
    def _heading_to_markdown(match: re.Match) -> str:
        level = min(int(match.group(1)) + 1, 6)
        return f"\n\n{'#' * level} {strip_tags(match.group(2))}\n\n"

    @staticmethod
    def _table_to_markdown(match: re.Match) -> str:
        rows: list[list[str]] = []
        for row_match in TR_RE.finditer(match.group("body")):
            cells = [
                _cell_text(cell.group("body"))
                for cell in list(TH_RE.finditer(row_match.group("body")))
                + list(TD_RE.finditer(row_match.group("body")))
            ]
            if cells:
                rows.append(cells)
        if not rows:
            return strip_tags(match.group("body"))

        width = max(len(row) for row in rows)
        lines = []
        for index, row in enumerate(rows):
            padded = row + [""] * (width - len(row))
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in padded) + " |")
            if index == 0:
                lines.append("| " + " | ".join(["---"] * width) + " |")
        return "\n\n" + "\n".join(lines) + "\n\n"

    @staticmethod
    def _list_to_markdown(match: re.Match) -> str:
        tag = match.group(1).lower()
        lines = []
        for item in LI_RE.finditer(match.group("body")):
            bullet = "1." if tag == "ol" else "-"
            lines.append(f"{bullet} {strip_tags(item.group('body'))}")
        return "\n" + "\n".join(lines) + "\n"

    @staticmethod
    def _tidy(text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.strip() for line in text.splitlines()).strip()