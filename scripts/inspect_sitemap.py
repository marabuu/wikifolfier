"""Inspect the Wikidot sitemap to understand scope before a full import."""
import re
import sys
import collections

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}


def main() -> int:
    index = requests.get(f"{BASE}/sitemap.xml", headers=HEADERS, timeout=30).text
    maps = re.findall(r"<loc>(.*?)</loc>", index)
    print(f"Sub-sitemaps: {len(maps)}")
    page_maps = [m for m in maps if "sitemap_page" in m]
    print(f"Page sitemaps: {page_maps}")

    total = 0
    namespaces = collections.Counter()
    samples = collections.defaultdict(list)

    for url in page_maps:
        text = requests.get(url, headers=HEADERS, timeout=60).text
        locs = re.findall(r"<loc>(.*?)</loc>", text)
        total += len(locs)
        print(f"  {url} -> {len(locs)} urls")
        for loc in locs:
            path = loc.replace(BASE + "/", "").split("#")[0]
            ns = path.split(":")[0] if ":" in path else "(no-namespace)"
            namespaces[ns] += 1
            if len(samples[ns]) < 3:
                samples[ns].append(path)

    print(f"\nTOTAL PAGES DISCOVERABLE: {total}\n")
    print(f"{'NAMESPACE':<28}{'COUNT':>7}")
    print("-" * 35)
    for ns, count in namespaces.most_common(60):
        print(f"{ns:<28}{count:>7}   e.g. {', '.join(samples[ns][:2])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())