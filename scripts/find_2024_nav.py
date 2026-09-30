"""Find the real navigation/index pages on dnd2024 by reading its sidebar."""
import collections
import re
import sys
import time

import requests

BASE = "https://dnd2024.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}


def session_get(session, path: str) -> str:
    return session.get(f"{BASE}/{path}", timeout=30).text


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    text = session_get(session, "main:home")

    print("--- site-wide nav links (all links on home, deduped) ---")
    nav = collections.Counter(re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)(?:#|")', text))
    for link, count in nav.most_common(60):
        print(f"  {link:<40}{count}")

    print("\n--- link labels (text near href) for 'all'-style index pages ---")
    anchors = re.findall(r'<a[^>]*href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)"[^>]*>([^<]{0,40})</a>', text)
    seen = set()
    for link, label in anchors:
        key = (link, label.strip())
        if key in seen:
            continue
        seen.add(key)
        lowered = label.lower()
        if any(word in lowered for word in ("all", "index", "class", "spell", "item", "feats", "lineage", "background")):
            print(f"  {link:<34} :: {label.strip()}")

    print("\n--- sidebar region ---")
    sidebar = re.search(r'<div class="side-bar".*?</div>\s*</div>', text, re.S)
    if sidebar:
        side_links = re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)"', sidebar.group(0))
        for link in dict.fromkeys(side_links):
            print(f"  {link}")

    print("\n--- probing candidate index pages ---")
    candidates = [
        "spell", "spells", "spells:fireball", "spells:list", "spells:index",
        "class", "class:all", "classes", "equipment", "equipment:all",
        "magic-item", "magic-item:all", "items", "items:all",
        "feat:all", "background:all", "lineage:all", "lineage", "rule:all",
        "races", "main:rules", "main:species",
    ]
    for candidate in candidates:
        try:
            response = session.get(f"{BASE}/{candidate}", timeout=25)
            if response.status_code == 200:
                start = response.text.find('<div id="page-content">')
                content = response.text[start:start + 200000] if start != -1 else ""
                links = set(re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)(?:#|")', content))
                print(f"  {candidate:<22} 200  links={len(links)}  e.g. {sorted(links)[:4]}")
            else:
                print(f"  {candidate:<22} {response.status_code}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {candidate:<22} ERR {exc}")
        time.sleep(0.9)

    return 0


if __name__ == "__main__":
    sys.exit(main())