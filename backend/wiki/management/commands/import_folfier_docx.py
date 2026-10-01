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

from docx_reader import parse_docx  # noqa: E402

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

PREFIX_RE = re.compile(
    r"^\s*(classe|sub|subclasse|sub-raça|subraca|raça|raca)\s*[-–:]\s*",
    re.IGNORECASE,
)
class Command(BaseCommand):
    help = "Import the campaign .docx corpus as pages with source=folfier."

    def add_arguments(self, parser):
        parser.add_argument("--root", default=str(ROOT), help="Corpus folder")
        parser.add_argument("--dry-run", action="store_true",
                            help="Parse and report without writing")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--verbose", action="store_true",
                            help="List every page, not only multi-item documents")

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(options["root"])
        if not root.exists():
            raise CommandError(f"pasta nao encontrada: {root}")

        files = sorted(root.rglob("*.docx"))
        if options["limit"]:
            files = files[: options["limit"]]
        self.stdout.write(f"{len(files)} arquivos em {root}\n")

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

            for item in document.items:
                title = (PREFIX_RE.sub("", item.title).strip()
                         or PREFIX_RE.sub("", stem).strip())
                was_created = self._upsert(
                    title=title,
                    page_type=page_type,
                    category_slug=category_slug,
                    item=item,
                    categories=categories,
                    parent_title=parent_title,
                    collisions=collisions,
                )
                if was_created is None:
                    continue
                if was_created:
                    created += 1
                else:
                    updated += 1
                by_type[page_type] = by_type.get(page_type, 0) + 1
                per_file.append(f"      - [{page_type}] {title[:70]}")

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
                parent_title, collisions):
        slug = slugify(title)[:180]
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

        save_page_with_derived_data(page)
        return was_created