"""Locate the sub-entry sections the GM named, inside the new class documents."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importer"))

from docx_reader import parse_docx  # noqa: E402

CORPUS = Path(r"E:\dev\wikifolfier2\conteudo a adicionar\classes")

# What the GM said each class uses as its "subclasses".
NEEDLES = {
    "Classe - Herói": ["heroic", "destino", "destination"],
    "Classe - Runescaper": ["livro", "book"],
    "Classe - Filho da Magia": ["progenitora", "progenitor"],
    "Classe - Witcher": ["escola"],
    "Classe - Dovahkiin": [],
}

for name, needles in NEEDLES.items():
    path = CORPUS / f"{name}.docx"
    if not path.exists():
        print(f"!! {name}: arquivo nao encontrado")
        continue
    document = parse_docx(path)
    markdown = document.items[0].markdown if document.items else ""
    headings = re.findall(r"^#{2,4}\s*(.+)$", markdown, re.MULTILINE)

    print("=" * 72)
    print(f"{name}  ({len(markdown)} chars, {len(headings)} headings)")
    if not needles:
        print("  (sem subclasses)")
        continue
    hits = [h for h in headings
            if any(n in h.lower() for n in needles)]
    print(f"  headings que casam {needles}: {len(hits)}")
    for hit in hits[:16]:
        print(f"    - {hit[:74]}")