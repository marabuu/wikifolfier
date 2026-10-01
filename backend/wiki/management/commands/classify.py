"""Classify pages into sub-categories: spell level, feat kind, Unearthed Arcana.

Evidence-based, using data already present on the page:
- spell level   -> structured_data["level"] (0 = cantrip)
- feat kind     -> the wiki tags feats as originfeat / generalfeat /
                   fightingstylefeat / epicboonfeat
- Unearthed Arcana -> the wikidot path lives in the "ua:" namespace

Safe to re-run.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Category, Page
from wiki.management.commands.seed_categories import (
    FEAT_KINDS,
    SPELL_LEVELS,
)


class Command(BaseCommand):
    help = "Assign Page.subcategory for spells, feats and Unearthed Arcana pages."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {c.slug: c for c in Category.objects.all()}

        levels = {}
        for index, (name, level) in enumerate(SPELL_LEVELS):
            slug = "spell-cantrip" if level == 0 else f"spell-level-{level}"
            # Spell levels stay reachable by URL but are hidden from the
            # sidebar: /spells already groups by level and filters by it.
            category = self._ensure(
                categories, name=name, slug=slug, parent=categories.get("spells"),
                position=(index + 1) * 10, in_sidebar=False,
            )
            levels[level] = category

        feat_kinds = {}
        for index, (name, slug, tag) in enumerate(FEAT_KINDS):
            feat_kinds[tag] = self._ensure(
                categories, name=name, slug=slug, parent=categories.get("feats"),
                position=(index + 1) * 10,
            )

        ua = self._ensure(
            categories, name="Unearthed Arcana", slug="unearthed-arcana",
            parent=None, group="core", position=95,
        )

        stats = {"spells": 0, "spells_unclassified": 0, "feats": 0,
                 "feats_other": 0, "ua": 0}

        # Spells by level.
        for page in Page.objects.filter(page_type="spell"):
            level = (page.structured_data or {}).get("level")
            target = levels.get(level) if isinstance(level, int) else None
            if target is None:
                stats["spells_unclassified"] += 1
                page.subcategory = None
            else:
                stats["spells"] += 1
                page.subcategory = target
            page.save(update_fields=["subcategory"])

        # Feats by the wiki's own kind tags.
        for page in Page.objects.filter(page_type="feat"):
            tags = set(page.tags.values_list("slug", flat=True))
            target = next(
                (cat for tag, cat in feat_kinds.items() if tag in tags), None
            )
            if target is None:
                stats["feats_other"] += 1
            else:
                stats["feats"] += 1
            page.subcategory = target
            page.save(update_fields=["subcategory"])

        # Unearthed Arcana pages keep their own category but get grouped here.
        for page in Page.objects.all():
            path = str((page.structured_data or {}).get("wikidot_path", ""))
            if path.startswith("ua:"):
                page.subcategory = ua
                page.save(update_fields=["subcategory"])
                stats["ua"] += 1

        self.stdout.write(self.style.SUCCESS(str(stats)))
        for name, level in SPELL_LEVELS:
            count = Page.objects.filter(subcategory=levels[level]).count()
            self.stdout.write(f"  {name}: {count}")
        for tag, category in feat_kinds.items():
            self.stdout.write(f"  {category.name}: "
                              f"{Page.objects.filter(subcategory=category).count()}")
        self.stdout.write(f"  Unearthed Arcana: {Page.objects.filter(subcategory=ua).count()}")

    @staticmethod
    def _ensure(categories, name, slug, parent=None, group="core", position=100,
                in_sidebar=True):
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "parent": parent, "sidebar_group": group,
                      "position": position, "in_sidebar": in_sidebar},
        )
        categories[slug] = category
        changed = False
        if category.parent_id != (parent.id if parent else None):
            category.parent = parent
            changed = True
        if category.in_sidebar != in_sidebar:
            category.in_sidebar = in_sidebar
            changed = True
        if changed:
            category.save()
        return category