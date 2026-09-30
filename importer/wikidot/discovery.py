"""Page discovery for the 2024 wiki.

dnd2024.wikidot.com has no usable sitemap (it returns HTTP 503), so we discover
pages by reading its own index pages, which are authoritative and complete:

    spell              -> all spells
    feat:all           -> all feats
    background:all     -> all backgrounds
    species:all        -> all species
    magic-item:all     -> all magic items
    class:all          -> all classes
    equipment:all      -> equipment sub-indexes

Each class page additionally links its subclasses, so classes and subclasses are
covered too.
"""
from __future__ import annotations

import logging
import re
import time

import requests

log = logging.getLogger("importer.discovery")

USER_AGENT = "dnd-compendium-importer/1.0 (personal campaign compendium)"

BASE_2024 = "https://dnd2024.wikidot.com"
BASE_2014 = "https://dnd5e.wikidot.com"

# Index pages that enumerate the compendium.
INDEX_PAGES = [
    "spell",
    "feat:all",
    "background:all",
    "species:all",
    "magic-item:all",
    "class:all",
    "equipment:all",
]

# Pages worth following one level deep to pick up subclasses and sub-indexes.
SEEDS = [
    "artificer:main", "barbarian:main", "bard:main", "cleric:main",
    "druid:main", "fighter:main", "monk:main", "paladin:main",
    "ranger:main", "rogue:main", "sorcerer:main", "warlock:main",
    "wizard:main",
]

LINK_RE = re.compile(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)(?:#|")', re.IGNORECASE)


class Discovery:
    def __init__(self, base_url: str = BASE_2024, delay: float = 1.0, session=None):
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self, path: str) -> str:
        try:
            response = self.session.get(f"{self.base_url}/{path}", timeout=30)
        except requests.RequestException as exc:
            log.warning("fetch failed %s: %s", path, exc)
            return ""
        time.sleep(self.delay)
        if not response.ok:
            log.warning("fetch %s -> HTTP %s", path, response.status_code)
            return ""
        return response.text

    def links_from(self, path: str) -> set[str]:
        html = self.fetch(path)
        start = html.find('<div id="page-content">')
        if start == -1:
            return set()
        # Only the article region, so nav/footer links don't pollute results.
        body = html[start:start + 400000]
        return set(LINK_RE.findall(body))

    def discover(self, indexes=None, seeds=None, use_seeds: bool = True) -> list[str]:
        """Return the sorted set of page paths to import."""
        found: set[str] = set()

        for index in indexes or INDEX_PAGES:
            links = self.links_from(index)
            log.info("index %s -> %d links", index, len(links))
            found |= links

        if use_seeds:
            for seed in seeds or SEEDS:
                links = self.links_from(seed)
                log.info("seed %s -> %d links", seed, len(links))
                found |= links

        return sorted(found)


def sitemap_urls(base_url: str) -> list[str]:
    """Sitemap-based discovery (works on the 2014 wiki, returns [] on the 2024)."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    try:
        index = session.get(f"{base_url}/sitemap.xml", timeout=30).text
    except requests.RequestException:
        return []

    maps = re.findall(r"<loc>(.*?)</loc>", index)
    page_maps = [m for m in maps if "sitemap_page" in m]
    if not page_maps:
        return []

    urls: list[str] = []
    for url in page_maps:
        try:
            text = session.get(url, timeout=60).text
        except requests.RequestException:
            continue
        urls.extend(
            loc.replace(base_url.rstrip("/") + "/", "").split("#")[0]
            for loc in re.findall(r"<loc>(.*?)</loc>", text)
        )
    return sorted(set(urls))