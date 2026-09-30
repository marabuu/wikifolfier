"""Wikidot constructs that must never be imported.

This is an explicit, code-level filter — not a manual deletion step.
Monsters, creatures and stat blocks are out of scope for this compendium.
"""
from __future__ import annotations

import re

# Namespace / category prefixes that are out of scope.
EXCLUDED_PREFIXES = {
    "creature",
    "creatures",
    "monster",
    "monsters",
    "npcstatblock",
    "statblock",
    "srdmonster",
    "bestiary",
    "appendixmonster",
}

# Individual page titles that look like creatures.
EXCLUDED_TITLE_PATTERNS = [
    re.compile(r"^statblock\b", re.IGNORECASE),
    re.compile(r"\bstat\s*block\b", re.IGNORECASE),
    re.compile(r"^appendix\s+[a-z]?\s*:\s*", re.IGNORECASE),
    re.compile(r"\(monster\)\s*$", re.IGNORECASE),
    re.compile(r"\b(?:creature|monster)\s+type\b", re.IGNORECASE),
]

# Page types we explicitly refuse, whatever the source says.
EXCLUDED_PAGE_TYPES = {"monster", "creature", "stat_block"}

# Allowed namespaces -> our page types. Anything else is skipped.
NAMESPACE_TO_PAGE_TYPE = {
    "class": "class",
    "subclass": "subclass",
    "species": "species",
    "background": "background",
    "feat": "feat",
    "racialfeat": "feat",
    "spell": "spell",
    "item": "magic_item",
    "magicitem": "magic_item",
    "equipment": "equipment",
    "weapon": "weapon",
    "armor": "armor",
    "adventuringgear": "adventuring_gear",
    "rule": "rule",
    "condition": "condition",
    "mechanic": "rule",
    "action": "rule",
}


def is_excluded(path: str, title: str = "") -> tuple[bool, str]:
    """Return (excluded, reason). Exclusion is deterministic and code-driven."""
    namespace = (path.split(":")[0] if ":" in path else "").lower().strip()
    if namespace in EXCLUDED_PREFIXES:
        return True, f"excluded namespace '{namespace}'"

    if namespace and namespace not in NAMESPACE_TO_PAGE_TYPE and ":" in path:
        # Unknown namespace: keep only if the title clearly maps to a category
        # we care about. Otherwise skip to avoid importing monsters by accident.
        if not _looks_like_in_scope(title):
            return True, f"unknown namespace '{namespace}' outside compendium scope"

    for pattern in EXCLUDED_TITLE_PATTERNS:
        if pattern.search(title or ""):
            return True, f"title matched exclusion pattern '{pattern.pattern}'"

    return False, ""


def _looks_like_in_scope(title: str) -> bool:
    """Very small allowlist for namespace-less Wikidot pages we want."""
    if not title:
        return False
    scope_words = (
        "condition", "combat", "movement", "rest", "adventuring", "spellcasting",
        "action", "damage", "difficulty", "exhaustion", "inspiration", "advantage",
        "conditions", "rules",
    )
    lowered = title.lower()
    return any(word in lowered for word in scope_words)