#!/usr/bin/env python
"""Importer CLI.

    python -m importer.cli plan            # discovery only, no database
    python -m importer.cli dry-run         # fetch + parse, no database
    python -m importer.cli import          # writes to the database
    python -m importer.cli list-excluded

`plan` and `dry-run` deliberately avoid importing Django, so the pipeline can be
validated before any database exists.
"""
from __future__ import annotations

import argparse
import collections
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "importer"))

from wikidot.converter import Converter  # noqa: E402
from wikidot.discovery import Discovery, sitemap_urls  # noqa: E402
from wikidot.filters import is_excluded, page_type_for  # noqa: E402

log = logging.getLogger("importer")

DEFAULT_BASE = "https://dnd2024.wikidot.com"
MIN_BODY_LENGTH = 120


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def gather_paths(args) -> list[str]:
    if getattr(args, "sitemap", False):
        paths = sitemap_urls(args.base_url)
        print(f"sitemap discovery: {len(paths)} pages")
        return paths

    discovery = Discovery(base_url=args.base_url, delay=args.delay)
    paths = discovery.discover(indexes=args.indexes, use_seeds=not args.no_seeds)
    print(f"index discovery: {len(paths)} pages")
    return paths


def split_scope(paths: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    in_scope, excluded = [], []
    for path in paths:
        skip, reason = is_excluded(path)
        if skip:
            excluded.append((path, reason))
        else:
            in_scope.append(path)
    return in_scope, excluded


def report_scope(in_scope: list[str], excluded: list[tuple[str, str]]) -> None:
    types = collections.Counter(page_type_for(p) for p in in_scope)
    print("\n=== SCOPE ===")
    print(f"Discovered : {len(in_scope) + len(excluded)}")
    print(f"In scope   : {len(in_scope)}")
    print(f"Excluded   : {len(excluded)}")
    print("\nBy page type:")
    for page_type, count in types.most_common():
        print(f"  {page_type:<20}{count:>6}")

    if excluded:
        print("\nExclusion reasons:")
        for reason, count in collections.Counter(r for _, r in excluded).most_common(12):
            print(f"  {count:>5}  {reason}")


def cmd_plan(args) -> int:
    """Discovery only: no page is fetched beyond the index pages."""
    paths = gather_paths(args)
    in_scope, excluded = split_scope(paths)
def cmd_dry_run(args) -> int:
    """Fetch and parse a sample; proves the pipeline without touching the DB."""
    paths = gather_paths(args)
    in_scope, excluded = split_scope(paths)
    report_scope(in_scope, excluded)

    sample = in_scope[: args.sample] if args.sample else in_scope
    print(f"\n=== DRY RUN: parsing {len(sample)} pages ===")

    discovery = Discovery(base_url=args.base_url, delay=args.delay)
    converter = Converter()

    ok, thin, failed = 0, 0, []
    warnings: list[str] = []
    samples: list[str] = []

    for index, path in enumerate(sample, 1):
        html = discovery.fetch(path)
        if not html:
            failed.append(path)
            continue

        converted = converter.convert_page(html, path)
        skip, _reason = is_excluded(path, converted.title)
        if skip:
            continue
        if len(converted.markdown) < MIN_BODY_LENGTH:
            thin += 1
            continue

        ok += 1
        warnings.extend(converted.warnings)
        if len(samples) < args.show:
            samples.append(_describe(path, converted))

        if index % 25 == 0:
            print(f"  ... {index}/{len(sample)} "
                  f"({ok} ok, {thin} thin, {len(failed)} failed)")

    print("\n=== RESULT ===")
    print(f"Parsed OK     : {ok}")
    print(f"Thin (skipped): {thin}")
    print(f"Fetch failed  : {len(failed)}")
    print(f"Warnings      : {len(warnings)}")
    if failed:
        print(f"  failures: {failed[:10]}")
    for sample_text in samples:
        print(sample_text)
    return 0


def _describe(path: str, converted) -> str:
    return (
        f"\n--- {path}\n"
        f"  title     : {converted.title}\n"
        f"  type      : {converted.page_type} -> /{converted.category_slug}\n"
        f"  subtitle  : {converted.subtitle}\n"
        f"  tags      : {converted.tags[:6]}\n"
        f"  links     : {len(converted.links)}\n"
        f"  structured: {json.dumps(converted.structured_data, ensure_ascii=False)[:240]}\n"
        f"  markdown ({len(converted.markdown)} chars):\n"
        + "\n".join(f"    {line}" for line in converted.markdown.splitlines()[:20])
    )


def cmd_list_excluded(args) -> int:
    samples = [
        "creature:adult-red-dragon", "monster:goblin", "stat:commoner",
        "appendix:zombies", "bestiary:dragon", "spell:fireball",
        "wizard", "wizard:main", "wizard:evocation", "feat:alert",
        "magic-item:bag-of-holding", "species:elf", "background:acolyte",
        "system:recent-changes", "help:templates", "forum:start",
    ]
    for path in samples:
        excluded, reason = is_excluded(path, path.split(":")[-1].replace("-", " "))
        print(f"{'EXCLUDED' if excluded else 'IMPORTED':<9} {path:<32} "
              f"{page_type_for(path):<14} {reason}")
    return 0


def _add_common(parser) -> None:
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--indexes", nargs="*", default=None)
    parser.add_argument("--no-seeds", action="store_true")
    parser.add_argument("--sitemap", action="store_true")
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--show", type=int, default=3)
    parser.add_argument("--save")
    parser.add_argument("--verbose", action="store_true")


def main() -> int:
    parser = argparse.ArgumentParser(description="Wikidot importer")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Discovery only, no page fetching")
    _add_common(plan)
    plan.set_defaults(func=cmd_plan)

    dry = sub.add_parser("dry-run", help="Fetch + parse a sample, no database")
    _add_common(dry)
    dry.set_defaults(func=cmd_dry_run)

    exc = sub.add_parser("list-excluded", help="Preview the exclusion filters")
    exc.set_defaults(func=cmd_list_excluded)

    args = parser.parse_args()
    configure_logging(getattr(args, "verbose", False))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())