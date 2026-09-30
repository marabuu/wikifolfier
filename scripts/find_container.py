"""Locate the real content container and show the raw article HTML."""
import re
import sys

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}

CANDIDATES = [
    '<div id="page-content"',
    '<div id="wiki-content"',
    '<div class="page-content"',
    'id="page-content"',
    "page-show-content",
    'id="main-content"',
    'class="content"',
]


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "spell:fireball"
    text = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30).text

    print(f"### {path}\n")
    for candidate in CANDIDATES:
        print(f"  {candidate!r}: {text.count(candidate)} occurrences")

    # Show every div that carries an id, with a short preview of its content.
    print("\n--- divs with id (preview) ---")
    for match in re.finditer(r'<div[^>]*\bid="([^"]+)"[^>]*>', text):
        div_id = match.group(1)
        start = match.end()
        preview = re.sub(r"\s+", " ", text[start:start + 220])
        print(f"\n[{div_id}]\n   {preview}")

    print("\n--- module- / collapse markers ---")
    for marker in ["module-suppressed", 'data-module', "module-content", "page-tags", "page-source"]:
        print(f"  {marker}: {text.count(marker)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())