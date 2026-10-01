"""Compare the structure of an official class page with a Folfier one."""
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

TARGETS = ["wizard", "filho-da-magia", "runescaper", "witcher"]


def outline(page):
    content = page.source_content or ""
    headings = re.findall(r"^(#{2,4})\s*(.+)$", content, re.MULTILINE)
    tables = content.count("| --- |")
    first_para = next(
        (line for line in content.splitlines()
         if line.strip() and not line.startswith(("#", "|", "-"))),
        "",
    )
    return {
        "title": page.title,
        "subtitle": page.subtitle or "(vazio)",
        "chars": len(content),
        "headings": len(headings),
        "tables": tables,
        "intro": first_para[:90],
        "h2": [h[1] for h in headings if len(h[0]) == 2][:8],
        "h3": [h[1] for h in headings if len(h[0]) == 3][:6],
        "h4": [h[1] for h in headings if len(h[0]) == 4][:4],
    }


for slug in TARGETS:
    page = Page.objects.filter(slug=slug).first()
    if not page:
        print(f"!! {slug} nao encontrada")
        continue
    info = outline(page)
    print("=" * 72)
    print(f"{slug}  [{page.source}]")
    for key in ("title", "subtitle", "chars", "headings", "tables"):
        print(f"  {key:<9}: {info[key]}")
    print(f"  intro     : {info['intro']!r}")
    print(f"  H2        : {info['h2']}")
    print(f"  H3        : {info['h3']}")
    print(f"  H4        : {info['h4']}")