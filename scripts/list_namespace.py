"""List every discovered path in a given namespace (including excluded ones)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "importer"))

from wikidot.discovery import Discovery
from wikidot.filters import is_excluded, page_type_for
from wikidot.extract import extract_title

namespace = sys.argv[1] if len(sys.argv) > 1 else "ua"

discovery = Discovery(base_url="https://dnd2024.wikidot.com", delay=0.4)
paths = discovery.discover()

matches = [p for p in paths if p.split(":")[0] == namespace]
print(f"\n{len(matches)} paths in namespace '{namespace}':\n")

for path in matches:
    skip, reason = is_excluded(path)
    html = discovery.fetch(path, delay=0.4)
    title = extract_title(html) if html else "(fetch failed)"
    print(f"  {path:<38} {page_type_for(path):<12} "
          f"{'EXCLUDED' if skip else 'IN SCOPE':<9} {title}")
    if reason:
        print(f"      reason: {reason}")
