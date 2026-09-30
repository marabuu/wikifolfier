"""Compare the scope of dnd5e vs dnd2024 so the import target can be chosen."""
import collections
import re
import sys
import time

import requests

HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}
SITES = ["https://dnd2024.wikidot.com", "https://dnd5e.wikidot.com"]


def get(url: str, timeout: int = 45) -> str:
    return requests.get(url, headers=HEADERS, timeout=timeout).text


def page_count(base: str) -> tuple[int, list[str]]:
    index = get(f"{base}/sitemap.xml")
    maps = re.findall(r"<loc>(.*?)</loc>", index)
    page_maps = [m for m in maps if "sitemap_page" in m]
    total, urls = 0, []
    for url in page_maps:
        text = get(url)
        locs = [loc for loc in re.findall(r"<loc>(.*?)</loc>", text)]
        total += len(locs)
        urls.extend(locs)
    return total, urls


def namespaces(urls: list[str], base: str) -> collections.Counter:
    counter = collections.Counter()
    for loc in urls:
        path = loc.replace(base + "/", "").split("#")[0]
        ns = path.split(":")[0] if ":" in path else "(no-namespace)"
        counter[ns] += 1
    return counter


def main() -> int:
    for base in SITES:
        print("=" * 70)
        print(f"{base}")
        try:
            total, urls = page_count(base)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")
            continue

        print(f"  total pages: {total}")
        counter = namespaces(urls, base)
        print(f"  namespaces: {len(counter)}")
        for ns, count in counter.most_common(28):
            print(f"    {ns:<26}{count:>6}")
        time.sleep(1.5)

    print("\n=== Spot check: does dnd2024 carry 2024 text? ===")
    for path in ["spell:fireball", "wizard", "main:home"]:
        try:
            text = get(f"https://dnd2024.wikidot.com/{path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {path}: ERROR {exc}")
            continue
        content = text[text.find('<div id="page-content">'):][:8000]
        plain = re.sub(r"<[^>]+>", " ", content)
        hits2024 = plain.count("2024")
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        print(f"  {path}: 200, '2024' in body={hits2024}, title={title.group(1).strip()[:50] if title else '?'}")
        time.sleep(1.2)

    return 0


if __name__ == "__main__":
    sys.exit(main())