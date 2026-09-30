"""Wikidot HTML -> Markdown, tuned to the real page structure.

Observed on dnd2024.wikidot.com:
- the article is plain server-rendered HTML inside #page-content
- a spell header is a run of <p> with <strong>Label:</strong> and <br>
- section headings are <strong><em>Title.</em></strong> inside <p>, or <h2>/<h3>
- tables use <table class="wiki-content-table"> with colspan header rows
"""
from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass, field

from .extract import extract_article, extract_tags, extract_title
from .modules import handle_module


@dataclass
class Warning_:
    construct: str
    snippet: str
    page: str = ""


@dataclass
class ParseResult:
    markdown: str = ""
    title: str = ""
    subtitle: str = ""
    tags: list[str] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    source_label: str = ""
    header_lines: list[str] = field(default_factory=list)
    warnings: list[Warning_] = field(default_factory=list)
    unknown_constructs: list[str] = field(default_factory=list)


# ----------------------------------------------------------------- patterns
H_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
HR_RE = re.compile(r"<hr\s*/?>", re.IGNORECASE)
STRONG_RE = re.compile(r"<strong[^>]*>(.*?)</strong>", re.IGNORECASE | re.DOTALL)
EM_RE = re.compile(r"<em[^>]*>(.*?)</em>", re.IGNORECASE | re.DOTALL)
B_RE = re.compile(r"<b[^>]*>(.*?)</b>", re.IGNORECASE | re.DOTALL)
I_RE = re.compile(r"<i[^>]*>(.*?)</i>", re.IGNORECASE | re.DOTALL)
CODE_RE = re.compile(r"<code[^>]*>(.*?)</code>", re.IGNORECASE | re.DOTALL)
PRE_RE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.IGNORECASE | re.DOTALL)
LINK_RE = re.compile(
    r'<a\b[^>]*href="(?P<href>[^"]*)"[^>]*>(?P<text>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
IMG_RE = re.compile(r"<img\b[^>]*src=\"(?P<src>[^\"]*)\"[^>]*>", re.IGNORECASE)
BLOCKQUOTE_RE = re.compile(r"<blockquote[^>]*>(.*?)</blockquote>", re.IGNORECASE | re.DOTALL)
TABLE_RE = re.compile(r"<table[^>]*>(?P<body>.*?)</table>", re.IGNORECASE | re.DOTALL)
TR_RE = re.compile(r"<tr[^>]*>(?P<body>.*?)</tr>", re.IGNORECASE | re.DOTALL)
TH_RE = re.compile(r"<th[^>]*>(?P<body>.*?)</th>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td[^>]*>(?P<body>.*?)</td>", re.IGNORECASE | re.DOTALL)
LIST_RE = re.compile(r"<(ul|ol)[^>]*>(?P<body>.*?)</\1>", re.IGNORECASE | re.DOTALL)
LI_RE = re.compile(r"<li[^>]*>(?P<body>.*?)</li>", re.IGNORECASE | re.DOTALL)
MODULE_RE = re.compile(
    r"<div\s[^>]*class=\"[^\"]*\bmodule\b[^\"]*\"[^>]*data-options="
    r"(?P<quote>[\"'])(?P<opts>.*?)(?P=quote)[^>]*>(?P<body>.*?)</div>",
    re.IGNORECASE | re.DOTALL,
)
WIKI_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
WIKI_ITALIC_RE = re.compile(r"//(.+?)//", re.DOTALL)
SECTION_LEAD_RE = re.compile(r"^(?P<title>[A-Z][^.!?]{2,70}\.)\s+(?P<rest>.+)$", re.DOTALL)

SOURCE_RE = re.compile(r"^\s*Source:\s*(?P<src>.{2,60}?)\s*$", re.IGNORECASE | re.MULTILINE)
SCHOOL_RE = re.compile(
    r"\b(?:(?P<level>cantrip|[1-9](?:st|nd|rd|th)[- ]level)\s+)?(?P<school>[a-z]+)\b",
    re.IGNORECASE,
)


def strip_tags(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html_lib.unescape(text).strip()


def _img_repl(result: ParseResult | None):
    def repl(match: re.Match) -> str:
        src = match.group("src")
        if result is not None:
            result.images.append(src)
        return f"![{src.rsplit('/', 1)[-1]}]({src})"

    return repl


def _link_repl(result: ParseResult | None):
    def repl(match: re.Match) -> str:
        from .links import path_to_slug

        href = html_lib.unescape(match.group("href"))
        label = strip_tags(match.group("text")) or href
        if not href or href.startswith(("#", "javascript:")):
            return label
        if re.match(r"^[a-z]+://", href) and "wikidot.com" not in href:
            return f"[{label}]({href})"
        raw = href.strip("/").split("/")[-1].split("#")[0]
        slug = path_to_slug(raw) if raw else raw
        if slug and result is not None:
            result.links.append((slug, label))
        return f"[{label}](/{slug})"

    return repl


def _inline(text: str, result: ParseResult | None = None) -> str:
    """Convert inline HTML to Markdown (images/links already handled globally)."""
    text = STRONG_RE.sub(r"**\1**", text)
    text = B_RE.sub(r"**\1**", text)
    text = EM_RE.sub(r"*\1*", text)
    text = I_RE.sub(r"*\1*", text)
    text = CODE_RE.sub(r"`\1`", text)
    text = PRE_RE.sub(r"\n```\n\1\n```\n", text)
    text = BR_RE.sub("\n", text)
    text = re.sub(
        r"</?(?:div|span|small|sup|sub|center|font)[^>]*>", "", text, flags=re.IGNORECASE
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = WIKI_BOLD_RE.sub(r"**\1**", text)
    text = WIKI_ITALIC_RE.sub(r"*\1*", text)
    return text.strip()
class WikidotParser:
    """Converts a full Wikidot page (or bare article HTML) into Markdown."""

    def parse_page(self, page_html: str, page_path: str = "") -> ParseResult:
        result = ParseResult()
        result.title = extract_title(page_html)
        result.tags = extract_tags(page_html)
        article = extract_article(page_html)
        result.markdown = self.parse(article, page_path, result)
        return result

    def parse(self, raw_html: str, page_path: str = "",
              result: ParseResult | None = None) -> str:
        result = result if result is not None else ParseResult()
        text = raw_html or ""

        def module_repl(match: re.Match) -> str:
            options = html_lib.unescape(match.group("opts") or "")
            class_match = re.search(r'class="([^"]*)"', match.group(0))
            class_name = class_match.group(1) if class_match else "module"
            handled = handle_module(class_name, options, strip_tags(match.group("body")))
            if not handled.understood:
                result.unknown_constructs.append(handled.name)
                result.warnings.append(
                    Warning_(handled.name, handled.markdown[:120], page_path)
                )
            return "\n\n" + handled.markdown + "\n\n"

        text = MODULE_RE.sub(module_repl, text)
        # Links and images can appear outside <p> (lists, table cells, bare
        # markup), so they are converted globally before block handling.
        text = IMG_RE.sub(_img_repl(result), text)
        text = LINK_RE.sub(_link_repl(result), text)
        text = TABLE_RE.sub(self._table, text)
        text = BLOCKQUOTE_RE.sub(lambda m: self._block_quote(m, result), text)
        text = LIST_RE.sub(self._list, text)
        text = H_RE.sub(lambda m: self._heading(m, result), text)
        text = P_RE.sub(lambda m: self._paragraph(m, result), text)
        text = HR_RE.sub("\n\n---\n\n", text)
        # Only leftover tags are stripped here. Re-running _inline over the whole
        # document would re-match the ** markers produced above and corrupt them.
        text = re.sub(r"<[^>]+>", "", text)
        text = html_lib.unescape(text)

        markdown = self._tidy(text)
        self._collect_header(markdown, result)
        return markdown

    # -------------------------------------------------------------- blocks
    @staticmethod
    def _heading(match: re.Match, result: ParseResult) -> str:
        level = min(int(match.group(1)), 6)
        text = strip_tags(match.group(2))
        if not text:
            return ""
        if level == 2 and not result.title:
            result.title = text
        return f"\n\n{'#' * level} {text}\n\n"

    @staticmethod
    def _paragraph(match: re.Match, result: ParseResult) -> str:
        text = _inline(match.group(1), result)
        if not text:
            return "\n"

        source = SOURCE_RE.match(text)
        if source:
            result.source_label = source.group("src").strip(" .")
            return "\n"

        school = SCHOOL_RE.match(text)
        if school and school.group("school") and len(text) < 45:
            return f"\n\n{text}\n\n"

        # "<strong><em>At Higher Levels.</em></strong> rest..." -> heading
        lead = SECTION_LEAD_RE.match(text)
        if lead and text[:45].count("*") >= 2:
            title = lead.group("title").strip(" .*")
            rest = lead.group("rest").strip()
            return f"\n\n### {title}\n\n{rest}\n\n"

        return f"\n\n{text}\n\n"

    @staticmethod
    def _block_quote(match: re.Match, result: ParseResult) -> str:
        text = _inline(match.group(1), result)
        return "\n\n" + "\n".join(f"> {line}" for line in text.splitlines()) + "\n\n"

    @staticmethod
    def _list(match: re.Match) -> str:
        ordered = match.group(1).lower() == "ol"
        lines: list[str] = []
        for item in LI_RE.finditer(match.group("body")):
            body = item.group("body")
            nested = ""
            inner = LIST_RE.search(body)
            if inner:
                nested = "\n" + WikidotParser._list(inner)
                body = body[: inner.start()]
            text = _inline(body)
            if text:
                lines.append(f"{'1.' if ordered else '-'} {text}{nested}")
        return "\n" + "\n".join(lines) + "\n"

    @staticmethod
    def _cell(text: str) -> str:
        """Table cell: keeps inline Markdown, drops tags."""
        text = STRONG_RE.sub(r"**\1**", text)
        text = B_RE.sub(r"**\1**", text)
        text = EM_RE.sub(r"*\1*", text)
        text = I_RE.sub(r"*\1*", text)
        text = BR_RE.sub(" ", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = html_lib.unescape(text)
        text = WIKI_BOLD_RE.sub(r"**\1**", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _table(cls, match: re.Match) -> str:
        """Markdown table; colspan header groups are flattened into one row."""
        header_rows: list[list[str]] = []
        body_rows: list[list[str]] = []

        for row_match in TR_RE.finditer(match.group("body")):
            row = row_match.group("body")
            cells = [cls._cell(c.group("body"))
                     for c in list(TH_RE.finditer(row)) + list(TD_RE.finditer(row))]
            if not any(cells):
                continue
            if TH_RE.search(row) and not TD_RE.search(row):
                header_rows.append(cells)
            else:
                body_rows.append(cells)

        if not body_rows and not header_rows:
            return strip_tags(match.group(0))

        width = max((len(r) for r in header_rows + body_rows), default=0)
        if width == 0:
            return ""

        header = list(header_rows[0]) if header_rows else [f"Col {i + 1}" for i in range(width)]
        for extra in header_rows[1:]:
            header = extra + header[len(extra):]
        header = (header + [""] * width)[:width]

        lines = [
            "| " + " | ".join(c.replace("|", "\\|") for c in header) + " |",
            "| " + " | ".join(["---"] * width) + " |",
        ]
        for row in body_rows:
            padded = (row + [""] * width)[:width]
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in padded) + " |")
        return "\n\n" + "\n".join(lines) + "\n\n"

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _collect_header(markdown: str, result: ParseResult) -> None:
        """Leading lines before the first heading are the page header block."""
        header: list[str] = []
        for line in markdown.splitlines():
            if line.startswith("#"):
                break
            if line.strip():
                header.append(line.strip())
        if header:
            result.header_lines = header
            if not result.subtitle:
                result.subtitle = header[0]

    @staticmethod
    def _tidy(text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        # Empty emphasis only ("* *"), never across a line break: "*text*\n**next**"
        # is legitimate Markdown and must not be collapsed.
        text = re.sub(r"\*[ \t]+\*", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.rstrip() for line in text.splitlines()).strip()

        return f"\n\n{text}\n\n"

    @staticmethod
    def _block_quote(match: re.Match, result: ParseResult) -> str:
        text = _inline(match.group(1), result)
        return "\n\n" + "\n".join(f"> {line}" for line in text.splitlines()) + "\n\n"

    @staticmethod
    def _list(match: re.Match) -> str:
        ordered = match.group(1).lower() == "ol"
        lines: list[str] = []
        for item in LI_RE.finditer(match.group("body")):
            body = item.group("body")
            nested = ""
            inner = LIST_RE.search(body)
            if inner:
                nested = "\n" + WikidotParser._list(inner)
                body = body[: inner.start()]
            text = _inline(body)
            if text:
                lines.append(f"{'1.' if ordered else '-'} {text}{nested}")
        return "\n" + "\n".join(lines) + "\n"
