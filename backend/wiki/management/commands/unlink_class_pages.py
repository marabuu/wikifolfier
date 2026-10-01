"""Remove the inline link sections previously injected into class pages.

`link_class_pages` appended "## Subclasses" / "## Spell List" blocks to class
bodies. Those duplicated the list the page already renders from its children and
were applied to imported official pages too, so they are reverted here.
"""
from __future__ import annotations

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Page
from wiki.services import save_page_with_derived_data

HEADINGS = ("## Subclasses", "## Spell List")


class Command(BaseCommand):
    help = "Strip the injected Subclasses/Spell List blocks from class bodies."

    @transaction.atomic
    def handle(self, *args, **options):
        changed = 0

        for page in Page.objects.filter(page_type="class"):
            body = page.source_content or ""
            original = body

            for heading in HEADINGS:
                while heading in body:
                    index = body.index(heading)
                    rest = body[index + len(heading):]
                    # The block ends at the next H2 or the end of the document.
                    nxt = re.search(r"^##\s", rest, re.MULTILINE)
                    end = index + len(heading) + (nxt.start() if nxt else len(rest))
                    body = body[:index] + body[end:]

            body = re.sub(r"\n{3,}", "\n\n", body).rstrip() + "\n"

            if body != original:
                page.source_content = body
                save_page_with_derived_data(page)
                changed += 1
                self.stdout.write(f"  {page.title}: removido")

        self.stdout.write(self.style.SUCCESS(f"paginas ajustadas: {changed}"))