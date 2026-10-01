"""Find where each Folfier class document keeps its spell list."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importer"))

from docx_reader import parse_docx  # noqa: E402

CORPUS = Path(r"E:\dev\wikifolfier2\conteudo a adicionar")

MARKERS = re.compile(
    r"(lista\s+de\s+magias|magia[s]?\s+(?:da|do)\s+classe|spell\s*list|"
    r"magias\s+dispon[ií]veis|slots?\s+de\s+magia|spell\s+slots?)",
    re.IGNORECASE,
)

for path in sorted(CORPUS.rglob("*.docx")):
    if path.parent.name.lower() != "classes":
        continue
    document = parse_docx(path)
    if not document.items:
        continue
    markdown = document.items[0].markdown
    hits = MARKERS.findall(markdown)
    tables = markdown.count("| --- |")
    print(f"{path.name}")
    print(f"   {len(markdown)} chars | tabelas={tables} | marcadores={len(hits)}")
    for match in MARKERS.finditer(markdown):
        line_start = markdown.rfind("\n", 0, match.start()) + 1
        line_end = markdown.find("\n", match.end())
        print(f"      -> {markdown[line_start:line_end][:90]!r}")
        break
    if not hits:
        print("      (nenhum marcador de lista de magias)")