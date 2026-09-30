"""Small HTTP client for the Wikidot public pages.

Politeness rules:
- sequential requests with a delay;
- descriptive User-Agent;
- simple retry with backoff.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

log = logging.getLogger("importer.client")

DEFAULT_BASE_URL = "https://dnd5e.wikidot.com"
USER_AGENT = "dnd-compendium-importer/1.0 (personal campaign compendium)"


@dataclass
class FetchResult:
    url: str
    status: int
    text: str
    ok: bool


class WikidotClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        delay: float = 1.0,
        timeout: int = 30,
        retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def absolute(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def fetch(self, path: str) -> FetchResult:
        url = self.absolute(path)
        last_status = 0
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                last_status = response.status_code
                if response.ok:
                    time.sleep(self.delay)
                    return FetchResult(url, response.status_code, response.text, True)
                log.warning("HTTP %s for %s (attempt %s)", response.status_code, url, attempt)
            except requests.RequestException as exc:
                log.warning("Request error for %s: %s (attempt %s)", url, exc, attempt)
            time.sleep(self.delay * attempt)

        log.error("Giving up on %s after %s attempts", url, self.retries)
        return FetchResult(url, last_status, "", False)