"""Merge a Folfier page into an existing official page.

The official text is never discarded: the homebrew is appended under the
section matching its level, so "Hand of Ultimate Harm" lands next to the
official "Level 17" features instead of floating at the end.
"""
from __future__ import annotations

import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Page, Source
from wiki.services import save_page_with_derived_data

LEVEL_RE = re.compile(r"^#{2,4}\s*(?:N[ií]vel\s*)?(\d{1,2})\b", re.IGNORECASE)
MERGE_MARKER = "### Ajustes Folfier"


class Command(BaseCommand):
    help = "Merge a source=folfier page into the official page of the same name."

    def add_arguments(self, parser):
        parser.add_argument("slug", help="Slug of the official page")
        parser.add_argument("--from-slug", default=None,
                            help="Slug of the folfier page (default: <slug>-folfier)")
        parser.add_argument("--drop-source", action="store_true", default=True,
                            help="Delete the folfier page after merging")

    @transaction.atomic
    def handle(self, *args, **options):
        slug = options["slug"]
        from_slug = options["from_slug"] or f"{slug}-folfier"

        official = Page.objects.filter(slug=slug, source=Source.WIKIDOT).first()
        if official is None:
            raise CommandError(f"pagina oficial nao encontrada: {slug}")

        homebrew = Page.objects.filter(
            slug=from_slug, source=Source.FOLFIER
        ).first()
        if homebrew is None:
            raise CommandError(f"pagina folfier nao encontrada: {from_slug}")

        if MERGE_MARKER in official.source_content:
            self.stdout.write(self.style.WARNING(
                f"{slug} ja contem um bloco Folfier; nada foi alterado."
            ))
            return

        level = self._detect_level(homebrew.source_content)
        merged = self._insert(official.source_content, homebrew.source_content, level)

        official.source_content = merged
        save_page_with_derived_data(official)

        if options["drop_source"]:
            homebrew.delete()

        self.stdout.write(self.style.SUCCESS(f"mesclado: {slug}"))
        self.stdout.write(
            f"  nivel detectado: {level or 'sem nivel'}"
        )
        self.stdout.write(f"  markdown: {len(official.source_content)} chars")
        if options["drop_source"]:
            self.stdout.write(f"  pagina folfier removida: {homebrew.slug}")

    @staticmethod
    def _detect_level(markdown: str):
        """Level mentioned in the homebrew text, e.g. 'No nivel 17'."""
        match = re.search(r"n[ií]vel\s*(\d{1,2})", markdown, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _insert(body: str, addition: str, level: int | None) -> str:
        block = f"{MERGE_MARKER}\n\n{addition.strip()}\n"

        if level is not None:
            pattern = re.compile(
                r"^(#{2,4}\s*(?:N[ií]vel\s*)?\d{1,2}\b.*)$", re.MULTILINE | re.IGNORECASE
            )
            matches = list(pattern.finditer(body))
            # Insert after the last section of the matching level.
            same_level = [m for m in matches
                          if int(re.search(r"(\d{1,2})", m.group(1)).group(1)) == level]
            target = (same_level or matches)
            if target:
                last = target[-1]
                # Find the end of that section (next heading or end of text).
                nxt = re.search(r"^#{2,4}\s", body[last.end():], re.MULTILINE)
                end = last.end() + (nxt.start() if nxt else len(body) - last.end())
                return body[:end].rstrip() + "\n\n" + block + "\n" + body[end:].lstrip()

        return body.rstrip() + "\n\n" + block