"""Syntax-check every Python file in the repository."""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
failures = 0
checked = 0
for path in sorted(ROOT.rglob("*.py")):
    if any(part in {".venv", "node_modules", "__pycache__"} for part in path.parts):
        continue
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        checked += 1
    except SyntaxError as exc:
        failures += 1
        print(f"SYNTAX ERROR {path}:{exc.lineno}: {exc.msg}")
print(f"checked={checked} failures={failures}")
sys.exit(1 if failures else 0)