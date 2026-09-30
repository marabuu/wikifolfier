"""Wikidot modules.

A module is a Wikidot component whose content lives in `data-options`
(JSON or wikitext). We map the ones we understand and report the rest.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable

log = logging.getLogger("importer.modules")


@dataclass
class ModuleResult:
    name: str
    markdown: str
    data: dict = field(default_factory=dict)
    understood: bool = True


def _json_options(options: str) -> dict:
    try:
        return json.loads(options)
    except (ValueError, TypeError):
        return {}


def spell_module(options: str) -> ModuleResult:
    """Spell stat block: casting time / range / components / duration / classes."""
    data = _json_options(options)
    fields = [
        ("Casting Time", data.get("castingtime")),
        ("Range", data.get("range")),
        ("Components", data.get("components")),
        ("Duration", data.get("duration")),
    ]
    lines = [f"**{label}:** {value}" for label, value in fields if value]
    classes = data.get("classes") or []
    if classes:
        lines.append("**Classes:** " + ", ".join(classes))
    return ModuleResult("spell", "\n".join(lines) + "\n", data)


def info_module(options: str) -> ModuleResult:
    """Generic titled info box."""
    data = _json_options(options)
    title = data.get("title", "Info")
    body = data.get("text") or data.get("content") or ""
    return ModuleResult("info", f"**{title}**\n\n{body}\n", data)


def featured_module(options: str) -> ModuleResult:
    data = _json_options(options)
    title = data.get("title", "Featured content")
    body = data.get("content") or data.get("text") or ""
    return ModuleResult("featured", f"**{title}**\n\n{body}\n", data)


def footnote_module(options: str) -> ModuleResult:
    data = _json_options(options)
    notes = data.get("notes") or data.get("text") or ""
    return ModuleResult("footnote", f"> {notes}\n", data)


def unknown_module(options: str, body: str = "") -> ModuleResult:
    log.warning("WARNING: unsupported Wikidot construct -> %s", options[:200])
    return ModuleResult("unknown", body, {}, understood=False)


MODULE_HANDLERS: dict[str, Callable[[str], ModuleResult]] = {
    "spell": spell_module,
    "spellmini": spell_module,
    "infobox": info_module,
    "info": info_module,
    "featured": featured_module,
    "footnote": footnote_module,
}


def handle_module(class_name: str, options: str, body: str = "") -> ModuleResult:
    for key, handler in MODULE_HANDLERS.items():
        if key in class_name.lower():
            return handler(options)
    return unknown_module(options, body)