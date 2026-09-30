"""Probe for the remaining index pages on dnd2024 (species, rules, equipment)."""
import collections
import re
import sys
import time

import requests

BASE = "https://dnd2024.wikidot.com"
HEADERS = {"User-Agent": "dnd-compendium-importer/1.0 (personal campaign compendium)"}

CANDIDATES = [
    "species", "species:all", "lineages", "lineage", "ancestries",
    "rules", "rule", "rules:all", "conditions", "condition:all",
    "equipment:adventuring-gear", "equipment:armor", "equipment:weapons",
    "equipment:tools", "equipment:mounts", "equipment:crafting",
    "background:all", "feat:all", "spell", "magic-item:all", "class:all",
    "status:all", "condition:blinded", "rules:index",
    "main:rules", "main:lineages", "main:species", "main:index",
]

# Namespaces we care about for the compendium.
IN_SCOPE = re.compile(
    r"^(spell|feat|background|lineage|species|magic-item|equipment|weapon|armor|"
    r"rule|condition|rules|class|ancestry|status|poison|vehicle|tool|"
    r"artificer|barbarian|bard|cleric|druid|fighter|monk|paladin|ranger|rogue|"
    r"sorcerer|warlock|wizard)\b"
)


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)

    found = {}

    for candidate in CANDIDATES:
        try:
            response = session.get(f"{BASE}/{candidate}", timeout=25)
        except Exception as exc:  # noqa: BLE001
            print(f"  {candidate:<28} ERR {exc}")
            continue

        if response.status_code != 200:
            print(f"  {candidate:<28} {response.status_code}")
            time.sleep(0.7)
            continue

        start = response.text.find('<div id="page-content">')
        content = response.text[start:start + 400000] if start != -1 else ""
        links = set(re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)(?:#|")', content))
        in_scope = {l for l in links if IN_SCOPE.match(l)}
        print(f"  {candidate:<28} 200  total_links={len(links):<5} in_scope={len(in_scope):<5} e.g. {sorted(in_scope)[:3]}")
        if in_scope:
            found[candidate] = in_scope
        time.sleep(0.7)

    union = set().union(*found.values()) if found else set()
    print(f"\n=== union of in-scope links across index pages: {len(union)} ===")
    counter = collections.Counter(l.split(":")[0] for l in union)
    for ns, count in counter.most_common(40):
        print(f"  {ns:<24}{count:>6}")

    with open("candidates_2024.txt", "w", encoding="utf-8") as handle:
        for link in sorted(union):
            handle.write(link + "\n")
    print("\nWrote candidates_2024.txt")

    return 0


if __name__ == "__main__":
    sys.exit(main())