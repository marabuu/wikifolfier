from __future__ import annotations

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BrokenLink, Category, Page, Source, Visibility
from .rendering import render
from .search import search_pages
from .serializers import (
    BrokenLinkSerializer,
    CategorySerializer,
    PageDetailSerializer,
    PageLinkSerializer,
    PageListSerializer,
    PageWriteSerializer,
    TagSerializer,
)


def visible_pages(request):
    qs = Page.objects.published().select_related("category", "parent_page")
    return qs.visible_to(request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.annotate(
            page_count=Count("pages", filter=Q(pages__is_published=True))
        ).prefetch_related("children")

    @action(detail=False, methods=["get"])
    def tree(self, request):
        roots = [c for c in self.get_queryset() if c.parent_id is None and c.in_sidebar]
        return Response(CategorySerializer(roots, many=True, context={"request": request}).data)


class TagViewSet(viewsets.ModelViewSet):
    from .models import Tag

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class PageViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"
    filterset_fields = [
        "page_type",
        "source",
        "edition",
        "visibility",
        "category",
        "is_published",
        "parent_page__slug",
    ]
    # Friendly filters: the frontend works with readable slugs, not FK ids.
    filterset_fields = filterset_fields + ["category__slug", "tags__slug"]
    search_fields = ["title", "subtitle"]
    ordering_fields = ["title", "updated_at", "page_type"]

    def get_queryset(self):
        return visible_pages(self.request).prefetch_related("tags")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PageWriteSerializer
        if self.action == "list":
            return PageListSerializer
        return PageDetailSerializer

    def get_object(self):
        page = get_object_or_404(visible_pages(self.request), slug=self.kwargs["slug"])
        self.check_object_permissions(self.request, page)
        return page

    @action(detail=True, methods=["get"])
    def backlinks(self, request, slug=None):
        return Response(
            PageLinkSerializer(self.get_object().incoming_links(), many=True).data
        )

    @action(detail=True, methods=["get"])
    def outlinks(self, request, slug=None):
        return Response(PageLinkSerializer(self.get_object().outgoing_links(), many=True).data)

    @action(detail=True, methods=["get"])
    def children(self, request, slug=None):
        return Response(
            PageListSerializer(self.get_object().child_pages.all(), many=True).data
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def preview(self, request):
        result = render(request.data.get("markdown", ""))
        return Response({"html": result.html, "links": result.internal_links})


class BrokenLinkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BrokenLink.objects.select_related("source_page")
    serializer_class = BrokenLinkSerializer
    pagination_class = None


class SearchView(APIView):
    def get(self, request):
        term = request.query_params.get("q", "")
        qs = visible_pages(request)

        page_type = request.query_params.get("type")
        source = request.query_params.get("source")
        category = request.query_params.get("category")
        for tag in request.query_params.getlist("tag"):
            qs = qs.filter(tags__slug=tag)

        if page_type:
            qs = qs.filter(page_type=page_type)
        if source:
            qs = qs.filter(source=source)
        if category:
            # Accept either the category id or its readable slug.
            if str(category).isdigit():
                qs = qs.filter(category_id=category)
            else:
                qs = qs.filter(category__slug=category)
        qs = qs.distinct()

        qs = search_pages(qs, term) if term.strip() else qs.order_by("title")

        return Response(
            {
                "query": term,
                "count": qs.count(),
                "results": PageListSerializer(qs[:100], many=True).data,
                "filters": {
                    "types": [c[0] for c in Page._meta.get_field("page_type").choices],
                    "sources": [c[0] for c in Source.choices],
                    "visibilities": [c[0] for c in Visibility.choices],
                },
            }
        )


class NavigationView(APIView):
    def get(self, request):
        qs = Category.objects.filter(in_sidebar=True).prefetch_related("children")
        payload = {"core": [], "campaign": []}
        for cat in qs.filter(parent__isnull=True):
            bucket = "campaign" if cat.sidebar_group == "campaign" else "core"
            payload[bucket].append(
                CategorySerializer(cat, context={"request": request}).data
            )
        return Response(payload)


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_ok = True
        except Exception:  # pragma: no cover
            db_ok = False
        return Response(
            {"status": "ok" if db_ok else "degraded", "database": db_ok},
            status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )