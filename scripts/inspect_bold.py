"""Check run-level bold structure of the feats / fighting styles docs."""
from pathlib import Path

import docx

ROOT = Path(r"E:\dev\wikifolfier2\conteudo a adicionar\Regras Homebrew")

for name in ["Novos Feats.docx", "Novos fighting styles.docx"]:
    document = docx.Document(str(ROOT / name))
    print("=" * 68)
    print(name)
    for paragraph in document.paragraphs[:22]:
        text = paragraph.text.strip()
        if not text:
            continue
        runs = [(r.text[:22], bool(r.bold)) for r in paragraph.runs if r.text.strip()]
        print(f"  {text[:56]!r}")
        print(f"      runs: {runs}")
