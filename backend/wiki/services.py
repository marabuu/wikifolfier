"""Business logic: rendering, link sync and tag handling.

Kept out of serializers/views so the importer can reuse exactly the same code path.
"""
from __future__ import annotations

from django.utils.text import slugify

from .models import BrokenLink, Page, PageLink, Tag
from .rendering import render


def save_page_with_derived_data(page: Page, tag_names=None) -> Page:
    """Persist a page, rendering markdown and syncing internal links."""
    result = render(page.source_content)
    page.rendered_content = result.html
    page.save()

    if tag_names is not None:
        tags = []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag, _ = Tag.objects.get_or_create(
                slug=slugify(name)[:60], defaults={"name": name[:60]}
            )
            tags.append(tag)
        page.tags.set(tags)

    sync_links(page, result.internal_links)
    return page


def sync_links(page: Page, internal_links) -> dict:
    """Rebuild PageLink / BrokenLink rows for a page.

    internal_links: iterable of (target_slug, link_text)
    """
    page.from_links.all().delete()
    page.broken_link_records.all().delete()

    known = {}
    broken = 0
    created = 0
    seen = set()

    for slug, text in internal_links:
        if not slug or slug in seen:
            continue
        seen.add(slug)
        target = known.get(slug)
        if target is None:
            target = Page.objects.filter(slug=slug).first()
            known[slug] = target
        if target is None:
            BrokenLink.objects.get_or_create(
                source_page=page, href=f"/{slug}", link_text=text[:255]
            )
            broken += 1
            continue
        PageLink.objects.get_or_create(
            source_page=page, target_page=target, link_text=text[:255]
        )
        created += 1

    return {"links": created, "broken": broken}