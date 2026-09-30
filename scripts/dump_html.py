"""Dump the real HTML skeleton of a page so the parser can target it."""
import re
import sys

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "spell:fireball"
    text = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30).text

    print(f"### {path}: {len(text)} bytes\n")

    # Every div id present, in document order.
    print("--- div ids ---")
    for match in re.finditer(r'<div[^>]*id="([^"]+)"', text):
        print(f"  {match.group(1)}")

    print("\n--- div classes (unique, top 40) ---")
    classes = {}
    for match in re.finditer(r'<div[^>]*class="([^"]+)"', text):
        for cls in match.group(1).split():
            classes[cls] = classes.get(cls, 0) + 1
    for cls, count in sorted(classes.items(), key=lambda kv: -kv[1])[:40]:
        print(f"  {cls}: {count}")

    print("\n--- 2024 / 5e context ---")
    for marker in ["2024", "5e", "SRD"]:
        for match in list(re.finditer(marker, text))[:4]:
            start = max(0, match.start() - 90)
            print(f"  [{marker}] ...{re.sub(chr(60), '<', text[start:match.end()+90])}...")

    print("\n--- page-title block ---")
    title_block = re.search(r'<div id="page-title".*?(?=<div id="page-info"|</body>)', text, re.S)
    if title_block:
        print(re.sub(r"\s+", " ", title_block.group(0))[:1500])

    print("\n--- page-info block ---")
    info_block = re.search(r'<div id="page-info".*?(?=<div id="page-content|<div id="footer")', text, re.S)
    if info_block:
        print(re.sub(r"\s+", " ", info_block.group(0))[:2000])

    return 0


if __name__ == "__main__":
    sys.exit(main())