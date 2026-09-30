#!/usr/bin/env python
"""Importer CLI.

    python -m importer.cli import --seeds spell:fireball class:wizard
    python -m importer.cli report
    python -m importer.cli list-excluded

Idempotent by design: running twice updates instead of duplicating.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")

import django  # noqa: E402

django.setup()

from wikidot.assets import AssetStore  # noqa: E402
from wikidot.client import WikidotClient  # noqa: E402
from wikidot.converter import Converter  # noqa: E402
from wikidot.crawler import Crawler  # noqa: E402
from wikidot.filters import is_excluded  # noqa: E402
from wiki.models import BrokenLink, Category, ImportRun, Page, Source  # noqa: E402
from wiki.services import save_page_with_derived_data  # noqa: E402

log = logging.getLogger("importer")

DEFAULT_SEEDS = [
    "class:wizard",
    "class:cleric",
    "class:fighter",
    "class:rogue",
    "spell:fireball",
    "spell:magic-missile",
    "feat:alert",
    "item:bag-of-holding",
]

MIN_BODY_LENGTH = 200


class Importer:
    def __init__(self, base_url: str, delay: float, download_assets: bool):
        self.client = WikidotClient(base_url=base_url, delay=delay)
        self.crawler = Crawler(self.client)
        self.converter = Converter()
        self.assets = AssetStore(self.client.session) if download_assets else None
        self.report = {
            "pages_discovered": 0,
            "pages_in_scope": 0,
            "pages_excluded": 0,
            "pages_imported": 0,
            "pages_updated": 0,
            "assets_downloaded": 0,
            "broken_links": 0,
            "unknown_constructs": 0,
            "warnings": [],
            "excluded_examples": [],
        }

    def run(self, seeds: list[str], max_pages: int) -> ImportRun:
        from django.utils import timezone

        record = ImportRun.objects.create()
        discovered = self.crawler.discover_from_seeds(seeds)
        self.report["pages_discovered"] = len(discovered)

        in_scope = [page for page in discovered if page.in_scope][:max_pages]
        excluded = [page for page in discovered if not page.in_scope]
        self.report["pages_in_scope"] = len(in_scope)
        self.report["pages_excluded"] = len(excluded)
        self.report["excluded_examples"] = [
            {"path": page.path, "reason": page.reason} for page in excluded[:50]
        ]

        for entry in in_scope:
            self._import_page(entry.path, entry.title)

        if self.assets:
            self.report["assets_downloaded"] = self.assets.downloaded
        self.report["broken_links"] = BrokenLink.objects.count()

        record.finished_at = timezone.now()
        record.pages_discovered = self.report["pages_discovered"]
        record.pages_in_scope = self.report["pages_in_scope"]
        record.pages_excluded = self.report["pages_excluded"]
        record.pages_imported = self.report["pages_imported"]
        record.pages_updated = self.report["pages_updated"]
        record.assets_downloaded = self.report["assets_downloaded"]
        record.broken_links = self.report["broken_links"]
        record.unknown_constructs = self.report["unknown_constructs"]
        record.warnings = len(self.report["warnings"])
        record.report = self.report
        record.save()
        return record
def _import_page(self, path: str, fallback_title: str) -> None:
        result = self.client.fetch(f"/{path}")
        if not result.ok:
            self.report["warnings"].append(f"fetch failed: {path}")
            return

        converted = self.converter.convert(path, result.text, fallback_title)

        # Safety net: never import a creature page, even if a filter was missed.
        excluded, _reason = is_excluded(path, converted.title)
        if excluded:
            self.report["pages_excluded"] += 1
            return

        if len(converted.markdown) < MIN_BODY_LENGTH:
            log.info("Skipping thin page %s (%s chars)", path, len(converted.markdown))
            self.report["warnings"].append(f"thin page skipped: {path}")
            return

        markdown = converted.markdown
        if self.assets:
            markdown = self.assets.localize_markdown(markdown)

        existing = Page.objects.filter(slug=converted.slug).first()
        created = existing is None
        page = existing or Page(slug=converted.slug, title=converted.title)

        page.title = converted.title
        page.subtitle = converted.subtitle
        page.page_type = converted.page_type
        page.source = Source.WIKIDOT
        page.category = Category.objects.filter(slug=converted.category_slug).first()
        page.source_content = markdown
        page.structured_data = converted.structured_data
        page.visibility = "public"

        save_page_with_derived_data(page, converted.tags or None)

        if created:
            self.report["pages_imported"] += 1
        else:
            self.report["pages_updated"] += 1

        for warning in converted.warnings:
            self.report["unknown_constructs"] += 1
            self.report["warnings"].append(f"{path}: {warning}")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def cmd_import(args) -> int:
    configure_logging(args.verbose)
    importer = Importer(args.base_url, args.delay, not args.no_assets)
    seeds = args.seeds or DEFAULT_SEEDS
    record = importer.run(seeds, args.max_pages)

    print("\n=== Import Report ===")
    for key in (
        "pages_discovered", "pages_in_scope", "pages_excluded",
        "pages_imported", "pages_updated", "assets_downloaded",
        "broken_links", "unknown_constructs",
    ):
        print(f"{key.replace('_', ' ').title()}: {importer.report[key]}")
    print(f"Warnings: {len(importer.report['warnings'])}")

    output = Path(args.report_path)
    output.write_text(
        json.dumps(importer.report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nReport written to {output} (ImportRun #{record.pk})")
    return 0


def cmd_report(args) -> int:
    latest = ImportRun.objects.first()
    if not latest:
        print("No import runs yet.")
        return 1
    print(json.dumps(latest.report, indent=2, ensure_ascii=False))
    return 0


def cmd_list_excluded(args) -> int:
    """Show which page paths the filters reject."""
    samples = [
        "creature:adult-red-dragon", "monster:goblin", "stat:commoner",
        "appendix:zombies", "spell:fireball", "class:wizard",
        "feat:alert", "item:bag-of-holding", "my-homebrew-page",
    ]
    for path in samples:
        excluded, reason = is_excluded(path, path.split(":")[-1].replace("-", " "))
        mark = "EXCLUDED" if excluded else "IMPORTED"
        print(f"{mark:9} {path:35} {reason}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Wikidot importer")
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", help="Discover, parse and import pages")
    imp.add_argument("--seeds", nargs="*", help="Seed page paths (e.g. spell:fireball)")
    imp.add_argument(
        "--base-url",
        default=os.environ.get("WIKIDOT_BASE_URL", "https://dnd5e.wikidot.com"),
    )
    imp.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    imp.add_argument("--max-pages", type=int, default=100000)
    imp.add_argument("--no-assets", action="store_true", help="Skip image download")
    imp.add_argument("--report-path", default="import_report.json")
    imp.add_argument("--verbose", action="store_true")
    imp.set_defaults(func=cmd_import)

    rep = sub.add_parser("report", help="Show the last import report")
    rep.set_defaults(func=cmd_report)

    exc = sub.add_parser("list-excluded", help="Preview the exclusion filters")
    exc.set_defaults(func=cmd_list_excluded)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())