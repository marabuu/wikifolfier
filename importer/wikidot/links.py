"""Wikidot link resolution.

Wikidot URLs can be:
- full:  https://dnd5e.wikidot.com/spell:fireball
- short: /spell:fireball
- bare:  spell:fireball

All of them normalize to a page path `spell:fireball` and then to our slug.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

WIKIDOT_HOSTS = {"dnd5e.wikidot.com", "www.dnd5e.wikidot.com"}
ANCHOR_RE = re.compile(r"^#")


def normalize_href(href: str, base_url: str = "") -> str | None:
    """Return the Wikidot page path ('spell:fireball') or None if not internal."""
    if not href or ANCHOR_RE.match(href):
        return None

    if href.startswith("//"):
        parsed = urlparse("https:" + href)
    elif href.startswith("http"):
        parsed = urlparse(href)
        if parsed.netloc not in WIKIDOT_HOSTS:
            return None
    else:
        return href.strip("/").split("#")[0] or None

    if base_url:
        base_host = urlparse(base_url).netloc
        if parsed.netloc and base_host and parsed.netloc != base_host:
            return None

    path = parsed.path.strip("/").split("#")[0]
    return path or None


def path_to_slug(path: str) -> str:
    """'spell:fireball' -> 'fireball'."""
    tail = path.split(":")[-1]
    from .converter import slugify

    return slugify(tail.replace("_", "-"))


def resolve(page_path: str, href: str, base_url: str = "") -> str | None:
    normalized = normalize_href(href, base_url)
    if normalized is None:
        return None
    if ":" not in normalized:
        # Same-namespace relative link (e.g. /fireball from spell:fireball).
        namespace = page_path.split(":")[0] if ":" in page_path else ""
        normalized = f"{namespace}:{normalized}" if namespace else normalized
    return path_to_slug(normalized)