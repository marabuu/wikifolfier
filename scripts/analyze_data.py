"""Inspect real data to design the sub-categorisation from evidence, not guesses."""
import os
import sys
from collections import Counter
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

print("=== TAG FREQUENCY ON FEATS ===")
counter = Counter()
for page in Page.objects.filter(page_type="feat"):
    counter.update(page.tags.values_list("slug", flat=True))
for tag, count in counter.most_common(30):
    print(f"  {tag:<32}{count:>5}")

print("\n=== SAMPLE FEAT structured_data ===")
for page in Page.objects.filter(page_type="feat")[:5]:
    print(f"  {page.title:<26} sd={page.structured_data}")
    print(f"      tags={[t.slug for t in page.tags.all()]}")

print("\n=== SPELL: level distribution + school ===")
levels, schools, classes = Counter(), Counter(), Counter()
missing_level = 0
for page in Page.objects.filter(page_type="spell"):
    sd = page.structured_data or {}
    if "level" not in sd:
        missing_level += 1
    else:
        levels[sd["level"]] += 1
    if sd.get("school"):
        schools[sd["school"]] += 1
    for klass in sd.get("classes", []) or []:
        classes[klass] += 1
print("  level:", dict(sorted(levels.items(), key=lambda kv: (kv[0] is None, kv[0]))))
print(f"  spells without level: {missing_level}")
print("  school:", dict(schools.most_common(10)))
print("  classes (top 12):", dict(classes.most_common(12)))

print("\n=== SPELL: do tags also carry class? ===")
spell_tags = Counter()
for page in Page.objects.filter(page_type="spell")[:120]:
    spell_tags.update(page.tags.values_list("slug", flat=True))
for tag, count in spell_tags.most_common(25):
    print(f"  {tag:<28}{count:>5}")

print("\n=== UA PAGES: how are they identified? ===")
ua = Page.objects.filter(structured_data__has_key="wikidot_path")
ua_paths = [p for p in Page.objects.all()
            if str((p.structured_data or {}).get("wikidot_path", "")).startswith("ua:")]
print(f"  pages whose wikidot_path starts with ua: {len(ua_paths)}")
for page in ua_paths[:10]:
    print(f"    {page.title:<40} sd_tags={[t.slug for t in page.tags.all()]}")

source_tags = Counter()
for page in Page.objects.all():
    for tag in page.tags.values_list("slug", flat=True):
        if tag.startswith("source-"):
            source_tags[tag] += 1
print("\n  source-* tags:", dict(source_tags.most_common(20)))
