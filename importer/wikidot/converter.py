"""Map parsed Wikidot output onto compendium Page fields."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .filters import page_type_for
from .parser import ParseResult, WikidotParser


@dataclass
class ConvertedPage:
    title: str
    slug: str
    page_type: str
    category_slug: str
    source: str = "wikidot"
    edition: str = "D&D 2024"
    subtitle: str = ""
    markdown: str = ""
    structured_data: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source_label: str = ""
    warnings: list[str] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    images: list[str] = field(default_factory=list)


CATEGORY_BY_PAGE_TYPE = {
    "class": "classes",
    "subclass": "subclasses",
    "species": "species",
    "background": "backgrounds",
    "feat": "feats",
    "spell": "spells",
    "magic_item": "magic-items",
    "equipment": "equipment",
    "weapon": "weapons",
    "armor": "armor",
    "adventuring_gear": "adventuring-gear",
    "rule": "rules",
    "condition": "rules",
}

SPELL_FIELD_RE = re.compile(
    r"^\s*\*{0,2}(Casting Time|Range|Components|Duration)\*{0,2}\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Covers both header styles:
#   2024: "Level 3 Evocation (Sorcerer, Wizard)" / "Evocation Cantrip"
#   2014: "3rd-level evocation" / "cantrip (th)"
VALID_SCHOOLS = {
    "abjuration", "conjuration", "divination", "enchantment",
    "evocation", "illusion", "necromancy", "transmutation",
}

# 2024 header: "*Level 3 Evocation (Sorcerer, Wizard)*" / "*Evocation Cantrip (Warlock)*"
HEADER_2024_RE = re.compile(
    r"\b(?:Level\s+(?P<level>[1-9])\s+(?P<school>[a-z]+)|(?P<school2>[a-z]+)\s+Cantrip)"
    r"\s*(?:\((?P<classes>[^)]*)\))?",
    re.IGNORECASE,
)
HEADER_2014_RE = re.compile(
    r"\b(?:(?P<level>[1-9])(?:st|nd|rd|th)[- ]level\s+(?P<school>[a-z]+)|"
    r"(?P<school2>[a-z]+)\s+(?:\(\s*cantrip\s*\)|Cantrip))"
    r"\s*(?:\((?P<classes>[^)]*)\))?",
    re.IGNORECASE,
)
RARITY_RE = re.compile(r"\b(Common|Uncommon|Rare|Very Rare|Legendary|Artifact|Varies)\b")
ATTUNEMENT_RE = re.compile(r"requires?\s+attunement", re.IGNORECASE)
ITEM_TYPE_RE = re.compile(
    r"^\s*\**\s*(?P<type>[A-Z][a-z]+\s+Item|Item)\b", re.MULTILINE
)
SPELL_LIST_RE = re.compile(r"Spell Lists?\.", re.IGNORECASE)

# Class names used to recognise the per-class tags the wiki puts on spells.
# Includes the campaign's homebrew classes so their spells are recognised too.
CLASS_NAMES = {
    "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
    "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    "runescaper", "filho-da-magia", "heroi",
}


def slugify(text: str) -> str:
    from django.utils.text import slugify as django_slugify

    return django_slugify(text)[:180]


class Converter:
    def __init__(self):
        self.parser = WikidotParser()

    def convert_page(self, page_html: str, path: str) -> ConvertedPage:
        parsed = self.parser.parse_page(page_html, page_path=path)
        return self._build(path, parsed)

    def convert(self, path: str, raw_html: str,
                fallback_title: str = "") -> ConvertedPage:
        parsed = self.parser.parse(raw_html, page_path=path)
        return self._build(path, parsed, fallback_title)

    def _build(self, path: str, parsed: ParseResult,
               fallback_title: str = "") -> ConvertedPage:
        page_type = page_type_for(path)
        title = parsed.title or fallback_title or path.split(":")[-1].replace("_", " ")
        title = re.sub(r"^(Background|Species|Feat|Spell|Magic Item)\s*:\s*", "", title)

        structured: dict = {}
        if page_type == "spell":
            structured = self._spell_data(parsed)
        elif page_type in {"magic_item", "weapon", "armor"}:
            structured = self._item_data(parsed)

        tags = list(dict.fromkeys(parsed.tags))
        if parsed.source_label:
            slug = re.sub(r"[^a-z0-9]+", "-", parsed.source_label.lower()).strip("-")
            if slug:
                tags.append(f"source-{slug}")

        return ConvertedPage(
            title=title.strip(),
            slug=slugify(title),
            page_type=page_type,
            category_slug=CATEGORY_BY_PAGE_TYPE.get(page_type, "rules"),
            edition="D&D 2024",
            subtitle=parsed.subtitle,
            markdown=parsed.markdown,
            # The Wikidot path keeps the namespace, which is the only way to
            # know which class a subclass belongs to once the title is slugified.
            structured_data={**structured, "wikidot_path": path},
            tags=tags,
            source_label=parsed.source_label,
            warnings=[f"{w.construct}: {w.snippet}" for w in parsed.warnings],
            links=parsed.links,
            images=parsed.images,
        )

    @staticmethod
    def _spell_data(parsed: ParseResult) -> dict:
        data: dict = {}
        haystack = "\n".join(parsed.header_lines) + "\n" + parsed.markdown[:4000]

        for label, value in SPELL_FIELD_RE.findall(haystack):
            key = {
                "casting time": "casting_time",
                "range": "range",
                "components": "components",
                "duration": "duration",
            }[label.lower()]
            # Values may still carry a stray "**" from the bold label.
            data[key] = value.strip().lstrip("*").strip()

        for pattern in (HEADER_2024_RE, HEADER_2014_RE):
            match = pattern.search(haystack)
            if not match:
                continue
            groups = match.groupdict()
            school = (groups.get("school") or groups.get("school2") or "").lower()
            # Guard against words that merely look like a school name.
            if school in VALID_SCHOOLS:
                data["school"] = school.capitalize()
            level = groups.get("level")
            data["level"] = int(level) if level else 0
            break

        # 2024 lists the classes in the header: "Level 3 Evocation (Sorcerer, Wizard)"
        raw_classes: set[str] = set()
        header_match = HEADER_2024_RE.search(haystack) or HEADER_2014_RE.search(haystack)
        if header_match and header_match.group("classes"):
            for name in header_match.group("classes").split(","):
                name = name.strip().strip("*").strip()
                if name and len(name) <= 40:
                    raw_classes.add(name)

        # 2014 lists them as links under "Spell Lists."
        spell_list = SPELL_LIST_RE.search(parsed.markdown)
        if spell_list:
            tail = parsed.markdown[spell_list.end(): spell_list.end() + 600]
            raw_classes.update(c.strip() for c in re.findall(r"\[([^\]]+)\]", tail))

        # The wiki also tags each spell with the classes that can cast it.
        raw_classes.update(t for t in parsed.tags if t in CLASS_NAMES)

        # Normalise: "wizard", "Wizard" and "WIZARD" are the same class.
        # Homebrew classes (runescaper, filho-da-magia, heroi) are stored as
        # slugs so the spell-index filter can find them by slug.
        classes: set[str] = set()
        for name in raw_classes:
            slug = name.strip().lower()
            if slug in CLASS_NAMES:
                classes.add(slug)
            else:
                classes.add(name.strip())

        if classes:
            data["classes"] = sorted(classes)
        return data

    @staticmethod
    def _item_data(parsed: ParseResult) -> dict:
        data: dict = {}
        haystack = "\n".join(parsed.header_lines) + "\n" + parsed.markdown[:3000]

        rarity = RARITY_RE.search(haystack)
        if rarity:
            data["rarity"] = rarity.group(1)
        if ATTUNEMENT_RE.search(haystack):
            data["requires_attunement"] = True
        kind = ITEM_TYPE_RE.search(haystack)
        if kind:
            data["item_type"] = kind.group("type").strip()
        return data