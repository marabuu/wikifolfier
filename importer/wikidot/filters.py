"""Scope rules for the Wikidot import.

Verified against dnd2024.wikidot.com (the 2024 wiki) and dnd5e.wikidot.com (2014).

Monsters, creatures and stat blocks are OUT OF SCOPE. They have no PageType, no
template and no route; they are rejected here in code, never by hand.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------- monsters
# Namespaces and title markers that identify creature content.
MONSTER_PREFIXES = {
    "creature", "creatures", "monster", "monsters", "bestiary",
    "statblock", "stat", "npcstatblock", "npc-stat", "srdmonster",
    "appendixmonster", "appendix-monster", "encounter", "encounters",
    "monsterlist", "adventure-path", "cult", "cults",
}

MONSTER_TITLE_PATTERNS = [
    re.compile(r"\bstat\s*block\b", re.IGNORECASE),
    re.compile(r"\bstatblock\b", re.IGNORECASE),
    re.compile(r"\(monster\)", re.IGNORECASE),
    re.compile(r"\(creature\)", re.IGNORECASE),
    re.compile(r"^appendix\s+[a-z]?\s*:\s*", re.IGNORECASE),
    re.compile(r"\b(?:creature|monster)\s+type\b", re.IGNORECASE),
    re.compile(
        r"^\s*(?:large|medium|small|tiny|huge|gargantuan)\s+(?:dragon|beast|monster)\b",
        re.IGNORECASE,
    ),
]

# ------------------------------------------------------- in-scope mapping
NAMESPACE_TO_PAGE_TYPE = {
    "spell": "spell",
    "feat": "feat",
    "background": "background",
    "species": "species",
    "lineage": "species",
    "magic-item": "magic_item",
    "magicitem": "magic_item",
    "item": "magic_item",
    "equipment": "equipment",
    "weapon": "weapon",
    "armor": "armor",
    "adventuring-gear": "adventuring_gear",
    "tool": "equipment",
    "vehicle": "equipment",
    "poison": "equipment",
    "siege-equipment": "equipment",
    "rule": "rule",
    "rules": "rule",
    "condition": "condition",
    "mechanic": "rule",
    "action": "rule",
    "variant": "rule",
    "variantrule": "rule",
    "subclass": "subclass",
    # Unearthed Arcana is an official Wizards sourcebook, not user content.
    # Its pages are classes and class options ("ua:class-psion", ...).
    "ua": "class",
    "unearthed-arcana": "class",
    "unearthedarcana": "class",
}

# Class landing pages: bare "<class>" or "<class>:main".
CLASS_NAMES = {
    "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
    "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
}

# Per-class namespaces hold subclass pages on this wiki.
CLASS_SUBCLASS_NAMESPACES = {
    "artificer", "barbarian", "bard", "blood-hunter", "cleric", "discipline",
    "druid", "fighter", "hexblade", "monk", "mystic", "paladin", "ranger",
    "rogue", "sorcerer", "warlock", "wizard", "sidekick",
}

# Site chrome / discussion namespaces: never compendium content.
CHROME_PREFIXES = {
    "system", "help", "legal", "forum", "css", "admincss", "nav", "home",
    "main", "search", "template", "t", "w", "doc", "doc-data-forms",
    "doc-modules", "deleted", "wip", "thread", "category", "template-part",
    "quotes", "forum-category", "forum-thread", "forum-post", "css-theme",
}

EXCLUDED_PAGE_TYPES = {"monster", "creature", "stat_block"}

_WEAPON_HINT = re.compile(
    r"\b(sword|axe|bow|dagger|hammer|mace|spear|staff|wand|weapon|"
    r"armor|shield|mail|plate|leather|helmet|gauntlet|boots)\b"
)


def namespace_of(path: str) -> str:
    return path.split(":")[0].lower().strip() if ":" in path else ""


def page_type_for(path: str) -> str:
    """Map a Wikidot path to our PageType. Defaults to 'other'."""
    ns = namespace_of(path)
    tail = path.split(":")[-1].lower() if ":" in path else path.lower()

    # A bare "<class>" path (no namespace) is the class landing page.
    if not ns:
        return "class" if tail in CLASS_NAMES else "other"

    # A namespaced class path is the class landing page only when it is :main.
    if ns in CLASS_SUBCLASS_NAMESPACES or ns in CLASS_NAMES:
        return "class" if tail in {"main", "_home", ""} else "subclass"
    if ns in NAMESPACE_TO_PAGE_TYPE:
        mapped = NAMESPACE_TO_PAGE_TYPE[ns]
        if ns in {"item", "magicitem", "magic-item"} and _WEAPON_HINT.search(tail):
            return "weapon"
        return mapped
    return "other"


def is_excluded(path: str, title: str = "") -> tuple[bool, str]:
    """Return (excluded, reason). Deterministic, code-driven, no manual step."""
    ns = namespace_of(path)
    title = title or ""

    if ns in MONSTER_PREFIXES:
        return True, f"creature namespace '{ns}'"

    for pattern in MONSTER_TITLE_PATTERNS:
        if pattern.search(title):
            return True, f"creature title pattern '{pattern.pattern}'"

    if ns in CHROME_PREFIXES:
        return True, f"site chrome namespace '{ns}'"

    page_type = page_type_for(path)
    if page_type == "other" and ns and ns not in CLASS_SUBCLASS_NAMESPACES:
        return True, f"namespace '{ns}' is outside the compendium scope"

    return False, ""
