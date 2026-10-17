"""Create the default category tree.

There is no 'Homebrew' and no 'My Campaign' node: homebrew content lives inside
the very same categories as imported content.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Category

TREE = [
    # (name, parent, group, position)
    ("Classes", None, "core", 10),
    ("Subclasses", None, "core", 20),
    ("Species", None, "core", 30),
    ("Backgrounds", None, "core", 40),
    ("Feats", None, "core", 50),
    ("Spells", None, "core", 60),
    ("Equipment", None, "core", 70),
    ("Magic Items", None, "core", 80),
    ("Rules", None, "core", 90),
    ("Locations", None, "campaign", 10),
    ("NPCs", None, "campaign", 20),
    ("Factions", None, "campaign", 30),
    ("Lore", None, "campaign", 40),
    ("Events", None, "campaign", 50),
    ("Sessions", None, "campaign", 60),
    ("House Rules", None, "campaign", 70),
]

# Groupings inside a category. These are reached through Page.subcategory and
# never change the page URL (/spells/fireball stays under "spells").
SPELL_LEVELS = [
    ("Cantrip", 0),
    ("Level 1", 1),
    ("Level 2", 2),
    ("Level 3", 3),
    ("Level 4", 4),
    ("Level 5", 5),
    ("Level 6", 6),
    ("Level 7", 7),
    ("Level 8", 8),
    ("Level 9", 9),
]

FEAT_KINDS = [
    ("Origin Feats", "feat-origin", "originfeat"),
    ("General Feats", "feat-general", "generalfeat"),
    ("Fighting Styles", "feat-fighting-style", "fightingstylefeat"),
    ("Epic Boons", "feat-epic-boon", "epicboonfeat"),
]

SPELL_SCHOOLS = [
    "Abjuration", "Conjuration", "Divination", "Enchantment",
    "Evocation", "Illusion", "Necromancy", "Transmutation",
]


class Command(BaseCommand):
    help = "Create or update the default compendium category tree."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Delete categories without pages first."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created, updated = 0, 0
        for name, parent_name, group, position in TREE:
            parent = Category.objects.filter(name=parent_name).first() if parent_name else None
            cat, is_new = Category.objects.get_or_create(
                name=name,
                defaults={"parent": parent, "sidebar_group": group, "position": position},
            )
            if not is_new:
                changed = False
                if cat.parent_id != (parent.id if parent else None):
                    cat.parent = parent
                    changed = True
                if cat.sidebar_group != group:
                    cat.sidebar_group = group
                    changed = True
                if changed:
                    cat.save()
                    updated += 1
            else:
                created += 1

        if options["reset"]:
            Category.objects.filter(pages__isnull=True).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Categories: {created} created, {updated} updated.")
        )
