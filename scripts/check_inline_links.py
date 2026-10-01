"""Are subclass links inline in the body, or only in the bottom section?"""
import os
import re
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


def report(slug):
    page = Page.objects.filter(slug=slug).first()
    if not page:
        print(f"!! {slug} nao encontrada")
        return
    body = page.rendered_content or ""
    links = re.findall(r'href="(/[^"]+)"', body)
    print("=" * 70)
    print(f"{slug} [{page.source}]  filhos={page.child_pages.count()}")
    print(f"  markdown links no CORPO: {len(links)}")
    for link in links[:14]:
        print(f"    {link}")

    # Spell-slot tables still inside the class body?
    if "| --- |" in (page.source_content or ""):
        head = re.findall(r"^\|\s*([^|]+?)\s*\|", page.source_content, re.M)[:6]
        print(f"  tabelas no corpo, colunas: {head}")
    if re.search(r"spell\s*slot|slots?\s+de\s+magia|Circle|slot", page.source_content or "", re.I):
        print("  >> mentions spell slots inside the class page")


for slug in ["wizard", "filho-da-magia", "runescaper", "dovahkiin", "witcher"]:
    report(slug)