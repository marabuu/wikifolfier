"""Link orphaned subclasses to their parent class.

The importer sets parent_page when the class page already exists at import
time. Pages imported in a different order can end up without a parent, which
hides them from the class page. This backfills those links.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")

import django

django.setup()

from wiki.models import Page

CLASS_SLUGS = {
    "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
    "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
}

# A subclass title is frequently prefixed with its class ("Aberrant Sorcery"
# is a Wizard feature), so match on the whole class name first.
CLASS_TITLE_TO_SLUG = {
    "artificer": "artificer", "barbarian": "barbarian", "bard": "bard",
    "cleric": "cleric", "druid": "druid", "fighter": "fighter",
    "monk": "monk", "paladin": "paladin", "ranger": "ranger",
    "rogue": "rogue", "sorcerer": "sorcerer", "warlock": "warlock",
    "wizard": "wizard",
}


def main() -> int:
    orphans = list(Page.objects.filter(page_type="subclass", parent_page__isnull=True))
    print(f"subclasses sem parent: {len(orphans)}\n")

    linked, unresolved = 0, []
    for page in orphans:
        path = (page.structured_data or {}).get("wikidot_path", "")
        namespace = path.split(":")[0].lower() if ":" in path else ""

        parent = None
        if namespace:
            # Class landing pages are slugified from the class name.
            parent = Page.objects.filter(
                slug=namespace, page_type="class"
            ).first()

        if parent is None:
            unresolved.append(f"{page.title} ({path or page.slug})")
            continue

        page.parent_page = parent
        page.save(update_fields=["parent_page"])
        linked += 1

    print(f"vinculadas: {linked}")
    print(f"sem correspondencia: {len(unresolved)}")
    for item in unresolved[:15]:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())