"""Rebuild the PostgreSQL search vector for every page.

Run after bulk imports or if you ever change the indexing strategy.
"""
from django.core.management.base import BaseCommand

from wiki.models import Page


class Command(BaseCommand):
    help = "Rebuild search vectors."

    def handle(self, *args, **options):
        pages = Page.objects.all()
        count = 0
        for page in pages.iterator():
            page.update_search_vector()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Reindexed {count} pages."))