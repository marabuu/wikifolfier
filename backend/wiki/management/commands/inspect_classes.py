"""Inspect specific class pages for embedded subclass content."""
from django.core.management.base import BaseCommand
from wiki.models import Page


class Command(BaseCommand):
    help = 'Inspect specific class pages'

    def handle(self, *args, **options):
        for slug in ['witcher', 'filho-da-magia', 'heroi', 'xama']:
            p = Page.objects.get(slug=slug)
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'=== {slug} ===')
            self.stdout.write(f'{"="*60}')
            self.stdout.write(p.source_content)
