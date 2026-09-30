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

# Model field limits (backend/wiki/models.py). Imported content is not
# guaranteed to respect them, so every text field is clamped before writing.
MAX_TITLE = 255
MAX_SUBTITLE = 255
MAX_SLUG = 180


def clamp(text: str, limit: int) -> str:
    return (text or "")[:limit]


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
    report_scope(in_scope, excluded)
    if args.save:
        Path(args.save).write_text("\n".join(in_scope), encoding="utf-8")
        print(f"\nSaved {len(in_scope)} in-scope paths to {args.save}")
    return 0


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


def cmd_import(args) -> int:
    """Fetch, convert and persist pages. Requires the database."""
    from django.utils import timezone

    from wikidot.assets import AssetStore
    from wiki.models import BrokenLink, Category, ImportRun, Page, Source
    from wiki.services import save_page_with_derived_data

    paths = gather_paths(args)
    in_scope, excluded = split_scope(paths)
    report_scope(in_scope, excluded)

    target = in_scope[: args.sample] if args.sample else in_scope
    if getattr(args, "only_file", None):
        wanted = {
            line.strip()
            for line in Path(args.only_file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        target = [path for path in in_scope if path in wanted]
    if args.only:
        wanted = set(args.only)
        target = [path for path in target if path in wanted]

    print(f"\n=== IMPORT: writing {len(target)} pages to the database ===")
    if not args.yes and not args.dry_run:
        answer = input("Continue? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted.")
            return 1

    discovery = Discovery(base_url=args.base_url, delay=args.delay)
    converter = Converter()
    assets = None if args.no_assets else AssetStore(discovery.session)

    run = ImportRun.objects.create()
    created = updated = thin = failed = 0
    warnings: list[str] = []
    unknown = 0
    by_type: dict[str, int] = {}
    done_slugs: set[str] = set()
    if args.skip_existing and not args.force:
        done_slugs = set(
            Page.objects.filter(source=Source.WIKIDOT).values_list("slug", flat=True)
        )
        print(f"resuming: {len(done_slugs)} already-imported pages will be skipped")

    for index, path in enumerate(target, 1):
        html = discovery.fetch(path)
        if not html:
            failed += 1
            continue

        converted = converter.convert_page(html, path)

        # Second exclusion pass, right before the write.
        skip, _reason = is_excluded(path, converted.title)
        if skip:
            continue
        if len(converted.markdown) < MIN_BODY_LENGTH:
            thin += 1
            continue

        markdown = converted.markdown
        if assets is not None:
            markdown = assets.localize_markdown(markdown)

        existing = Page.objects.filter(slug=converted.slug).first()
        is_new = existing is None

        # Resumable: already-imported pages are skipped unless forced, so an
        # interrupted run can simply be launched again.
        if is_new and args.skip_existing and converted.slug in done_slugs:
            continue
        if is_new and args.skip_existing:
            done_slugs.add(converted.slug)

        page = existing or Page(
            slug=clamp(converted.slug, MAX_SLUG), title=clamp(converted.title, MAX_TITLE)
        )

        page.title = clamp(converted.title, MAX_TITLE)
        page.subtitle = clamp(converted.subtitle, MAX_SUBTITLE)
        page.page_type = converted.page_type
        page.source = Source.WIKIDOT
        page.edition = "D&D 2024"
        page.category = Category.objects.filter(slug=converted.category_slug).first()
        page.source_content = markdown
        page.structured_data = converted.structured_data
        page.visibility = "public"
        page.is_published = True

        # Subclasses point at their parent class page.
        if converted.page_type == "subclass":
            parent_slug = path.split(":")[0]
            page.parent_page = Page.objects.filter(
                slug=f"{parent_slug}"
            ).first() or Page.objects.filter(title__iexact=parent_slug.title()).first()

        save_page_with_derived_data(page, converted.tags or None)

        if is_new:
            created += 1
        else:
            updated += 1
        by_type[converted.page_type] = by_type.get(converted.page_type, 0) + 1

        for warning in converted.warnings:
            unknown += 1
            warnings.append(f"{path}: {warning}")

        if index % 25 == 0:
            print(f"  ... {index}/{len(target)} "
                  f"({created} new, {updated} updated, {failed} failed)")

    run.finished_at = timezone.now()
    run.pages_discovered = len(in_scope) + len(excluded)
    run.pages_in_scope = len(in_scope)
    run.pages_excluded = len(excluded)
    run.pages_imported = created
    run.pages_updated = updated
    run.assets_downloaded = assets.downloaded if assets else 0
    run.broken_links = BrokenLink.objects.count()
    run.unknown_constructs = unknown
    run.warnings = len(warnings)
    run.report = {
        "thin_skipped": thin,
        "fetch_failed": failed,
        "by_type": by_type,
        "warning_samples": warnings[:50],
    }
    run.save()

    print("\n=== IMPORT REPORT ===")
    print(f"Pages discovered : {run.pages_discovered}")
    print(f"Pages in scope   : {run.pages_in_scope}")
    print(f"Pages excluded   : {run.pages_excluded}")
    print(f"Pages imported   : {run.pages_imported}")
    print(f"Pages updated    : {run.pages_updated}")
    print(f"Thin (skipped)   : {thin}")
    print(f"Fetch failed     : {failed}")
    print(f"Assets downloaded: {run.assets_downloaded}")
    print(f"Broken links     : {run.broken_links}")
    print(f"Unknown constructs: {run.unknown_constructs}")
    print(f"Warnings         : {run.warnings}")
    print("\nBy type:")
    for page_type, count in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {page_type:<20}{count:>6}")
    return 0


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
    parser.add_argument("--no-assets", action="store_true",
                        help="Skip image download")
    parser.add_argument("--only", nargs="*", default=None,
                        help="Import only these exact page paths")
    parser.add_argument("--only-file", default=None,
                        help="Import only the page paths listed in this file")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Do not ask for confirmation")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip pages already imported (default: on)")
    parser.add_argument("--force", action="store_true",
                        help="Re-import even pages that already exist")
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

    imp = sub.add_parser("import", help="Fetch, convert and write to the database")
    _add_common(imp)
    imp.set_defaults(func=_cmd_import_wrapper)

    exc = sub.add_parser("list-excluded", help="Preview the exclusion filters")
    exc.set_defaults(func=cmd_list_excluded)

    args = parser.parse_args()
    configure_logging(getattr(args, "verbose", False))
    return args.func(args)


def _cmd_import_wrapper(args) -> int:
    """Set up Django, then run the import."""
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compendium.settings")
    try:
        import django
    except ImportError:  # pragma: no cover
        print("Django is not installed. Run: pip install -r backend/requirements.txt")
        return 1
    django.setup()
    return cmd_import(args)


if __name__ == "__main__":
    raise SystemExit(main())