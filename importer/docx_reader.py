"""Read the campaign's .docx corpus into Markdown.

The documents have no heading styles at all (every paragraph is "normal"), so
the structure is inferred from the formatting that IS there:

- a bold, short paragraph reads as an item title;
- a line of underscores separates items;
- a short paragraph ending in ":" reads as a field label;
- tables become Markdown tables.

Documents containing several titled items are split into one page per item.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import docx
from docx.table import Table
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

SEPARATOR_RE = re.compile(r"^_{10,}$")

# Documents that hold several independent entries and must be split per entry.
MULTI_ITEM_DOCS = {
    "novos feitiços", "novos feiticos", "novos feats", "novos fighting styles",
}
FIELD_RE = re.compile(r"^([A-Za-zÀ-ÿ][^:.]{2,40}):\s*(.*)$")
LIST_PREFIX_RE = re.compile(r"^\s*[-*•]\s*")

# Portuguese spell-level markers used in the campaign's documents.
ORDINALS = [
    ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5),
    ("6", 6), ("7", 7), ("8", 8), ("9", 9),
]
LEVEL_PATTERNS = [
    (re.compile(r"\bcantrip\b|\btrilha\b", re.IGNORECASE), 0),
] + [
    (re.compile(rf"\b{n}[ºoª]\s*c[ií]rc(?:ulo|ir)o\b", re.IGNORECASE), level)
    for n, level in ORDINALS
]

SCHOOL_RE = re.compile(
    r"\b(abjura[çc][ãa]o|conjura[çc][ãa]o|adivinha[çc][ãa]o|encanta[çc][ãa]o|"
    r"evoca[çc][ãa]o|ilus[ãa]o|necromancia|transmuta[çc][ãa]o)\b",
    re.IGNORECASE,
)

FIELD_MAP = {
    "casting time": "casting_time",
    "tempo de conjura[çc][ãa]o": "casting_time",
    "range": "range",
    "alcance": "range",
    "target": "target",
    "alvo": "target",
    "component": "components",
    "componentes": "components",
    "components": "components",
    "duration": "duration",
    "dura[çc][ãa]o": "duration",
    "spell lists": "classes",
    "spell list": "classes",
    "lista de magias": "classes",
}


@dataclass
class DocxItem:
    title: str
    markdown: str
    structured_data: dict = field(default_factory=dict)


@dataclass
class DocxDocument:
    filename: str
    folder: str
    items: list[DocxItem]
    warnings: list[str] = field(default_factory=list)

    @property
    def is_multi(self) -> bool:
        return len(self.items) > 1


"""Field labels that look like titles when bold (they end with ':')."""
KNOWN_FIELDS = {
    "casting time", "tempo de conjuração", "range", "alcance", "target", "alvo",
    "component", "components", "componentes", "duration", "duração",
    "spell lists", "spell list", "lista de magias", "pré-requisito",
    "prerequisito", "espaço", "espaco", "hirelings", "tipo", "nível", "nivel",
    "atributos principais", "dado de vida", "proficiências", "equipamento",
}


"""Expand a paragraph into lines, keeping each line's own boldness.

Two documents need this: "Adepto de montaria voadora (Feat):" is bold on the
first run only, and "Novos fighting styles" stores several entries separated by
line breaks inside a single non-bold paragraph.
"""
def _hyperlink_markdown(paragraph, hyperlink) -> str:
    """Return a DOCX hyperlink as Markdown, preserving the linked target."""
    text = "".join(node.text or "" for node in hyperlink.iter() if node.tag == qn("w:t"))
    if not text:
        return ""

    relationship_id = hyperlink.get(qn("r:id"))
    relationship = paragraph.part.rels.get(relationship_id)
    target = str(relationship.target_ref) if relationship else ""
    if not target:
        return text

    # Wikidot links use URLs such as /spell:mage-armor. The application routes
    # imported pages by their final slug, so keep the generated link local.
    match = re.search(r"(?:^|/)spell:([^/?#]+)", target, re.IGNORECASE)
    if match:
        # Wikidot sometimes encodes possessives as `dragon-s-breath`, while
        # imported page slugs are generated from the visible title as
        # `dragons-breath`.
        slug_source = match.group(1) if re.match(r"https?://", text, re.IGNORECASE) else text
        slug_source = slug_source.replace("'", "").replace("’", "")
        slug_source = unicodedata.normalize("NFKD", slug_source)
        slug_source = "".join(c for c in slug_source if not unicodedata.combining(c))
        slug_source = re.sub(r"[^a-zA-Z0-9\s_-]", "", slug_source)
        slug = re.sub(r"[-\s]+", "-", slug_source).strip("-").lower()
        return f"[{text}]({target})"
    if target.startswith("/"):
        return f"[{text}]({target})"
    return f"[{text}]({target})"


def _run_text(run_element) -> str:
    parts: list[str] = []
    for node in run_element.iter():
        if node.tag == qn("w:t"):
            parts.append(node.text or "")
        elif node.tag == qn("w:br"):
            parts.append("\n")
    return "".join(parts)


def _rewrite_url_links(text: str) -> str:
    # Some source DOCX files write `Spell Name: <hyperlinked URL>` instead of
    # making the spell name itself the hyperlink. Turn that representation into
    # one linked spell name and discard the visible URL.
    def replace_url_link(match: re.Match) -> str:
        prefix = match.group("prefix")
        raw_name = match.group("name").strip()
        is_bullet = bool(re.match(r"^[\s\u2022*-]+", raw_name))
        name = re.sub(r"^[\s\u2022*-]+", "", raw_name).strip()
        href = match.group("href")
        return f"{prefix}{'- ' if is_bullet else ''}[{name}]({href})"

    return re.sub(
        r"(?P<prefix>^|[\n\u2022]\s*)(?P<name>[^:\n]+):\s*"
        r"\[https?://[^\]]+/spell:[^\]]+\]\((?P<href>https?://[^)]+)\)",
        replace_url_link,
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )


def _paragraph_markdown_text(paragraph) -> str:
    """Read paragraph content in XML order, including w:hyperlink nodes."""
    parts: list[str] = []
    for child in paragraph._p:
        if child.tag == qn("w:hyperlink"):
            parts.append(_hyperlink_markdown(paragraph, child))
        elif child.tag == qn("w:r"):
            parts.append(_run_text(child))
    text = "".join(parts)
    return _rewrite_url_links(text)


def _paragraph_is_bulleted(paragraph) -> bool:
    ppr = paragraph._p.pPr
    return ppr is not None and ppr.numPr is not None


def _paragraph_lines(paragraph) -> list[tuple[str, bool]]:
    lines: list[tuple[str, bool]] = []
    current = ""
    current_bold = False

    def flush() -> None:
        nonlocal current, current_bold
        if current.strip():
            lines.append((current.strip(), current_bold))
        current = ""
        current_bold = False

    for child in paragraph._p:
        if child.tag == qn("w:hyperlink"):
            text = _hyperlink_markdown(paragraph, child)
            is_bold = False
        elif child.tag == qn("w:r"):
            text = _run_text(child)
            rpr = child.find(qn("w:rPr"))
            is_bold = rpr is not None and rpr.find(qn("w:b")) is not None
        else:
            continue
        if not text:
            continue
        pieces = text.split("\n")
        current += pieces[0]
        current_bold = current_bold or is_bold
        for piece in pieces[1:]:
            flush()
            current = piece
            current_bold = is_bold
    flush()
    return [(_rewrite_url_links(text), is_bold) for text, is_bold in lines]


def _paragraph_is_bold_title(paragraph) -> bool:
    """A bold, short paragraph reads as an item title.

    Bold lines ending in ':' are only labels when they name a known field;
    otherwise ("Concentracao multipla (feat):") they are the item's title.
    """
    lines = [line for line in _paragraph_lines(paragraph) if line[0]]
    if not lines:
        return False
    # Majority bold: some entries bold only their first run.
    bold_runs = [is_bold for _, is_bold in lines]
    if sum(bold_runs) * 2 < len(bold_runs):
        return False
    if not bold_runs[0]:
        return False
    text = lines[0][0]
    if LIST_PREFIX_RE.match(text) or text.lstrip().startswith("- "):
        return False
    if len(text) > 90:
        return False
    # The colon is often a separate, non-bold run ("Casting time" + ":"), so the
    # label is checked both with and without it.
    stripped = text.rstrip(":").strip().lower()
    if stripped in KNOWN_FIELDS:
        return False
    return True


def _paragraph_title(paragraph) -> str:
    for text, _bold in _paragraph_lines(paragraph):
        if text:
            return text
    return ""


def _table_to_markdown(table) -> str:
    rows = []
    for row in table.rows:
        cells = [c.text.strip().replace("|", "\\|").replace("\n", " ") for c in row.cells]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    lines = [
        "| " + " | ".join(_pad(rows[0], width)) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(_pad(row, width)) + " |")
    return "\n".join(lines)


def _pad(row: list[str], width: int) -> list[str]:
    return (row + [""] * width)[:width]


def _paragraph_to_markdown(paragraph, title: str | None) -> str | None:
    text = _paragraph_markdown_text(paragraph).strip()
    if not text:
        return None
    if SEPARATOR_RE.match(text):
        return None
    if _paragraph_is_bold_title(paragraph):
        return f"### {text}"
    field_match = FIELD_RE.match(text)
    if field_match and len(text) < 120:
        return f"**{field_match.group(1).strip()}:** {field_match.group(2).strip()}".rstrip()
    line = LIST_PREFIX_RE.sub("", text)
    return f"- {line}" if _paragraph_is_bulleted(paragraph) else line


def detect_level(text: str):
    for pattern, level in LEVEL_PATTERNS:
        if pattern.search(text):
            return level
    return None


def extract_structured(text: str) -> dict:
    """Read the spell stat block written in the campaign's own wording."""
    data: dict = {}
    head = text[:900]

    level = detect_level(head)
    if level is not None:
        data["level"] = level

    school = SCHOOL_RE.search(head)
    if school:
        data["school"] = school.group(1).capitalize()

    for label, key in FIELD_MAP.items():
        match = re.search(rf"\*\*{label}[^*]*\*\*\s*:?\s*(.+)", text, re.IGNORECASE)
        if not match:
            continue
        value = match.group(1).strip()
        if not value or value == ":":
            continue
        if key == "classes":
            classes = [
                c.strip() for c in re.split(r"[;,/]", value)
                if c.strip() and len(c.strip()) <= 30
            ]
            if classes:
                data["classes"] = classes
        else:
            data[key] = value

    return data
    warnings: list[str] = field(default_factory=list)

    @property
    def is_multi(self) -> bool:
        return len(self.items) > 1
def _body_blocks(document) -> list:
    """Paragraphs and tables in true document order."""
    blocks = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith('}p'):
            blocks.append(("p", Paragraph(child, document)))
        elif child.tag.endswith('}tbl'):
            blocks.append(("t", Table(child, document)))
    return blocks


def _is_short_title(text: str) -> bool:
    return 0 < len(text) <= 60 and not text.rstrip(":").endswith((".", ",", ";"))


def _looks_like_plain_title(paragraph) -> bool:
    """A plain (unbolded) paragraph made only of "Title:" style lines."""
    lines = [text for text, _ in _paragraph_lines(paragraph) if text]
    if len(lines) < 2:
        return False
    titled = [t for t in lines if t.endswith(":") and _is_short_title(t)]
    return len(titled) >= 2


def _line_to_markdown(text: str) -> str | None:
    if not text or SEPARATOR_RE.match(text):
        return None
    field_match = FIELD_RE.match(text)
    if field_match and len(text) < 120:
        return f"**{field_match.group(1).strip()}:** {field_match.group(2).strip()}".rstrip()
    has_markdown_bullet = bool(LIST_PREFIX_RE.match(text)) or text.lstrip().startswith("- ")
    line = LIST_PREFIX_RE.sub("", text)
    return f"- {line}" if has_markdown_bullet else line


def _document_blocks(document) -> list[tuple[str, object]]:
    """Flatten the document into ('title'|'text'|'table', payload) blocks.

    A paragraph holding several lines becomes several blocks, which is how
    "Novos fighting styles" stores its entries.
    """
    blocks: list[tuple[str, object]] = []
    for kind, element in _body_blocks(document):
        if kind == "t":
            blocks.append(("table", element))
            continue

        lines = _paragraph_lines(element)
        if not lines:
            continue

        if _paragraph_is_bold_title(element):
            blocks.append(("title", _paragraph_title(element)))
            for text, is_bold in lines[1:]:
                if text:
                    blocks.append(("text", text))
            continue

        # "Novos fighting styles" has neither bold titles nor rules: its entries
        # are plain short lines ending in ':' ("Berserker:", "Duelista (revisado):").
        if _looks_like_plain_title(element):
            for text, _is_bold in lines:
                if text.endswith(":") and _is_short_title(text):
                    blocks.append(("title", text.rstrip(":").strip()))
                elif text:
                    blocks.append(("text", text))
            continue

        for text, _is_bold in lines:
            if text:
                prefix = "- " if _paragraph_is_bulleted(element) else ""
                blocks.append(("text", prefix + text))
    return blocks


def parse_docx(path) -> DocxDocument:
    document = docx.Document(str(path))
    filename = path.name
    folder = path.parent.name

    blocks = _document_blocks(document)

    # Only the known multi-entry documents are ever split. Class documents use
    # underscores as decoration and bold for feature names, so splitting them
    # shatters one class into pages called "Ki Points:" or "Pele de Troll".
    split_enabled = Path(filename).stem.strip().lower() in MULTI_ITEM_DOCS

    chunks: list[list] = []
    current: list = []
    seen_content = False

    if not split_enabled:
        chunks = [blocks]
    else:
        # Use the underscore rules when the document has them; fall back to bold
        # titles only for documents without rules, so bold sub-headings inside a
        # spell ("At Higher Levels") never become new spells.
        has_rules = any(kind == "text" and SEPARATOR_RE.match(payload)
                        for kind, payload in blocks)
        for kind, payload in blocks:
            if kind == "text" and SEPARATOR_RE.match(payload):
                if current:
                    chunks.append(current)
                current, seen_content = [], False
                continue

            if kind == "title" and seen_content and not has_rules:
                chunks.append(current)
                current = []

            current.append((kind, payload))
            if kind in {"title", "text"}:
                seen_content = True

        if current:
            chunks.append(current)

    items: list[DocxItem] = []
    warnings: list[str] = []

    for chunk in chunks:
        if not chunk:
            continue

        title = next((payload for kind, payload in chunk if kind == "title"), None)

        lines: list[str] = []
        for kind, payload in chunk:
            if kind == "title":
                if title and payload == title:
                    continue
                lines.append(f"### {payload}")
            elif kind == "text":
                line = _line_to_markdown(payload)
                if line:
                    lines.append(line)
            else:
                markdown = _table_to_markdown(payload)
                if markdown:
                    lines.append(markdown)

        markdown = re.sub(r"\n{3,}", "\n\n", "\n\n".join(lines)).strip()
        if not markdown:
            continue

        if title is None:
            if items:
                items[-1].markdown += "\n\n" + markdown
                items[-1].structured_data.update(extract_structured(markdown))
                continue
            title = Path(filename).stem

        # A document that was not split keeps the file name as its title: the
        # first bold line is usually a table caption ("Fiendish Legacy"), not the
        # entry's real name.
        if not split_enabled:
            title = Path(filename).stem

        items.append(DocxItem(
            title=title,
            markdown=markdown,
            structured_data=extract_structured(markdown),
        ))

    if not items:
        warnings.append("documento sem conteudo legivel")

    return DocxDocument(filename=filename, folder=folder, items=items,
                        warnings=warnings)
