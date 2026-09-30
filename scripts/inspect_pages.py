"""Fetch and inspect a few real pages to design the parser."""
import re
import sys
import time

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}

TARGETS = [
    "spell:fireball",
    "wizard",
    "spells:all",
    "feat:alert",
    "wondrous-items:lucent-destroyer",
    "lineage:elf",
    "background:acolyte",
    "main:classes",
]


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    for path in TARGETS:
        url = f"{BASE}/{path}"
        response = session.get(url, timeout=30)
        text = response.text
        print("=" * 70)
        print(f"{path}  ->  {response.status_code}  ({len(text)} bytes)")

        title = re.search(r"<title>(.*?)</title>", text, re.S)
        print(f"  title: {title.group(1).strip()[:80] if title else '?'}")

        # 2024 markers
        for marker in ["2024", "2014", "5e", "PHB", "SRD"]:
            hits = len(re.findall(marker, text))
            if hits:
                print(f"  marker {marker!r}: {hits} hits")

        # module classes actually used
        modules = collections_counter(re.findall(r'class="[^"]*module-([a-z0-9\-_]+)', text))
        if modules:
            print(f"  modules: {dict(list(modules.items())[:14])}")

        # table / list density
        print(f"  tables={len(re.findall('<table', text, re.I))} "
              f"h2={len(re.findall('<h2', text, re.I))} "
              f"h3={len(re.findall('<h3', text, re.I))}")

        # category tags
        cats = set(re.findall(r'data-categor(?:y|ies)="([^"]+)"', text))
        if cats:
            print(f"  categories: {sorted(cats)[:12]}")

        # does the body live in #page-content?
        body = re.search(r'<div id="page-content">(.*?)<div id="footer"', text, re.S)
        if body:
            inner = body.group(1)
            print(f"  #page-content: {len(inner)} bytes "
                  f"(module-suppressed={len(re.findall('module-suppressed', inner))})")
            snippet = re.sub(r"\s+", " ", inner)[:400]
            print(f"  snippet: {snippet}")

        time.sleep(1.5)

    return 0


def collections_counter(items):
    import collections

    return collections.Counter(items)


if __name__ == "__main__":
    sys.exit(main())