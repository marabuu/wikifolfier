"""Verify spell header parsing (level, school, classes) on real pages."""
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
    "spell:fireball", "spell:eldritch-blast", "spell:cure-wounds",
    "spell:counterspell", "spell:guiding-bolt", "spell:shillelagh",
]


def main() -> int:
    discovery = Discovery(base_url="https://dnd2024.wikidot.com", delay=0.5)
    converter = Converter()

    for path in TARGETS:
        html = discovery.fetch(path)
        if not html:
            print(f"!! {path}: fetch failed")
            continue
        c = converter.convert_page(html, path)
        sd = c.structured_data
        print(f"{path:<26} level={sd.get('level')!s:<3} school={sd.get('school')!s:<14} "
              f"classes={sd.get('classes')}")

    print("\nValid schools:", sorted(__import__("wikidot.converter", fromlist=["x"]).VALID_SCHOOLS))
    return 0


if __name__ == "__main__":
    sys.exit(main())