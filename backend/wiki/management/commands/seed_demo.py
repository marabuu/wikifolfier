"""Minimal demonstration content.

Shows the core rule: homebrew content is indistinguishable from imported content
except for the `source` metadata shown on the page.
"""
from django.core.management.base import BaseCommand

from wiki.models import Category, Page, PageType, Source
from wiki.services import save_page_with_derived_data

FIREBALL_DATA = {
    "level": 3,
    "school": "Evocation",
    "casting_time": "1 action",
    "range": "150 feet",
    "components": "V, S, M (a tiny ball of bat guano and sulfur)",
    "duration": "Instantaneous",
    "classes": ["Sorcerer", "Wizard"],
}

RUNE_BLAST_DATA = {
    "level": 2,
    "school": "Evocation",
    "casting_time": "1 action",
    "range": "60 feet",
    "components": "V, M (a carved rune)",
    "duration": "Instantaneous",
    "classes": ["Rune Mage"],
}

PAGES = [
    {
        "title": "Wizard",
        "subtitle": "Wizards are supreme magic-users",
        "category": "Classes",
        "page_type": PageType.CLASS,
        "source": Source.WIKIDOT,
        "tags": ["wizard", "caster"],
        "markdown": """Wizards are supreme magic-users, defined and united as a class by the spells they cast.

## Hit Points

Hit Dice: 1d6 per wizard level

Hit Points at 1st Level: 6 + your Constitution modifier

## Proficiencies

| Category | Proficiencies |
|---|---|
| Armor | None |
| Weapons | Daggers, darts, slings, quarterstaffs, light crossbows |
| Tools | None |

See also [Fireball](/fireball) and [Magic Missile](/magic-missile).""",
    },
    {
        "title": "Rune Mage",
        "subtitle": "A rune-carved battle mage",
        "category": "Classes",
        "page_type": PageType.CLASS,
        "source": Source.HOMEBREW,
        "tags": ["rune", "caster", "homebrew"],
        "markdown": """A rune mage inscribes glyphs into flesh and steel, binding short-lived laws to the world.

## Hit Points

Hit Dice: 1d8 per rune mage level

## Class Features

### Runeweaving

At 2nd level you can inscribe a rune during a short rest.

See also [Wizard](/wizard) and [Rune Blast](/rune-blast).""",
    },
    {
        "title": "Fireball",
        "page_type": PageType.SPELL,
        "category": "Spells",
        "source": Source.WIKIDOT,
        "tags": ["fire", "level-3", "evocation"],
        "structured_data": FIREBALL_DATA,
        "markdown": """A bright streak flashes from your pointing finger to a point you choose within range then blossoms with a low roar into an explosion of flame.

## At Higher Levels

When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.""",
    },
    {
        "title": "Rune Blast",
        "page_type": PageType.SPELL,
        "category": "Spells",
        "source": Source.HOMEBREW,
        "tags": ["rune", "level-2", "evocation", "homebrew"],
        "structured_data": RUNE_BLAST_DATA,
        "markdown": """You carve a sigil into the air and it detonates as force.

## At Higher Levels

The damage increases by 1d8 for each slot level above 2nd.""",
    },
    {
        "title": "Martial Rune Tradition",
        "page_type": PageType.SUBCLASS,
        "category": "Subclasses",
        "source": Source.HOMEBREW,
        "parent_title": "Rune Mage",
        "tags": ["rune", "homebrew"],
        "markdown": """Traditions of the martial rune warrior.

## Features

Your training focuses on weapon and rune synergy.""",
    },
    {
        "title": "Bag of Holding",
        "page_type": PageType.MAGIC_ITEM,
        "category": "Magic Items",
        "source": Source.WIKIDOT,
        "structured_data": {
            "item_type": "Wondrous item",
            "rarity": "Uncommon",
            "requires_attunement": False,
        },
        "markdown": """A bag with an extradimensional space accessible by any mundane opening.""",
    },
    {
        "title": "Terra das Estranhezas",
        "page_type": PageType.LOCATION,
        "category": "Locations",
        "source": Source.CAMPAIGN,
        "tags": ["campanha", "continente"],
        "markdown": """O continente onde a campanha se passa.

## Regiões

- Neverwinter Woods
- Ruínas de Salmuria""",
    },
    {
        "title": "Neverwinter Woods",
        "page_type": PageType.LOCATION,
        "category": "Locations",
        "source": Source.CAMPAIGN,
        "visibility": "gm_only",
        "tags": ["campanha", "regiao"],
        "markdown": """Floresta antiga ao norte. Apenas o GM conhece o segredo da torre.

## Segredo

Uma ruína abissal guarda o portal para [Terra das Estranhezas](/terra-das-estranhezas).""",
    },
]


class Command(BaseCommand):
    help = "Seed example pages demonstrating official + homebrew + campaign content."

    def handle(self, *args, **options):
        categories = {c.name: c for c in Category.objects.all()}
        made = 0

        for data in PAGES:
            spec = dict(data)
            category = categories.get(spec.pop("category", ""), None)
            parent_title = spec.pop("parent_title", None)
            tags = spec.pop("tags", [])
            markdown = spec.pop("markdown", "")
            visibility = spec.pop("visibility", "public")
            structured = spec.pop("structured_data", {})

            page = Page.objects.filter(title__iexact=data["title"]).first()
            if page is None:
                page = Page(title=data["title"])
            page.subtitle = spec.get("subtitle", "")
            page.page_type = spec.get("page_type", PageType.OTHER)
            page.source = spec.get("source", Source.CUSTOM)
            page.category = category
            page.visibility = visibility
            page.source_content = markdown
            page.structured_data = structured
            if parent_title:
                page.parent_page = Page.objects.filter(title__iexact=parent_title).first()

            save_page_with_derived_data(page, tags)
            made += 1

        self.stdout.write(self.style.SUCCESS(f"Upserted {made} example pages."))