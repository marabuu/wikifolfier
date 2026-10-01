"""Give each class spell-list table its level heading.

The imported spell list pages stack one table per spell level with no label, so
a reader cannot tell where cantrips end and 3rd-level starts. Instead of
assuming the order, this reads the structured level of the spells inside each
table and only inserts a heading when every spell in that table agrees.

Safe to re-run: a table that already has a heading is skipped.
"""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Page
from wiki.services import save_page_with_derived_data

LEVEL_HEADINGS = {
    0: "Cantrip",
    1: "1st Level", 2: "2nd Level", 3: "3rd Level", 4: "4th Level",
    5: "5th Level", 6: "6th Level", 7: "7th Level", 8: "8th Level",
    9: "9th Level",
}

SPELL_LINK = "[%s](/%s)"


class Command(BaseCommand):
    help = "Insert level headings into class spell-list tables."

    @transaction.atomic
    def handle(self, *args, **options):
        slugs_by_level = self._spell_levels()
        changed_pages = 0
        inserted = 0

        for page in Page.objects.filter(page_type="subclass"):
            text = page.source_content or ""
            if text.count("| --- |") < 2:
                continue

            new_text, count = self._label_tables(text, slugs_by_level)
            if not count:
                continue

            page.source_content = new_text
            save_page_with_derived_data(page)
            changed_pages += 1
            inserted += count

        self.stdout.write(
            self.style.SUCCESS(
                f"{changed_pages} paginas atualizadas, {inserted} titulos inseridos"
            )
        )

    @staticmethod
    def _spell_levels() -> dict:
        levels = {}
        for slug, data in Page.objects.filter(page_type="spell").values_list(
            "slug", "structured_data"
        ):
            level = (data or {}).get("level")
            if isinstance(level, int):
                levels[slug] = level
        return levels

    def _label_tables(self, text: str, levels: dict) -> tuple[str, int]:
        """Walk the tables in order and prepend a heading when unambiguous."""
        blocks = text.split("\n\n")
        output: list[str] = []
        inserted = 0
        previous_level = None

        for index, block in enumerate(blocks):
            if not block.lstrip().startswith("|") or "| --- |" not in block:
                output.append(block)
                continue

            # A heading already directly above this table: leave it alone.
            previous = blocks[index - 1].strip() if index else ""
            if previous.startswith("#"):
                output.append(block)
                continue

            found = Counter()
            for line in block.splitlines():
                if not line.startswith("|"):
                    continue
                for slug in _slugs_in_row(line):
                    if slug in levels:
                        found[levels[slug]] += 1

            # Label by the dominant level, but only when it is clearly dominant:
            # a table mixing levels must not get a misleading heading.
            if found:
                total = sum(found.values())
                level, hits = found.most_common(1)[0]
                if level in LEVEL_HEADINGS and hits / total >= 0.8:
                    if level != previous_level:
                        output.append(f"### {LEVEL_HEADINGS[level]}")
                        inserted += 1
                        previous_level = level
            output.append(block)

        return "\n\n".join(output), inserted


def _slugs_in_row(line: str):
    for label, slug in _iter_links(line):
        yield slug


def _iter_links(line: str):
    """Yield (label, slug) for every markdown link in a table row."""
    import re

    for match in re.finditer(r"\[([^\]]+)\]\((/[^)]+)\)", line):
        yield match.group(1), match.group(2).strip("/").split("/")[-1]
