"""Add inline links from a class page to its subclasses and spell list.

The imported (official) classes link their subclasses from inside the body. This
command does the same for homebrew classes: each subclass name becomes a link to
its own page, plus a link to the class' spell list.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Page
from wiki.services import save_page_with_derived_data

SUBCLASS_HEADING = "## Subclasses"
SPELL_LIST_HEADING = "## Spell List"


class Command(BaseCommand):
    help = "Link subclasses and spell list inside every class page body."

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0
        report = []

        for page in Page.objects.filter(page_type="class"):
            children = list(page.child_pages.all())
            subclasses = [c for c in children if c.page_type == "subclass"]
            spell_lists = [c for c in children if c.page_type == "spell"]
            if not subclasses and not spell_lists:
                continue

            body = page.source_content or ""
            # Rebuild the link sections so re-running stays idempotent.
            for heading in (SUBCLASS_HEADING, SPELL_LIST_HEADING):
                index = body.find(heading)
                if index == -1:
                    continue
                end = body.find("\n## ", index + len(heading))
                body = (body[:index] + body[end + 1:]) if end != -1 else body[:index]

            blocks = []
            if subclasses:
                lines = "\n".join(
                    f"- [{child.title}]({child.url_path})" for child in subclasses
                )
                blocks.append(f"{SUBCLASS_HEADING}\n\n{lines}")
            if spell_lists:
                lines = "\n".join(
                    f"- [{child.title}]({child.url_path})" for child in spell_lists
                )
                blocks.append(f"{SPELL_LIST_HEADING}\n\n{lines}")

            page.source_content = body.rstrip() + "\n\n" + "\n\n".join(blocks) + "\n"
            save_page_with_derived_data(page)
            updated += 1
            report.append(f"  {page.title}: {len(subclasses)} subclasse(s), "
                          f"{len(spell_lists)} lista(s)")

        self.stdout.write(self.style.SUCCESS(f"classes atualizadas: {updated}"))
        for line in report:
            self.stdout.write(line)