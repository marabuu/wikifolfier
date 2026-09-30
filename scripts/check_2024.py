"""Is the D&D 2024 content on this wiki? Sample real pages and read their tags."""
import re
import sys
import time
from collections import Counter

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}

# Sample across namespaces, including known "2024-flavoured" candidates.
PATHS = [
    "spell:fireball", "spell:blade-ward", "feat:alert", "wizard",
    "wizard:abjuration", "lineage:elf", "background:acolyte",
    "condition:blinded", "poisons:wyvern-poison", "discipline:crown-of-rage",
    "ranger:beast-master", "blood-hunter:profane-soul", "main:home",
    "spell:eldritch-blast", "feat:grappler", "lineage:halfling",
]


def page_tags(text: str) -> list[str]:
    block = re.search(r'<div class="page-tags">(.*?)</div>', text, re.S)
    if not block:
        return []
    return re.findall(r"/system:page-tags/tag/([^#\"]+)", block.group(1))


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    tag_counter = Counter()
    year_counter = Counter()

    for path in PATHS:
        response = session.get(f"{BASE}/{path}", timeout=30)
        text = response.text
        tags = page_tags(text)
        tag_counter.update(tags)

        years = Counter(re.findall(r"\b(20\d\d)\b", text))
        year_counter.update(years)

        title = re.search(r"<title>(.*?)</title>", text, re.S)
        print(f"{path:<34} {response.status_code} tags={tags[:9]}")

        # Look for explicit 2024 phrasing in the article body only.
        content = text[text.find('<div id="page-content">'):]
        content = content[:6000] if content else ""
        for marker in ["2024", "2014"]:
            if marker in content:
                idx = content.find(marker)
                snippet = re.sub(r"<[^>]+>", "", content[max(0, idx-70):idx+70])
                print(f"      body {marker}: ...{snippet.strip()}...")
        time.sleep(1.2)

    print(f"\n=== TAGS ACROSS SAMPLE ({len(PATHS)} pages) ===")
    for tag, count in tag_counter.most_common(40):
        print(f"  {tag}: {count}")

    print(f"\n=== YEARS IN FULL HTML ===")
    for year, count in year_counter.most_common():
        print(f"  {year}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())