"""Download and rewrite remote assets so the compendium works offline."""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import requests

log = logging.getLogger("importer.assets")

DEFAULT_MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/media"))
EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


class AssetStore:
    def __init__(self, client: requests.Session, root: Path = DEFAULT_MEDIA_ROOT):
        self.client = client
        self.root = Path(root) / "wikidot"
        self.root.mkdir(parents=True, exist_ok=True)
        self.downloaded = 0
        self.failed: list[str] = []

    def local_path(self, url: str) -> Path | None:
        name = url.rsplit("/", 1)[-1].split("?")[0]
        suffix = Path(name).suffix.lower()
        if suffix not in EXTENSIONS:
            return None
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        return self.root / f"{digest}-{Path(name).stem}{suffix}"

    def fetch(self, url: str) -> str | None:
        """Download an asset once; return its local relative path."""
        if not url.startswith("http"):
            return url

        target = self.local_path(url)
        if target is None:
            return url

        if target.exists():
            return f"/media/wikidot/{target.name}"

        try:
            response = self.client.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            log.warning("Asset download failed: %s (%s)", url, exc)
            self.failed.append(url)
            return url

        target.write_bytes(response.content)
        self.downloaded += 1
        log.info("Asset saved: %s", target.name)
        return f"/media/wikidot/{target.name}"

    def localize_markdown(self, markdown: str) -> str:
        """Rewrite remote image URLs to local paths, in place."""
        import re

        def repl(match: re.Match) -> str:
            url = match.group(2)
            return f"{match.group(1)}{self.fetch(url)}{match.group(3)}"

        return re.sub(r"(!\[[^\]]*\]\()([^)\s]+)(\))", repl, markdown)