"""Debug the class section split for one document."""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importer"))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "wiki" / "management" / "commands"))
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")

import django

django.setup()

from docx_reader import parse_docx  # noqa: E402
from import_folfier_docx import (  # noqa: E402
    CLASS_SUBCLASS_SECTIONS,
    normalize_class_markdown,
    split_named_sections,
    split_spell_list,
)

name = sys.argv[1] if len(sys.argv) > 1 else "Classe - Filho da Magia.docx"
path = Path(r"E:\dev\wikifolfier2\conteudo a adicionar\classes") / name

document = parse_docx(path)
markdown = document.items[0].markdown
print(f"original: {len(markdown)} chars")

markdown, subtitle = normalize_class_markdown(markdown)
print(f"normalized: {len(markdown)} chars | subtitle={subtitle[:60]!r}")

wanted = CLASS_SUBCLASS_SECTIONS.get(path.stem.strip().lower())
print(f"wanted = {wanted}")

headings = re.findall(r"^(#{2,4})\s*(.+?)\s*$", markdown, re.MULTILINE)
print("headings:")
for level, title in headings[:30]:
    print(f"   {level} {title[:70]}")

remaining, extracted = split_named_sections(markdown, wanted or [])
print(f"\nextracted: {len(extracted)}")
for title, _ in extracted:
    print(f"   - {title}")

# The command runs split_spell_list BEFORE the subclass split.
before = len(markdown)
markdown2, spell_list = split_spell_list(markdown)
print(f"\nsplit_spell_list: {before} -> {len(markdown2)} chars, "
      f"spell_list={len(spell_list)} chars")
_, extracted2 = split_named_sections(markdown2, wanted or [])
print(f"subclasses after split_spell_list: {len(extracted2)}")
for title, _ in extracted2:
    print(f"   - {title}")