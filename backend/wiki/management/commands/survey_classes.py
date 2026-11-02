"""Temporary survey command — lists H2/H3 headings and existing subclasses for homebrew/folfier class pages."""
from django.core.management.base import BaseCommand
from wiki.models import Page


class Command(BaseCommand):
    help = 'Survey homebrew/folfier class pages for embedded subclasses'

    def handle(self, *args, **options):
        classes = Page.objects.filter(page_type='class', source__in=['homebrew', 'folfier']).order_by('slug')
        for p in classes:
            lines = p.source_content.split('\n')
            h2 = [l[3:].strip() for l in lines if l.startswith('## ')]
            h3 = [l[4:].strip() for l in lines if l.startswith('### ')]
            existing_subs = list(Page.objects.filter(parent_page=p).values_list('slug', flat=True))
            self.stdout.write(f'\n--- {p.slug} (source={p.source}) ---')
            self.stdout.write(f'  H2: {h2}')
            self.stdout.write(f'  H3 (first 10): {h3[:10]}')
            self.stdout.write(f'  Existing subclasses: {existing_subs}')
