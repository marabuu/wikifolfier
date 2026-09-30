"""PostgreSQL full text search helpers."""
from __future__ import annotations

from django.contrib.postgres.search import SearchRank, SearchQuery, SearchVector
from django.db.models import F

SEARCH_CONFIG = "portuguese"


def build_search_vector(page):
    return (
        SearchVector("title", weight="A", config=SEARCH_CONFIG)
        + SearchVector("subtitle", weight="B", config=SEARCH_CONFIG)
        + SearchVector("source_content", weight="D", config=SEARCH_CONFIG)
    )


def search_pages(queryset, term: str):
    """Ranked full text search over title, subtitle and markdown content."""
    if not term or not term.strip():
        return queryset.none()
    query = SearchQuery(term, config=SEARCH_CONFIG, search_type="websearch")
    return (
        queryset.annotate(rank=SearchRank(F("search_vector"), query))
        .filter(search_vector=query)
        .order_by("-rank", "title")
    )