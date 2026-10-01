"""Compare the official and Folfier versions of a page before merging."""
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

from wiki.models import Page

slug = sys.argv[1] if len(sys.argv) > 1 else "warrior-of-mercy"

for page in Page.objects.filter(slug__startswith=slug):
    print("=" * 72)
    print(f"{page.title}  | source={page.source}  | {page.url_path}")
    print(f"  markdown ({len(page.source_content)} chars):")
    print(page.source_content[:2500])
    print()