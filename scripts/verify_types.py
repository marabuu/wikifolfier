"""Focused dry-run: verify spells, feats, items and classes parse correctly."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "importer"))

from wikidot.converter import Converter
from wikidot.discovery import Discovery

TARGETS = [
    "spell:fireball", "spell:eldritch-blast", "feat:alert",
    "magic-item:bag-of-holding", "wizard:main", "artificer:alchemist",
    "species:elf", "background:acolyte",
]


def main() -> int:
    discovery = Discovery(base_url="https://dnd2024.wikidot.com", delay=1.0)
    converter = Converter()

    for path in TARGETS:
        html = discovery.fetch(path)
        if not html:
            print(f"!! {path}: FETCH FAILED")
            continue
        c = converter.convert_page(html, path)
        print("=" * 72)
        print(f"{path}")
        print(f"  title      : {c.title}")
        print(f"  page_type  : {c.page_type}  -> /{c.category_slug}")
        print(f"  subtitle   : {c.subtitle[:70]}")
        print(f"  tags       : {c.tags[:5]}")
        print(f"  structured : {json.dumps(c.structured_data, ensure_ascii=False)[:300]}")
        print(f"  markdown   : {len(c.markdown)} chars, {len(c.links)} links")
        print("  " + "-" * 68)
        for line in c.markdown.splitlines()[:14]:
            print(f"  | {line[:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())