"""Check what the Folfier import actually produced, and what is missing."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")

import django

django.setup()

from django.db.models import Count

from wiki.models import Page

print("=== Folfier por tipo ===")
for row in (Page.objects.filter(source="folfier")
            .values("page_type").annotate(n=Count("id")).order_by("-n")):
    print(f"  {row['page_type']:<14}{row['n']:>4}")

print("\n=== Species (subracas) ===")
for page in Page.objects.filter(source="folfier", page_type="species"):
    print(f"  {page.title:<40} {page.url_path}  {len(page.source_content)} chars")

print("\n=== Classes Folfier: filhos (subclasses) ===")
for page in Page.objects.filter(source="folfier", page_type="class"):
    print(f"  {page.title:<36} subclasses={page.child_pages.count()}")

print("\n=== Todas as species (oficial + folfier) ===")
for page in Page.objects.filter(page_type="species")[:6]:
    print(f"  [{page.source:<9}] {page.title}")

print("\n=== Subclasses Folfier sem pai ===")
orphans = Page.objects.filter(source="folfier", page_type="subclass",
                              parent_page__isnull=True)
print(f"  total: {orphans.count()}")
for page in orphans[:12]:
    print(f"  {page.title[:48]:<50} {page.url_path}")

print("\n=== Magias Folfier (amostra) ===")
spells = Page.objects.filter(source="folfier", page_type="spell")
print(f"  total: {spells.count()}")
for page in spells[:6]:
    print(f"  {page.title:<34} level={(page.structured_data or {}).get('level')}")