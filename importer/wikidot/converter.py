"""Map Wikidot parsing output onto compendium Page fields."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .crawler import page_type_for
from .parser import ParseResult, WikidotParser

ORDINALS = ["", "cantrip", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"]

SPELL_FIELD_RE = re.compile(
    r"^(Casting Time|Range|Components|Duration)\s*:\s*(.+)$", re.MULTILINE | re.IGNORECASE
)
SCHOOL_RE = re.compile(r"(\d(?:st|nd|rd|th)[- ]level\s+)?([a-z]+)\s*$", re.IGNORECASE)


@dataclass
class ConvertedPage:
    title: str
    slug: str
    page_type: str
    category_slug: str
    source: str = "wikidot"
    subtitle: str = ""
    markdown: str = ""
    structured_data: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
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


def slugify(text: str) -> str:
    from django.utils.text import slugify as django_slugify

    return django_slugify(text)[:180]


class Converter:
    def __init__(self):
        self.parser = WikidotParser()

    def convert(self, path: str, raw_html: str, fallback_title: str = "") -> ConvertedPage:
        parsed = self.parser.parse(raw_html, page_path=path)
        page_type = page_type_for(path)
        title = fallback_title or path.split(":")[-1].replace("_", " ").title()

        structured = {}
        if page_type == "spell":
            structured = self._spell_data(parsed.markdown)
        elif page_type == "magic_item":
            structured = self._item_data(parsed.markdown)

        return ConvertedPage(
            title=title,
            slug=slugify(title),
            page_type=page_type,
            category_slug=CATEGORY_BY_PAGE_TYPE.get(page_type, "rules"),
            subtitle=parsed.subtitle,
            markdown=parsed.markdown,
            structured_data=structured,
            tags=[t for t in (parsed.source_label.lower().replace(" ", "-"),) if t],
            warnings=[f"{w.construct}: {w.snippet}" for w in parsed.warnings],
            links=parsed.links,
            images=parsed.images,
        )

    @staticmethod
    def _spell_data(markdown: str) -> dict:
        data: dict = {}
        for label, value in SPELL_FIELD_RE.findall(markdown):
            key = {
                "casting time": "casting_time",
                "range": "range",
                "components": "components",
                "duration": "duration",
            }[label.lower()]
            data[key] = value.strip()

        match = re.search(
            r"\b(cantrip|[1-9](?:st|nd|rd|th)[- ]level)\s+([a-z]+)", markdown, re.IGNORECASE
        )
        if match:
            level_word, school = match.group(1), match.group(2)
            data["level"] = 0 if level_word.lower() == "cantrip" else int(level_word[0])
            data["school"] = school.capitalize()

        classes = re.search(r"Spell Lists?\.\s*(.+)", markdown, re.IGNORECASE | re.DOTALL)
        if classes:
            names = re.findall(r"\[([^\]]+)\]", classes.group(1))
            data["classes"] = sorted({name.strip() for name in names if name.strip()})
        return data

    @staticmethod
    def _item_data(markdown: str) -> dict:
        data: dict = {}
        rarity = re.search(r"\b(Common|Uncommon|Rare|Very Rare|Legendary|Artifact|Varies)\b", markdown)
        if rarity:
            data["rarity"] = rarity.group(1)
        attunement = re.search(r"requires attunement", markdown, re.IGNORECASE)
        if attunement:
            data["requires_attunement"] = True
        kind = re.match(r"\s*([A-Z][a-z]+(?: [a-z]+)? item)", markdown)
        if kind:
            data["item_type"] = kind.group(1)
        return data