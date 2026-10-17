"""Move Dovahkiin's Thu'um catalogue to its own linked child page."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Category, Page
from wiki.services import save_page_with_derived_data


class Command(BaseCommand):
    help = "Create the Dovahkiin Thu'ums page and link to it from the class page."

    @transaction.atomic
    def handle(self, *args, **options):
        parent = Page.objects.filter(slug="dovahkiin").first()
        category = Category.objects.filter(slug="subclasses").first()
        if not parent or not category:
            raise CommandError("Dovahkiin or the Subclasses category was not found.")

        link_path = "/subclasses/dovahkiin-thuums"
        child = Page.objects.filter(slug="dovahkiin-thuums").first()
        if child and link_path in parent.source_content:
            self.stdout.write(self.style.SUCCESS("Dovahkiin Thu'ums page is already split."))
            return

        marker = next((token for token in ("**Thu", "## Thu") if token in parent.source_content), None)
        if not marker:
            raise CommandError("Could not find the Thu'um section in the Dovahkiin page.")

        start = parent.source_content.index(marker)
        thuums = parent.source_content[start:]
        title = "Thu'uns do Dovahkiin"
        child, _ = Page.objects.get_or_create(
            slug="dovahkiin-thuums",
            defaults={
                "title": title,
                "page_type": "subclass",
                "source": parent.source,
                "category": category,
                "parent_page": parent,
            },
        )
        child.title = title
        child.page_type = "subclass"
        child.source = parent.source
        child.category = category
        child.parent_page = parent
        child.source_content = f"# {title}\n\n{thuums}"
        save_page_with_derived_data(child)

        parent.source_content = (
            parent.source_content[:start].rstrip()
            + f"\n\n## Thu'uns\n\nA lista completa de gritos está em [{title}]({link_path})."
        )
        save_page_with_derived_data(parent)
        self.stdout.write(self.style.SUCCESS(f"Created {child.url_path} and linked it from Dovahkiin."))
