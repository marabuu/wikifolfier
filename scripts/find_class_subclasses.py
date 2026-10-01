"""Find subclass sections inside the new Folfier class documents."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importer"))

from docx_reader import parse_docx  # noqa: E402

CORPUS = Path(r"E:\dev\wikifolfier2\conteudo a adicionar\classes")

# Headings/paragraphs that introduce a subclass or a variant.
SUBCLASS_MARKER = re.compile(
    r"^(?:subclasse|sub[- ]?class|classe\s*:|variante|arquétipo|origem|"
    r"tradi[çc][ãa]o|escola)\b",
    re.IGNORECASE,
)

for path in sorted(CORPUS.glob("*.docx")):
    document = parse_docx(path)
    if not document.items:
        continue
    markdown = document.items[0].markdown
    headings = re.findall(r"^#{2,4}\s*(.+)$", markdown, re.MULTILINE)
    print("=" * 70)
    print(f"{path.name}  ({len(markdown)} chars)")
    print(f"  headings ({len(headings)}):")
    for heading in headings[:14]:
        print(f"    - {heading[:78]}")
    marks = [line for line in markdown.splitlines() if SUBCLASS_MARKER.match(line.strip())]
    if marks:
        print("  marcadores de subclasse:")
        for line in marks[:6]:
            print(f"    > {line.strip()[:78]}")