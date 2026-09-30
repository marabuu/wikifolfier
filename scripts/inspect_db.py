"""Inspect what actually landed in the database."""
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

from wiki.models import BrokenLink, Category, ImportRun, Page, PageLink, Tag


def main() -> int:
    print(f"Pages        : {Page.objects.count()}")
    print(f"Categories   : {Category.objects.count()}")
    print(f"Tags         : {Tag.objects.count()}")
    print(f"PageLinks    : {PageLink.objects.count()}")
    print(f"BrokenLinks  : {BrokenLink.objects.count()}")

    print("\nBy type:")
    for row in Page.objects.values("page_type").annotate(n=__import__("django.db.models", fromlist=["Count"]).Count("id")).order_by("-n"):
        print(f"  {row['page_type']:<20}{row['n']:>5}")

    print("\nSample pages:")
    for page in Page.objects.select_related("category")[:8]:
        print(f"  {page.title:<32} {page.page_type:<12} /{page.url_path}")
        if page.structured_data:
            print(f"      {page.structured_data}")

    fireball = Page.objects.filter(slug="fireball").first()
    if fireball:
        print(f"\nfireball.rendered_content ({len(fireball.rendered_content)} chars):")
        print(fireball.rendered_content[:400])

    print("\nImport runs:")
    for run in ImportRun.objects.all()[:3]:
        print(f"  {run.started_at:%Y-%m-%d %H:%M}  imported={run.pages_imported} "
              f"updated={run.pages_updated} broken={run.broken_links}")
    return 0


if __name__ == "__main__":
    sys.exit(main())