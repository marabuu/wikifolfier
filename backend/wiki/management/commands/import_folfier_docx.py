"""Import the campaign's .docx corpus as ordinary compendium pages.

These pages are treated like any other content: they live in the normal
categories (Classes, Subclasses, Feats, Spells, ...) and use the same
templates. The only difference is the `source` metadata, which is "folfier".

Multi-item documents (several bold titles separated by underscore rules) are
split into one page per item.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

# The .docx reader lives in the sibling "importer" package, outside the Django app.
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "importer"))

from docx_reader import DocxItem, parse_docx  # noqa: E402

from wiki.models import Category, Page, Source  # noqa: E402
from wiki.services import save_page_with_derived_data  # noqa: E402

ROOT = Path(r"E:\dev\wikifolfier2\conteudo a adicionar")

FOLDER_MAP = {
    "classes": ("classes", "class"),
    "subclasses": ("subclasses", "subclass"),
    "subclasse": ("subclasses", "subclass"),
    "raças": ("species", "species"),
    "racas": ("species", "species"),
    "especies": ("species", "species"),
}

# Documents under "Regras Homebrew" that belong to a specific category.
RULES_MAP = {
    "novos feitiços": ("spells", "spell"),
    "novos feiticos": ("spells", "spell"),
    "novos feats": ("feats", "feat"),
    "novos fighting styles": ("feats", "feat"),
    "novas eldritch invocations": ("subclasses", "subclass"),
    "novas opções de ataque": ("rules", "rule"),
    "novas opcoes de ataque": ("rules", "rule"),
    "regras gerais": ("rules", "rule"),
    "bastião": ("rules", "rule"),
    "bastiao": ("rules", "rule"),
}

DEFAULT_RULES = ("rules", "rule")

PARENT_RE = re.compile(r"\(([^)]+)\)")
CLASS_HINTS = {
    "wizard": "wizard", "bruxo": "warlock", "warlock": "warlock",
    "monge": "monk", "monk": "monk", "bardo": "bard", "bard": "bard",
    "clerico": "cleric", "clérigo": "cleric", "cleric": "cleric",
    "druida": "druid", "druid": "druid", "bárbaro": "barbarian",
    "barbaro": "barbarian", "barbarian": "barbarian",
    "paladino": "paladin", "paladin": "paladin",
    "patrulheiro": "ranger", "ranger": "ranger",
    "ladino": "rogue", "rogue": "rogue",
    "artificer": "artificer", "artífice": "artificer",
    "sorcerer": "sorcerer", "feiticeiro": "sorcerer",
}

# Subclasses whose file name does not carry a "(classe)" hint: matched by title.
TITLE_HINTS = {
    # Corrected by the GM: Circulo da Lua is a cleric option, Celestial is a
    # warlock revision.
    "circulo da lua": "cleric",
    "circle of the moon": "cleric",
    "celestial": "warlock",
    "horizon walker": "ranger",
    "eldritch invocation": "warlock",
    "way of mercy": "monk",
    "warrior of mercy": "monk",
    "way of shadow": "monk",
    "arcane ways": "wizard",
    "cosmic tinker": "artificer",
    "coletor de almas": "ranger",
    "duelista": "rogue",
    "colegio da pintura": "bard",
    "subtlety": "rogue",
    "luminae": "sorcerer",
    "mestre de espadas": "monk",
    "dragonborn": "barbarian",
    "loa da morte": "warlock",
    "great old one": "warlock",
    "caminho dos quatro elementos": "monk",
    "circulo da ordenacao dos mundos": "druid",
    "dominio da luz da lua": "cleric",
    "juramento dos escritores": "paladin",
}

# Renames and drops requested by the GM. None = do not import.
TITLE_OVERRIDES = {
    "way of mercy (revisado)": "Warrior of Mercy",
    "way of mercy (revisado).": "Warrior of Mercy",
    "o celestial (revisado)": None,
    "o celestial (apenas 2014)": None,
}

# The GM named what counts as a "subclass" for the new Folfier classes. These
# documents have no Subclasses section, so the headings are listed explicitly
# rather than guessed.
CLASS_SUBCLASS_SECTIONS = {
    "classe - herói": ["Destino Heróico"],
    "classe - runescaper": [
        "Livro de feitiços rúnicos",
        "Livro moderno",
        "Livro antigo",
        "Livro lunar",
        "Livro de Gravação rúnica",
    ],
    "classe - filho da magia": [
        "Magia Progenitora",
        "Magia Progenitora (Níveis 1, 3, 7, 10, 14, 18)",
    ],
    "classe - witcher": ["Escola do Lobo", "Escola do Urso", "Escola da Víbora"],
}

# Longest alternatives first: "subraça" must win over "sub".
PREFIX_RE = re.compile(
    r"^\s*(?:sub-?ra[çc]a|subclasse|classe|ra[çc]a|sub)\s*[-–:]?\s*",
    re.IGNORECASE,
)

# Section markers that introduce a class spell list inside a class document.
SPELL_LIST_RE = re.compile(
    r"^(?:#{2,3}\s*)?(?:lista\s+de\s+magias|magias\s+(?:da|do)\s+classe|"
    r"spell\s*(?:list|table)|lista\s+de\s+feitiços)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
def split_spell_list(markdown: str) -> tuple[str, str]:
    """Move a class spell list out of the class body.

    Returns (class_markdown, spell_list_markdown). The spell list is empty when
    the document has no such section.
    """
    match = SPELL_LIST_RE.search(markdown)
    if not match:
        return markdown, ""

    body_prefix = markdown[: match.start()].rstrip()
    after_heading = markdown[match.end():].lstrip()
    # Keep subclass sections after a class spell table in the class source.
    next_section = None
    for section in re.finditer(r"^###\s+(.+?)\s*$", after_heading, re.MULTILINE):
        section_title = section.group(1).strip()
        if re.match(r"^(?:\d+|[1-9])(?:st|nd|rd|th)\s+Level$", section_title, re.IGNORECASE):
            continue
        next_section = section
        break
    if next_section:
        listing = after_heading[:next_section.start()].rstrip()
        body = body_prefix + "\n\n" + after_heading[next_section.start():].lstrip()
    else:
        body = body_prefix
        listing = after_heading
    if not listing:
        return markdown, ""
    return body, listing


def add_spell_list_link(markdown: str, title: str, slug: str) -> str:
    """Expose a generated class spell list from the class page body."""
    link = f"[{title} Spell List](/subclasses/{slug})"
    sentence = f"A lista de magias de {title} está na {link}."
    if link in markdown:
        return markdown

    conjuration = re.search(
        r"^##\s+(?:Conjuração|Conjuração|Spellcasting)\s*$",
        markdown,
        re.IGNORECASE | re.MULTILINE,
    )
    if conjuration:
        start = conjuration.end()
        while markdown[start:start + 1] == "\n":
            start += 1
        end = markdown.find("\n\n", start)
        if end >= 0:
            return markdown[:end] + "\n\n" + sentence + markdown[end:]
        return markdown.rstrip() + "\n\n" + sentence

    feature = re.search(r"^.*conjura.{0,12}:.*$", markdown, re.IGNORECASE | re.MULTILINE)
    if feature:
        end = markdown.find("\n\n", feature.end())
        if end >= 0:
            return markdown[:end] + "\n\n" + sentence + markdown[end:]

    return markdown.rstrip() + "\n\n## Spell List\n\n" + sentence


# A class document opens with a stray "Classe" / "Classe: X" label.
CLASS_LABEL_RE = re.compile(r"^\s*\**\s*classe\s*\**\s*:?\s*\**\s*(.{0,60}?)\s*\**\s*$",
                            re.IGNORECASE)

# Section headings that become the page's top-level (H2) sections, matching how
# the official class pages are organised.
CLASS_SECTIONS = (
    "características da classe", "características de classe",
    "pontos de vida e proficiências", "pontos de vida",
    "proficiências", "equipamento", "conjuração",
    "class features", "hit points", "proficiencies",
)


def normalize_class_markdown(markdown: str) -> tuple[str, str]:
    """Give a homebrew class the same shape as an official class page.

    Returns (markdown, subtitle). The stray "Classe: X" label is dropped, the
    real opening paragraph becomes the subtitle, and the main sections are
    promoted to H2 so the page reads like the imported classes.
    """
    lines = markdown.splitlines()
    body: list[str] = []
    label = ""

    for line in lines:
        match = CLASS_LABEL_RE.match(line)
        if match and not body:
            label = match.group(1).strip()
            continue
        body.append(line)

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()

    # Promote the class' own section headings to H2.
    lines = text.splitlines()
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{3,4})\s*(.+?)\s*:?\s*$", line)
        if not heading:
            continue
        if heading.group(2).strip().lower() in CLASS_SECTIONS:
            lines[index] = f"## {heading.group(2).strip()}"
    text = "\n".join(lines)

    # Subtitle: the first real prose paragraph, skipping tables and headings.
    subtitle = ""
    paragraph: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("#", "|", "-", ">", "*")):
            continue
        paragraph.append(stripped)
        if len(" ".join(paragraph)) > 60:
            break
    if paragraph:
        subtitle = " ".join(paragraph)[:255]

    if not subtitle and label:
        subtitle = label[:255]

    return text, subtitle


def normalize_runescaper_markdown(markdown: str) -> str:
    """Arrange Runescaper's opening like an imported Wikidot class page."""
    class_marker = "## Características de Classe"
    hit_points_marker = "## Pontos de Vida"

    class_start = markdown.find(class_marker)
    hit_points_start = markdown.find(hit_points_marker)
    if class_start < 0 or hit_points_start < 0 or hit_points_start <= class_start:
        return markdown

    opening = markdown[:class_start].strip()
    class_block = markdown[class_start + len(class_marker):hit_points_start].strip()
    remainder = markdown[hit_points_start:].strip()

    # The first table is already the Runescaper progression table. Keep it,
    # but place it after the class introduction, as on the imported pages.
    table_start = class_block.find("| Nível")
    if table_start < 0:
        return markdown
    progression = class_block[table_start:].strip()

    intro_parts = [part.strip() for part in re.split(r"\n\s*\n", opening) if part.strip()]
    if not intro_parts:
        return markdown
    introduction = intro_parts[0]

    core_traits = """| Core Runescaper Traits | |
| --- | --- |
| **Primary Ability** | Intelligence |
| **Hit Point Die** | D8 per Runescaper level |
| **Saving Throw Proficiencies** | Intelligence and Constitution |
| **Skill Proficiencies** | Choose 2: History, Arcana, Insight, Medicine, Nature, or Athletics |
| **Weapon Proficiencies** | Simple weapons |
| **Tool Proficiencies** | Rune inscription tools |
| **Armor Training** | Light armor, medium armor, and shields |
| **Starting Equipment** | A simple weapon; a light crossbow and 20 bolts; (a) studded leather armor or (b) scale mail; rune inscription tools; or 3d10 gp |"""

    becoming = """# Becoming a Runescaper …

## As a Level 1 Character

- Gain all the traits in the Core Runescaper Traits table.
- Gain the Runescaper's level 1 features, which are listed in the Runescaper Features table.

## As a Multiclass Character

- You must have an Intelligence score of 13 or higher to multiclass into or out of this class.

# Runescaper Class Features

As a Runescaper, you gain the following class features when you reach the specified Runescaper levels. These features are listed in the Runescaper Features table.

###### Runescaper Features

"""

    return "\n\n".join(
        [introduction, core_traits, becoming + progression, remainder]
    ).strip()


RUNESCAPER_SUBCLASS_BLOCKS = (
    (
        "Livro moderno",
        "### Livro de feitiços rúnicos modernos",
        "### Livro de feitiços rúnicos antigos",
        "Livro Moderno",
        "Livro Antigo",
    ),
    (
        "Livro antigo",
        "### Livro de feitiços rúnicos antigos",
        "### Livro de feitiços rúnicos lunar",
        "Livro Antigo",
        "Livro Lunar",
    ),
    (
        "Livro lunar",
        "### Livro de feitiços rúnicos lunar",
        "### Livro de feitiços rúnicos de gravação",
        "Livro Lunar",
        "Livro de gravações rúnicas",
    ),
    (
        "Livro de Gravação rúnica",
        "### Livro de feitiços rúnicos de gravação",
        None,
        "Livro de gravações rúnicas",
        None,
    ),
)


def split_runescaper_subclasses(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    """Move each Runescaper book into its own linked subclass page."""
    def find_marker(marker: str, start: int = 0) -> tuple[int, int]:
        exact = markdown.find(marker, start)
        if exact >= 0:
            return exact, len(marker)
        if marker.endswith("de gravação"):
            match = re.search(
                r"^### Livro de feiti.{1,4}os r.{1,4}nicos de (?:grava|graca).*$",
                markdown[start:],
                re.IGNORECASE | re.MULTILINE,
            )
            if match:
                return start + match.start(), len(match.group(0))
        return -1, 0

    spell_books = markdown.find("Spell books")
    if spell_books < 0:
        return markdown, []

    sections: list[tuple[str, str]] = []
    spell_list_heading = "### Livro de feitiços rúnicos"
    spell_list_start, spell_list_heading_length = find_marker(spell_list_heading, spell_books)
    first_subclass_start = min(
        (
            position
            for _title, marker, _end, _feature, _feature_end in RUNESCAPER_SUBCLASS_BLOCKS
            for position, _length in [find_marker(marker, spell_books)]
            if position >= 0
        ),
        default=-1,
    )
    if spell_list_start >= 0 and first_subclass_start > spell_list_start:
        sections.append(
            (
                "Livro de feitiços rúnicos",
                markdown[spell_list_start + spell_list_heading_length:first_subclass_start].strip(),
            )
        )

    for title, spell_start_marker, spell_end_marker, feature_start_marker, feature_end_marker in RUNESCAPER_SUBCLASS_BLOCKS:
        spell_start, spell_heading_length = find_marker(spell_start_marker, spell_books)
        if spell_start < 0:
            continue
        spell_end, _ = find_marker(spell_end_marker, spell_start) if spell_end_marker else (-1, 0)
        if spell_end < 0:
            feature_start = markdown.find(feature_start_marker, spell_start)
            spell_end = feature_start if feature_start >= 0 else len(markdown)

        feature_start = markdown.find(feature_start_marker, spell_end)
        if feature_start < 0:
            continue
        feature_end = (
            markdown.find(feature_end_marker, feature_start)
            if feature_end_marker
            else len(markdown)
        )
        if feature_end < 0:
            feature_end = len(markdown)

        spell_body = markdown[spell_start + spell_heading_length:spell_end].strip()
        feature_body = markdown[feature_start:feature_end].strip()
        feature_body = re.sub(
            rf"^{re.escape(feature_start_marker)}\s*", "", feature_body, count=1
        ).strip()
        sections.append((title, f"{spell_body}\n\n{feature_body}".strip()))

    class_body = markdown[:spell_books].rstrip()
    class_body = re.sub(
        r"^### (?:Livro moderno|Livro antigo|Livro lunar|Livro de Gravação rúnica)\s*$\n?",
        "",
        class_body,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    class_body = class_body.replace(
        "### Livro de feitiços rúnicos",
        "### [Livro de feitiços rúnicos](/subclasses/runescaper-livro-de-feiticos-runicos)",
        1,
    )

    advanced_heading = "### Livro avançado"
    advanced_start = class_body.find(advanced_heading)
    next_heading = (
        class_body.find("\n### ", advanced_start + len(advanced_heading))
        if advanced_start >= 0 else -1
    )
    if advanced_start >= 0:
        advanced_end = next_heading if next_heading >= 0 else len(class_body)
        links = "\n\n".join(
            f"- [{title}](/subclasses/{slugify(f'Runescaper-{title}')})"
            for title, _body in sections
            if title != "Livro de feitiços rúnicos"
        )
        advanced = class_body[advanced_start:advanced_end].rstrip()
        class_body = class_body[:advanced_start] + advanced + "\n\n" + links + class_body[advanced_end:]

    conjuration_heading = "## Conjuração"
    conjuration_start = class_body.find(conjuration_heading)
    if conjuration_start >= 0:
        content_start = conjuration_start + len(conjuration_heading)
        while class_body[content_start:content_start + 1] == "\n":
            content_start += 1
        paragraph_end = class_body.find("\n\n", content_start)
        if paragraph_end >= 0:
            list_link = "[Livro de feitiços rúnicos](/subclasses/runescaper-livro-de-feiticos-runicos)"
            class_body = (
                class_body[:paragraph_end]
                + f"\n\nA lista de magias do Runescaper está na {list_link}."
                + class_body[paragraph_end:]
            )

    return class_body.strip(), sections


def split_named_sections(markdown: str, wanted: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """Pull the named subsections out of a class body.

    Returns (remaining_markdown, [(section_title, section_markdown), ...]).
    A section runs from its heading up to the next heading of the same or higher
    level, so the class keeps everything that was not named.
    """
    headings = list(re.finditer(r"^(#{2,4})\s*(.+?)\s*$", markdown, re.MULTILINE))
    extracted: list[tuple[str, str]] = []
    drop_spans: list[tuple[int, int]] = []

    for index, match in enumerate(headings):
        title = match.group(2).strip()
        # Exact match (case-insensitive): a prefix match would also swallow
        # "Livro de feitiços rúnicos modernos" into "Livro de feitiços rúnicos".
        if title.lower() not in {name.lower() for name in wanted}:
            continue

        level = len(match.group(1))
        end = len(markdown)
        for follow in headings[index + 1:]:
            if len(follow.group(1)) <= level:
                end = follow.start()
                break

        extracted.append((title, markdown[match.end(): end].strip()))
        drop_spans.append((match.start(), end))

    if not drop_spans:
        return markdown, []

    kept: list[str] = []
    cursor = 0
    for start, end in drop_spans:
        kept.append(markdown[cursor:start])
        cursor = end
    kept.append(markdown[cursor:])

    return re.sub(r"\n{3,}", "\n\n", "".join(kept)).strip(), extracted


class Command(BaseCommand):
    help = "Import the campaign .docx corpus as pages with source=folfier."

    def add_arguments(self, parser):
        parser.add_argument("--root", default=str(ROOT), help="Corpus folder")
        parser.add_argument("--dry-run", action="store_true",
                            help="Parse and report without writing")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--verbose", action="store_true",
                            help="List every page, not only multi-item documents")
        parser.add_argument("--reset", action="store_true",
                            help="Delete existing source=folfier pages before importing")

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(options["root"])
        if not root.exists():
            raise CommandError(f"pasta nao encontrada: {root}")

        files = sorted(root.rglob("*.docx"))
        if options["limit"]:
            files = files[: options["limit"]]
        self.stdout.write(f"{len(files)} arquivos em {root}\n")

        if options["reset"]:
            # Only pages created by this command are removed: official imported
            # content and hand-written pages are never touched.
            stale = Page.objects.filter(source=Source.FOLFIER)
            count = stale.count()
            stale.delete()
            self.stdout.write(f"páginas folfier removidas: {count}\n")

        categories = {c.slug: c for c in Category.objects.all()}
        created = updated = 0
        by_type: dict[str, int] = {}
        collisions: list[str] = []
        warnings: list[str] = []
        per_file: list[str] = []

        for path in files:
            document = parse_docx(path)
            folder = document.folder.lower()
            stem = Path(document.filename).stem

            if folder in FOLDER_MAP:
                category_slug, page_type = FOLDER_MAP[folder]
            else:
                key = re.sub(r"\s+", " ", stem.lower()).strip()
                category_slug, page_type = RULES_MAP.get(key, DEFAULT_RULES)

            parent_title = None
            if page_type == "subclass":
                hint = PARENT_RE.search(stem)
                if hint:
                    parent_title = CLASS_HINTS.get(hint.group(1).strip().lower())
                if not parent_title:
                    # No "(classe)" in the file name: match the entry title.
                    lowered = PREFIX_RE.sub("", stem).lower()
                    for needle, parent_slug in TITLE_HINTS.items():
                        if needle in lowered:
                            parent_title = parent_slug
                            break

            for item in document.items:
                title = (PREFIX_RE.sub("", item.title).strip()
                         or PREFIX_RE.sub("", stem).strip())
                if page_type == "feat":
                    title = re.sub(
                        r"\s*\((?:feat|feats)\)\s*:?[\s.]*$",
                        "",
                        title,
                        flags=re.IGNORECASE,
                    ).strip()

                # GM overrides: rename or drop this entry.
                if title.lower() in TITLE_OVERRIDES:
                    override = TITLE_OVERRIDES[title.lower()]
                    if override is None:
                        per_file.append(f"      - [descartado] {title[:70]}")
                        continue
                    title = override

                markdown = item.markdown

                # Split the class spell list out, but create the class page
                # first so the list can point at it as its parent.
                spell_list = None
                subtitle = ""
                named_subclasses: list[tuple[str, str]] = []
                if page_type == "class":
                    markdown, subtitle = normalize_class_markdown(markdown)
                    if title.strip().lower() == "runescaper":
                        markdown = normalize_runescaper_markdown(markdown)
                        markdown, named_subclasses = split_runescaper_subclasses(markdown)
                    markdown, spell_list = split_spell_list(markdown)

                # The GM named the subclass sections of the new classes.
                sub_sections: list[tuple[str, str]] = []
                if page_type == "class":
                    if named_subclasses:
                        sub_sections = named_subclasses
                    else:
                        wanted = CLASS_SUBCLASS_SECTIONS.get(stem.strip().lower())
                    if wanted and not sub_sections:
                        markdown, sub_sections = split_named_sections(markdown, wanted)

                if sub_sections:
                    # The subclass names must be links inside the class body,
                    # the same way the imported classes link their subclasses.
                    link_lines = "\n".join(
                        f"- [{section_title}](/subclasses/{slugify(f'{title}-{section_title}')})"
                        for section_title, _body in sub_sections
                    )
                    if title.strip().lower() != "runescaper":
                        markdown = (
                            markdown.rstrip()
                            + "\n\n## Subclasses\n\n"
                            + link_lines
                            + "\n\n"
                        )
                    if getattr(options, "verbose", False):
                        self.stdout.write(
                            f"      (links de subclasse inline: {len(sub_sections)})"
                        )

                if spell_list:
                    markdown = add_spell_list_link(
                        markdown, title, slugify(f"{title}-spell-list")
                    )

                was_created = self._upsert(
                    title=title,
                    page_type=page_type,
                    category_slug=category_slug,
                    item=DocxItem(title=title, markdown=markdown),
                    categories=categories,
                    parent_title=parent_title,
                    collisions=collisions,
                    subtitle=subtitle,
                )
                if was_created is None:
                    continue
                if was_created:
                    created += 1
                else:
                    updated += 1
                by_type[page_type] = by_type.get(page_type, 0) + 1
                per_file.append(f"      - [{page_type}] {title[:70]}")

                for section_title, section_markdown in sub_sections:
                    made = self._upsert(
                        title=section_title,
                        page_type="subclass",
                        category_slug="subclasses",
                        item=DocxItem(title=section_title, markdown=section_markdown),
                        categories=categories,
                        parent_title=None,
                        collisions=collisions,
                        slug_hint=slugify(f"{title}-{section_title}"),
                        as_child_of=title,
                    )
                    if made is not None:
                        if made:
                            created += 1
                        else:
                            updated += 1
                        by_type["subclass"] = by_type.get("subclass", 0) + 1
                        per_file.append(
                            f"      - [subclass] {title}: {section_title[:52]}"
                        )

                if spell_list:
                    made = self._upsert(
                        title=f"{title} Spell List",
                        # Wikidot exposes a class spell list as a related
                        # page of the class, under the Subclasses category.
                        # Keep homebrew class pages on that same shape instead
                        # of placing their generated list in the global spell
                        # index as if it were an individual spell.
                        page_type="subclass",
                        category_slug="subclasses",
                        item=DocxItem(title=f"{title} Spell List",
                                      markdown=spell_list),
                        categories=categories,
                        parent_title=None,
                        collisions=collisions,
                        slug_hint=slugify(f"{title}-spell-list"),
                        as_child_of=title,
                    )
                    if made is not None:
                        if made:
                            created += 1
                        else:
                            updated += 1
                        by_type["subclass"] = by_type.get("subclass", 0) + 1
                        per_file.append(f"      - [subclass] {title} Spell List")

                # The class is saved before its generated child pages. Re-render
                # it now so its subclass/spell-list links resolve immediately.
                if page_type == "class" and (sub_sections or spell_list):
                    parent = Page.objects.filter(slug=slugify(title)).first()
                    if parent:
                        save_page_with_derived_data(parent)

            if options["verbose"] or document.is_multi:
                self.stdout.write(f"\n  {path.parent.name}/{document.filename}"
                                  f" -> {len(document.items)} item(ns)")
                self.stdout.write("\n".join(per_file))
            per_file = []

            warnings.extend(document.warnings)

        if options["dry_run"]:
            transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"\npaginas criadas: {created}\npaginas atualizadas: {updated}"
        ))
        self.stdout.write("\npor tipo:")
        for page_type, count in sorted(by_type.items()):
            self.stdout.write(f"  {page_type:<14}{count:>5}")
        if collisions:
            self.stdout.write(f"\nconflitos de slug ({len(collisions)}):")
            for item in collisions[:20]:
                self.stdout.write(f"  {item}")
        if warnings:
            self.stdout.write(f"\navisos ({len(warnings)}):")
            for item in warnings[:20]:
                self.stdout.write(f"  {item}")

    def _upsert(self, title, page_type, category_slug, item, categories,
                parent_title, collisions, slug_hint=None, as_child_of=None, subtitle=""):
        slug = (slug_hint or slugify(title))[:180]
        if not slug:
            return None

        existing = Page.objects.filter(slug=slug).first()
        # Never overwrite imported official content with homebrew.
        if existing is not None and existing.source != Source.FOLFIER:
            collisions.append(f"{slug} (existe como {existing.source})")
            alt = f"{slug}-folfier"[:180]
            existing = Page.objects.filter(slug=alt).first()
            if existing is None:
                slug = alt

        was_created = existing is None
        page = existing or Page(slug=slug, title=title)
        page.title = title[:255]
        page.subtitle = subtitle[:255]
        page.page_type = page_type
        page.source = Source.FOLFIER
        page.edition = "D&D 2024"
        page.category = categories.get(category_slug)
        page.source_content = item.markdown
        page.structured_data = item.structured_data
        page.visibility = "public"
        page.is_published = True

        if parent_title:
            page.parent_page = Page.objects.filter(slug=parent_title).first()
        if as_child_of:
            # The spell list is reached from its class page, like the official
            # classes do.
            page.parent_page = Page.objects.filter(
                title__iexact=as_child_of
            ).first() or Page.objects.filter(slug=slugify(as_child_of)).first()

        save_page_with_derived_data(page)
        return was_created
