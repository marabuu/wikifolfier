"""Pagination that honours an explicit ?page_size= from the client.

DRF ignores page_size by default, which silently truncated the big categories
(Magic Items has 349 pages, Spells 464) to the first 50.
"""
from rest_framework.pagination import PageNumberPagination


class CompendiumPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 2000
    page_query_param = "page"