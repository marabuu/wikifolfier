"""Page discovery.

Two strategies:
- seed pages provided by the user (explicit list);
- sitemap-based discovery restricted to in-scope namespaces.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .client import WikidotClient
from .filters import NAMESPACE_TO_PAGE_TYPE, is_excluded

log = logging.getLogger("importer.crawler")

HREF_RE = re.compile(r'href="/([^"#:]+:[^"#]+)"')


@dataclass
class DiscoveredPage:
    path: str  # e.g. "spell:fireball"
    title: str
    in_scope: bool
    reason: str = ""


class Crawler:
    def __init__(self, client: WikidotClient):
        self.client = client

    def discover_from_seeds(self, seeds: list[str]) -> list[DiscoveredPage]:
        found: dict[str, DiscoveredPage] = {}
        queue = list(seeds)
        seen: set[str] = set()

        while queue:
            path = queue.pop(0)
            if path in seen:
                continue
            seen.add(path)

            page = self.inspect(path)
            if page is None:
                continue
            found[path] = page
            if page.in_scope:
                queue.extend(self._links_from(path))

        return list(found.values())

    def _links_from(self, path: str) -> list[str]:
        result = self.client.fetch(f"/{path}")
        if not result.ok:
            return []
        return sorted(set(HREF_RE.findall(result.text)))

    def inspect(self, path: str) -> DiscoveredPage | None:
        result = self.client.fetch(f"/{path}")
        if not result.ok:
            return None

        title = self._title_from(result.text) or path.split(":")[-1].replace("_", " ")
        excluded, reason = is_excluded(path, title)
        return DiscoveredPage(path=path, title=title, in_scope=not excluded, reason=reason)

    @staticmethod
    def _title_from(html: str) -> str:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if not match:
            match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def page_type_for(path: str) -> str:
    namespace = path.split(":")[0].lower() if ":" in path else ""
    return NAMESPACE_TO_PAGE_TYPE.get(namespace, "other")