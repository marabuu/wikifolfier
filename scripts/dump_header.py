"""Dump the raw header HTML of a 2024 page to tune structured extraction."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importer"))

from wikidot.extract import extract_article
from wikidot.discovery import Discovery


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "spell:fireball"
    discovery = Discovery(base_url="https://dnd2024.wikidot.com", delay=0.8)
    article = extract_article(discovery.fetch(path))
    head = article[:1400]
    print(f"### {path} article head ({len(article)} chars total)\n")
    print(head)
    return 0


if __name__ == "__main__":
    sys.exit(main())