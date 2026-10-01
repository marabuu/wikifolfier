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
from dataclasses import dataclass, field
from pathlib import Path

import docx
from docx.table import Table
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
def _paragraph_lines(paragraph) -> list[tuple[str, bool]]:
    lines: list[tuple[str, bool]] = []
    for run in paragraph.runs:
        if not run.text:
            continue
        pieces = run.text.split("\n")
        for index, piece in enumerate(pieces):
            piece = piece.strip()
            if piece:
                lines.append((piece, bool(run.bold)))
            elif index < len(pieces) - 1:
                lines.append(("", bool(run.bold)))
    return lines


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
    text = paragraph.text.strip()
    if not text:
        return None
    if SEPARATOR_RE.match(text):
        return None
    if _paragraph_is_bold_title(paragraph):
        return f"### {text}"
    field_match = FIELD_RE.match(text)
    if field_match and len(text) < 120:
        return f"**{field_match.group(1).strip()}:** {field_match.group(2).strip()}".rstrip()
    return LIST_PREFIX_RE.sub("", text)


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
    return LIST_PREFIX_RE.sub("", text)


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
                blocks.append(("text", text))
    return blocks


def parse_docx(path) -> DocxDocument:
    document = docx.Document(str(path))
    filename = path.name
    folder = path.parent.name

    blocks = _document_blocks(document)

    # Documents that use underscore rules are already split correctly by them;
    # splitting on bold as well would carve out bold sub-headings like
    # "At Higher Levels" as if they were new entries. Bold splitting is therefore
    # reserved for documents that have no rules at all ("Novos Feats").
    has_rules = any(kind == "text" and SEPARATOR_RE.match(payload)
                    for kind, payload in blocks)
    split_on_bold = (not has_rules
                     and Path(filename).stem.strip().lower() in MULTI_ITEM_DOCS)

    chunks: list[list] = []
    current: list = []
    seen_content = False

    for kind, payload in blocks:
        if kind == "text" and SEPARATOR_RE.match(payload):
            if current:
                chunks.append(current)
            current, seen_content = [], False
            continue

        if split_on_bold and kind == "title" and seen_content:
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
            warnings.append("sem titulo proprio; usando o nome do arquivo")
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