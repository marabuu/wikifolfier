"""dnd2024 has no usable sitemap: find another way to enumerate its pages."""
import re
import sys
import time

import requests

BASE = "https://dnd2024.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}

INDEX_PAGES = [
    "main:home", "spells:all", "feat:all", "background:all",
    "main:classes", "main:items", "lineage:elf", "wizard",
    "items:all", "rules:all", "class:all", "spells:index",
]


def get(path: str) -> tuple[int, str]:
    response = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30)
    return response.status_code, response.text


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    print("--- sitemap attempts ---")
    for candidate in ["sitemap.xml", "sitemap-pages.xml", "robots.txt"]:
        response = session.get(f"{BASE}/{candidate}", timeout=25)
        body = response.text[:400]
        print(f"  {candidate}: {response.status_code} len={len(response.text)}")
        if candidate == "robots.txt":
            print("   ", body.replace("\n", " ")[:300])

    print("\n--- index pages: how many in-scope links each one exposes? ---")
    all_links = set()
    for path in INDEX_PAGES:
        status, text = get(path)
        content_start = text.find('<div id="page-content">')
        content = text[content_start:content_start + 400000] if content_start != -1 else ""
        hrefs = set(re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)(?:#|\")', content))
        print(f"  {path:<22} {status}  links={len(hrefs)}")
        if hrefs:
            all_links |= hrefs
        time.sleep(1.0)

    print(f"\n--- combined unique namespaces-prefixed links: {len(all_links)} ---")
    namespaces = {}
    for link in sorted(all_links):
        ns = link.split(":")[0]
        namespaces[ns] = namespaces.get(ns, 0) + 1
    for ns, count in sorted(namespaces.items(), key=lambda kv: -kv[1])[:30]:
        print(f"  {ns:<26}{count:>5}")

    print(f"\n--- sample links ---")
    for link in sorted(all_links)[:25]:
        print(f"  {link}")

    return 0


if __name__ == "__main__":
    sys.exit(main())