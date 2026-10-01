"""Inspect one .docx by path: item titles and the first item's Markdown."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

from docx_reader import parse_docx  # noqa: E402

target = Path(sys.argv[1])
document = parse_docx(target)
print(f"ITENS: {len(document.items)}\n")
for item in document.items:
    print(f"  - {item.title}")
print("\n=== primeiro item ===")
print(document.items[0].markdown[:1200])