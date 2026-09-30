"""Validate the compose files without requiring Docker.

    python scripts/validate_compose.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "docker-compose.yml",
    ROOT / "docker-compose.dev.yml",
    ROOT / "docker-compose.prod.yml",
]

try:
    import yaml
except ImportError:
    print("PyYAML not installed; falling back to a structural check only.")
    yaml = None


def structural_check(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8")
    problems = []

    lines = text.splitlines()
    top_level = [line for line in lines if line and not line.startswith((" ", "#", "\t"))]
    duplicates = {line for line in top_level if top_level.count(line) > 1}
    if duplicates:
        problems.append(f"duplicate top-level keys: {sorted(duplicates)}")

    if "services:" not in text:
        problems.append("missing 'services:' key")

    for tab in [i + 1 for i, line in enumerate(lines) if "\t" in line]:
        problems.append(f"tab character on line {tab} (YAML forbids tabs)")

    if problems:
        print(f"{path.name}: FAIL")
        for problem in problems:
            print(f"  - {problem}")
        return False

    print(f"{path.name}: OK")
    return True


def semantic_check(path: pathlib.Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    services = data.get("services") or {}
    print(f"{path.name}: services = {sorted(services)}")
    for name, spec in services.items():
        if not isinstance(spec, dict):
            print(f"  - service '{name}' is not a mapping")
            return False
    return True


def main() -> int:
    ok = True
    for path in FILES:
        if not path.exists():
            print(f"{path.name}: MISSING")
            ok = False
            continue
        ok = structural_check(path) and ok
        if yaml is not None:
            ok = semantic_check(path) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())