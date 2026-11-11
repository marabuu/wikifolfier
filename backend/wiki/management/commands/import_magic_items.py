"""Import all magic items from dnd2024.wikidot.com/magic-item:all with exact prices.

Fetches the master magic-item:all index, extracts the exact prices and rarities
from all tables, fetches individual item pages concurrently with rate-limiting and retries,
renders markdown with proper Preço Sugerido, sets structured_data, and persists to the compendium.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

# Ensure importer module can be imported
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "importer") not in sys.path:
    sys.path.insert(0, str(ROOT / "importer"))

from wikidot.converter import Converter
from wiki.models import Category, Page
from wiki.services import save_page_with_derived_data

BASE_URL = "http://dnd2024.wikidot.com"
INDEX_URL = f"{BASE_URL}/magic-item:all"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"

RARITY_ORDER = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"]


def parse_numeric_price(price_str: str) -> int | None:
    """Extract clean integer price in GP if possible (e.g. '4,000 GP' -> 4000)."""
    clean = price_str.replace(",", "").strip()
    match = re.search(r"\b(\d+)\s*GP\b", clean, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def fetch_html_with_retry(url: str, max_retries: int = 4) -> str:
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                sleep_sec = 2.0 * (attempt + 1)
                time.sleep(sleep_sec)
                continue
            return ""
        except Exception:
            time.sleep(1.5 * (attempt + 1))
            continue
    return ""


class Command(BaseCommand):
    help = "Import all magic items from Wikidot with accurate prices."

    def add_arguments(self, parser):
        parser.add_argument("--workers", type=int, default=4, help="Concurrent workers for fetching")
        parser.add_argument("--limit", type=int, default=None, help="Limit number of items (for testing)")
        parser.add_argument("--dry-run", action="store_true", help="Do not write to database")

    def handle(self, *args, **options):
        workers = options["workers"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        converter = Converter()

        magic_cat = Category.objects.filter(slug="magic-items").first()
        if not magic_cat:
            self.stderr.write("Category 'magic-items' not found!")
            return

        self.stdout.write("1. Fetching master magic items index from Wikidot...")
        index_html = fetch_html_with_retry(INDEX_URL)
        if not index_html:
            self.stderr.write("Failed to fetch master index!")
            return

        tables = re.findall(r"<table[^>]*>(.*?)</table>", index_html, re.DOTALL)
        self.stdout.write(f"   Found {len(tables)} tables on master index.")

        items_by_slug: dict[str, dict] = {}

        for i, table_html in enumerate(tables):
            rarity = RARITY_ORDER[i] if i < len(RARITY_ORDER) else "Special"
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)
            for row in rows[1:]:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
                if len(cells) < 4:
                    continue

                link_match = re.search(r'href=["\']?/magic-item:([^"\'\s>]+)["\']?[^>]*>(.*?)</a>', cells[0])
                if link_match:
                    slug = link_match.group(1).strip()
                    title = re.sub(r"<[^>]+>", "", link_match.group(2)).strip()
                else:
                    title = re.sub(r"<[^>]+>", "", cells[0]).strip()
                    slug = title.lower().replace(" ", "-")

                item_type = re.sub(r"<[^>]+>", "", cells[1]).strip()
                attuned_raw = re.sub(r"<[^>]+>", "", cells[2]).strip()
                attuned = "attuned" in attuned_raw.lower() or "yes" in attuned_raw.lower()
                price_raw = re.sub(r"<[^>]+>", "", cells[3]).strip()
                price_raw = re.sub(r"\s+", " ", price_raw)

                if slug in items_by_slug:
                    existing = items_by_slug[slug]
                    existing_rarities = set(existing["rarities"])
                    existing_rarities.add(rarity)
                    existing["rarities"] = [r for r in RARITY_ORDER if r in existing_rarities]
                    existing["price_display"] = "Varies"
                    if attuned:
                        existing["requires_attunement"] = True
                else:
                    items_by_slug[slug] = {
                        "slug": slug,
                        "title": title,
                        "rarity": rarity,
                        "rarities": [rarity],
                        "item_type": item_type,
                        "requires_attunement": attuned,
                        "price_raw": price_raw,
                        "price_display": price_raw if price_raw else "—",
                        "price_num": parse_numeric_price(price_raw),
                    }

        unique_items = list(items_by_slug.values())
        if limit:
            unique_items = unique_items[:limit]

        self.stdout.write(f"   Parsed {len(unique_items)} unique magic items to import.")

        # Concurrently fetch item pages with polite worker count
        self.stdout.write(f"\n2. Fetching {len(unique_items)} item descriptions with {workers} workers...")
        pages_html: dict[str, str] = {}
        start_time = time.time()

        def fetch_item(item):
            slug = item["slug"]
            url = f"{BASE_URL}/magic-item:{slug}"
            return slug, fetch_html_with_retry(url)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch_item, it) for it in unique_items]
            completed = 0
            for fut in as_completed(futures):
                slug, html = fut.result()
                if html:
                    pages_html[slug] = html
                completed += 1
                if completed % 50 == 0 or completed == len(unique_items):
                    self.stdout.write(f"   Fetched [{completed}/{len(unique_items)}] pages ({time.time() - start_time:.1f}s)")

        self.stdout.write(f"\n3. Saving items to database (dry_run={dry_run})...")
        saved_count = 0
        updated_count = 0

        for item in unique_items:
            slug = item["slug"]
            path = f"magic-item:{slug}"
            html = pages_html.get(slug)

            # Consolidate rarity label
            if len(item["rarities"]) > 1:
                rarity_label = ", ".join(item["rarities"])
            else:
                rarity_label = item["rarity"]

            price_display = item["price_display"]
            price_num = item["price_num"]
            item_type = item["item_type"]

            existing_page = Page.objects.filter(slug=slug).first()

            if html:
                conv = converter.convert_page(html, path)
                title = conv.title
                subtitle = conv.subtitle or ""
                body = conv.markdown.strip()
                tags = set(conv.tags)
                requires_attunement = item["requires_attunement"] or conv.structured_data.get("requires_attunement", False)
                if not item_type:
                    item_type = conv.structured_data.get("item_type", "Wondrous Item")
            elif existing_page:
                title = existing_page.title
                subtitle = existing_page.subtitle or ""
                body = existing_page.source_content or ""
                tags = set(t.name for t in existing_page.tags.all())
                requires_attunement = item["requires_attunement"] or existing_page.structured_data.get("requires_attunement", False)
            else:
                self.stderr.write(f"   Missing data for {slug}, skipping.")
                continue

            # Strip any existing Preço Sugerido from body
            body = re.sub(r"\n*\*\*Pre[çc]o Sugerido:\*\*.*?\n+", "\n\n", body, flags=re.IGNORECASE).strip()

            # Format source content with Preço Sugerido
            header_match = re.match(r"^(\*[^*]+\*\n*)", body)
            if header_match:
                header = header_match.group(1).rstrip()
                rest = body[header_match.end():].lstrip()
                source_content = f"{header}\n\n**Preço Sugerido:** {price_display}\n\n{rest}"
            else:
                attune_str = " (Requires Attunement)" if requires_attunement else ""
                header = f"*{item_type}, {rarity_label}{attune_str}*"
                source_content = f"{header}\n\n**Preço Sugerido:** {price_display}\n\n{body}"

            sd = {
                "rarity": rarity_label,
                "item_type": item_type,
                "requires_attunement": requires_attunement,
                "price": price_num,
                "price_display": price_display,
                "wikidot_path": path,
            }

            tags.add("magic-item")
            for r in item["rarities"]:
                tags.add(r.lower().replace(" ", "-"))
            if item_type:
                tags.add(item_type.lower().replace(" ", "-"))

            clean_tags = [str(t).strip().lower() for t in tags if str(t).strip()]

            if dry_run:
                self.stdout.write(f"   [DRY-RUN] {title} ({slug}) | {rarity_label} | {item_type} | Price: {price_display}")
                continue

            with transaction.atomic():
                page = existing_page
                if not page:
                    page = Page(slug=slug)
                    created = True
                else:
                    created = False

                page.title = title
                page.subtitle = subtitle
                page.page_type = "magic_item"
                page.category = magic_cat
                page.subcategory = None
                page.parent_page = None
                page.source = "wikidot"
                page.edition = "D&D 2024"
                page.visibility = "public"
                page.is_published = True
                page.structured_data = sd
                page.source_content = source_content

                save_page_with_derived_data(page, tag_names=clean_tags)
                page.update_search_vector()

                if created:
                    saved_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nFinished! Created: {saved_count}, Updated: {updated_count} magic items with exact Wikidot prices."
        ))
