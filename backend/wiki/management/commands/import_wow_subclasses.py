"""Import World of Warcraft subclasses and their cited spells from dnd2024.wikidot.com.

Imports:
1. The 9 subclasses tagged 'wow':
   - Barbarian: Path of the Elements, Path of the Spiritual Guardian
   - Cleric: Discipline Domain, Shadow Domain
   - Monk: Warrior of Mystic Brews
   - Paladin: Oath of the Ebon Blade, Oath of the Holy
   - Ranger: Demon Hunter
   - Rogue: Swashbuckler
2. ONLY the 27 spells cited/referenced by these subclasses.
3. Preserves all existing homebrew content.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.request
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

# Ensure importer module can be imported
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "importer") not in sys.path:
    sys.path.insert(0, str(ROOT / "importer"))

from wikidot.converter import Converter
from wiki.models import Category, Page, Source
from wiki.services import save_page_with_derived_data

BASE_URL = "http://dnd2024.wikidot.com"

SUBCLASSES = [
    ("barbarian", "path-of-the-elements", "Path of the Elements"),
    ("barbarian", "path-of-the-spiritual-guardian", "Path of the Spiritual Guardian"),
    ("cleric", "discipline-domain", "Discipline Domain"),
    ("cleric", "shadow-domain", "Shadow Domain"),
    ("monk", "warrior-of-mystic-brews", "Warrior of Mystic Brews"),
    ("paladin", "oath-of-the-ebon-blade", "Oath of the Ebon Blade"),
    ("paladin", "oath-of-the-holy", "Oath of the Holy"),
    ("ranger", "demon-hunter", "Demon Hunter"),
    ("rogue", "swashbuckler", "Swashbuckler"),
]

# Spells from the WoW book cited by these subclasses
CITED_WOW_SPELLS = [
    "bonestorm",
    "chains-of-ice",
    "chaos-nova",
    "collapsing-star",
    "consume-soul",
    "death-and-decay",
    "death-grip",
    "demon-spikes",
    "eye-beam",
    "fel-rush",
    "fiery-brand",
    "frostscythe",
    "infernal-strike",
    "leeching-strike",
    "metamorphosis",
    "prayer-of-mending",
    "psychic-horror",
    "remorseless-winter",
    "rune-strike",
    "scourge-strike",
    "shadow-word-pain",
    "sigil-of-chains",
    "sigil-of-flame",
    "soul-reap",
    "throw-glaive",
    "vampiric-blood",
    "void-eruption",
]

LEVEL_SUBCAT_MAP = {
    0: "spell-cantrip",
    1: "spell-level-1",
    2: "spell-level-2",
    3: "spell-level-3",
    4: "spell-level-4",
    5: "spell-level-5",
    6: "spell-level-6",
    7: "spell-level-7",
    8: "spell-level-8",
    9: "spell-level-9",
}

LEVEL_TAG_MAP = {
    0: "cantrip",
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
}

CLASS_MAPPINGS = {
    "paladin": "paladin",
    "death knight": ("paladin", "cavaleiro-da-morte"),
    "ranger": "ranger",
    "demon hunter": ("ranger", "cacador-de-demonios"),
    "cleric": "cleric",
    "druid": "druid",
    "sorcerer": "sorcerer",
    "warlock": "warlock",
    "wizard": "wizard",
    "artificer": "artificer",
    "barbarian": "barbarian",
    "bard": "bard",
    "fighter": "fighter",
    "monk": "monk",
    "rogue": "rogue",
    "shaman": "xama",
}


def normalize_classes(raw_classes: list[str]) -> tuple[list[str], list[str]]:
    classes = set()
    extra_tags = set()
    for item in raw_classes:
        s = str(item).strip()
        s_clean = re.sub(r"\[.*?\]\(.*?\)", "", s)
        s_lower = s_clean.lower()
        for pattern, target in CLASS_MAPPINGS.items():
            if pattern in s_lower:
                if isinstance(target, tuple):
                    for t in target:
                        classes.add(t)
                else:
                    classes.add(target)
    return sorted(list(classes)), sorted(list(extra_tags))


class Command(BaseCommand):
    help = "Import WoW subclasses and their cited spells from Wikidot."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying DB")
        parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests in seconds")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delay = options["delay"]
        converter = Converter()

        subclasses_cat = Category.objects.filter(slug="subclasses").first()
        spells_cat = Category.objects.filter(slug="spells").first()

        subcats = {
            c.slug: c for c in Category.objects.filter(parent=spells_cat)
        }

        # ----------------------------------------------------
        # 1. Import Cited Spells
        # ----------------------------------------------------
        self.stdout.write(f"\n=== Step 1: Importing {len(CITED_WOW_SPELLS)} Cited WoW Spells ===")
        imported_spells = 0

        for idx, spell_slug in enumerate(CITED_WOW_SPELLS, 1):
            path = f"spell:{spell_slug}"
            url = f"{BASE_URL}/{path}"
            time.sleep(delay)

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req) as resp:
                    page_html = resp.read().decode("utf-8", errors="ignore")

                conv = converter.convert_page(page_html, path)
                sd = dict(conv.structured_data)

                level = sd.get("level", 0)
                if level is None:
                    level = 0
                school = sd.get("school", "")

                classes, extra_tags = normalize_classes(sd.get("classes", []))
                sd["classes"] = classes
                sd["wikidot_path"] = path

                subcat_slug = LEVEL_SUBCAT_MAP.get(level)
                subcat = subcats.get(subcat_slug) if subcat_slug else None

                tag_names = set(conv.tags)
                tag_names.add("wow")
                tag_names.add("source-world-of-warcraft")
                if school:
                    tag_names.add(school.lower())
                lvl_tag = LEVEL_TAG_MAP.get(level)
                if lvl_tag:
                    tag_names.add(lvl_tag)
                for cls in classes:
                    tag_names.add(cls)

                clean_tags = [str(t).strip().lower() for t in tag_names if str(t).strip()]

                if dry_run:
                    self.stdout.write(f"  [{idx}/{len(CITED_WOW_SPELLS)}] [DRY-RUN] Spell: {conv.title} (Lvl {level} {school}) -> {classes}")
                    continue

                with transaction.atomic():
                    page, created = Page.objects.get_or_create(
                        slug=conv.slug,
                        defaults={
                            "title": conv.title,
                            "subtitle": conv.subtitle or "",
                            "page_type": "spell",
                            "category": spells_cat,
                            "subcategory": subcat,
                            "source": "wikidot",
                            "edition": "D&D 2024",
                            "visibility": "public",
                            "is_published": True,
                            "structured_data": sd,
                            "source_content": conv.markdown,
                        },
                    )
                    if not created:
                        page.title = conv.title
                        page.subtitle = conv.subtitle or ""
                        page.page_type = "spell"
                        page.category = spells_cat
                        page.subcategory = subcat
                        page.source = "wikidot"
                        page.edition = "D&D 2024"
                        page.visibility = "public"
                        page.is_published = True
                        page.structured_data = sd
                        page.source_content = conv.markdown

                    save_page_with_derived_data(page, tag_names=clean_tags)
                    page.update_search_vector()
                    imported_spells += 1
                    status = "Created" if created else "Updated"
                    self.stdout.write(f"  [{idx}/{len(CITED_WOW_SPELLS)}] {status}: {page.title} (Lvl {level})")

            except Exception as e:
                self.stderr.write(f"  [{idx}/{len(CITED_WOW_SPELLS)}] ERROR importing {url}: {e}")

        # ----------------------------------------------------
        # 2. Import Subclasses
        # ----------------------------------------------------
        self.stdout.write(f"\n=== Step 2: Importing {len(SUBCLASSES)} WoW Subclasses ===")
        imported_subclasses = 0

        for idx, (class_slug, sub_slug, default_title) in enumerate(SUBCLASSES, 1):
            path = f"{class_slug}:{sub_slug}"
            url = f"{BASE_URL}/{path}"
            time.sleep(delay)

            try:
                parent_class = Page.objects.filter(slug=class_slug, page_type="class").first()
                if not parent_class:
                    self.stderr.write(f"  Warning: Parent class '{class_slug}' not found!")

                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req) as resp:
                    page_html = resp.read().decode("utf-8", errors="ignore")

                conv = converter.convert_page(page_html, path)
                sd = dict(conv.structured_data)
                sd["wikidot_path"] = path

                tag_names = set(conv.tags)
                tag_names.add("subclass")
                tag_names.add("wow")
                tag_names.add("source-world-of-warcraft")
                tag_names.add(class_slug)

                clean_tags = [str(t).strip().lower() for t in tag_names if str(t).strip()]

                if dry_run:
                    self.stdout.write(f"  [{idx}/{len(SUBCLASSES)}] [DRY-RUN] Subclass: {conv.title} ({conv.slug}) -> Parent: {class_slug}")
                    continue

                with transaction.atomic():
                    page, created = Page.objects.get_or_create(
                        slug=conv.slug,
                        defaults={
                            "title": conv.title,
                            "subtitle": conv.subtitle or "",
                            "page_type": "subclass",
                            "category": subclasses_cat,
                            "parent_page": parent_class,
                            "source": "wikidot",
                            "edition": "D&D 2024",
                            "visibility": "public",
                            "is_published": True,
                            "structured_data": sd,
                            "source_content": conv.markdown,
                        },
                    )
                    if not created:
                        page.title = conv.title
                        page.subtitle = conv.subtitle or ""
                        page.page_type = "subclass"
                        page.category = subclasses_cat
                        page.parent_page = parent_class
                        page.source = "wikidot"
                        page.edition = "D&D 2024"
                        page.visibility = "public"
                        page.is_published = True
                        page.structured_data = sd
                        page.source_content = conv.markdown

                    save_page_with_derived_data(page, tag_names=clean_tags)
                    page.update_search_vector()
                    imported_subclasses += 1
                    status = "Created" if created else "Updated"
                    self.stdout.write(f"  [{idx}/{len(SUBCLASSES)}] {status}: {page.title} -> Parent: {parent_class.title if parent_class else 'None'}")

            except Exception as e:
                self.stderr.write(f"  [{idx}/{len(SUBCLASSES)}] ERROR importing {url}: {e}")

        # ----------------------------------------------------
        # 3. Update Parent Class inline links
        # ----------------------------------------------------
        if not dry_run:
            self.stdout.write("\n=== Step 3: Updating Subclass Links on Parent Classes ===")
            SUBCLASS_HEADING = "## Subclasses"
            affected_classes = set(c for c, _, _ in SUBCLASSES)
            for cls_slug in affected_classes:
                class_page = Page.objects.filter(slug=cls_slug, page_type="class").first()
                if not class_page:
                    continue
                subclasses = list(class_page.child_pages.filter(page_type="subclass").order_by("title"))
                if not subclasses:
                    continue

                body = class_page.source_content or ""
                # Replace existing ## Subclasses section
                idx = body.find(SUBCLASS_HEADING)
                if idx != -1:
                    end = body.find("\n## ", idx + len(SUBCLASS_HEADING))
                    body = (body[:idx] + body[end + 1:]) if end != -1 else body[:idx]

                lines = "\n".join(f"- [{sub.title}]({sub.url_path})" for sub in subclasses)
                block = f"{SUBCLASS_HEADING}\n\n{lines}\n"
                class_page.source_content = body.rstrip() + "\n\n" + block
                save_page_with_derived_data(class_page)
                self.stdout.write(f"  Updated class '{class_page.title}' with {len(subclasses)} subclasses.")

            self.stdout.write(self.style.SUCCESS(
                f"\nSuccessfully finished! Imported {imported_subclasses} subclasses and {imported_spells} cited spells."
            ))
