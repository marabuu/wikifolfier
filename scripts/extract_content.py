"""Extract the #page-content region and show the real article HTML."""
import html
import re
import sys

import requests

BASE = "https://dnd5e.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}


def extract(text: str) -> str:
    start = text.find('<div id="page-content">')
    if start == -1:
        return ""
    start += len('<div id="page-content">')
    # Page ends at #action-area / #footer.
    for marker in ['<div id="action-area"', '<div id="page-options-bottom-tips"', '<div id="footer"']:
        end = text.find(marker, start)
        if end != -1:
            return text[start:end]
    return text[start:start + 40000]


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "spell:fireball"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    text = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30).text

    content = extract(text)
    print(f"### {path}  extracted={len(content)} bytes\n")
    print(re.sub(r"\n{3,}", "\n\n", content)[:limit])

    print("\n\n=== TAG HISTOGRAM ===")
    tags = {}
    for match in re.finditer(r"<([a-zA-Z][a-zA-Z0-9]*)", content):
        tag = match.group(1).lower()
        tags[tag] = tags.get(tag, 0) + 1
    for tag, count in sorted(tags.items(), key=lambda kv: -kv[1])[:25]:
        print(f"  {tag}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())