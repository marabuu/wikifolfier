"""Data integrity check: subclass categories, parent links and URL shape."""
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

from django.db.models import Count

from wiki.models import Category, Page

print("--- pages com parent_page, por categoria ---")
rows = (
    Page.objects.filter(parent_page__isnull=False)
    .values("category__slug", "page_type")
    .annotate(n=Count("id"))
    .order_by("-n")
)
for row in rows:
    print(f"  {str(row['category__slug']):<16} {row['page_type']:<12} {row['n']:>4}")

wrong = Page.objects.filter(
    parent_page__isnull=False, page_type="subclass"
).exclude(category__slug="subclasses")
print(f"\nsubclasses com categoria errada: {wrong.count()}")
for page in wrong[:10]:
    print(f"  {page.title:<30} url={page.url_path}  cat={page.category}")

print("\n--- subclasses sem parent_page ---")
orphan = Page.objects.filter(page_type="subclass", parent_page__isnull=True)
print(f"  total: {orphan.count()}")
for page in orphan[:10]:
    print(f"  {page.title:<32} {page.url_path}")

print("\n--- classes sem parent (ok) e sem filho ---")
classes = Page.objects.filter(page_type="class")
print(f"  classes: {classes.count()}")
for klass in classes:
    n = klass.child_pages.count()
    if n == 0:
        print(f"  SEM SUBCLASSES: {klass.title:<28} {klass.url_path}")
