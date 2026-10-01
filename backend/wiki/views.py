from __future__ import annotations

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

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


class SpellFilterBackend(DjangoFilterBackend):
    """Extra filters for the spell index: level, school and casting class."""

    SPELL_CLASSES = {
        "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
        "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    }

    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)

        params = request.query_params

        level = params.get("level")
        if level is not None and level != "":
            try:
                queryset = queryset.filter(structured_data__level=int(level))
            except (TypeError, ValueError):
                pass

        school = params.get("school")
        if school:
            queryset = queryset.filter(
                structured_data__school__iexact=school
            )

        klass = params.get("class")
        if klass:
            slug = klass.strip().lower()
            if slug in self.SPELL_CLASSES:
                # Either recorded in the structured data or as a wiki tag.
                queryset = queryset.filter(
                    Q(structured_data__classes__contains=[slug]) | Q(tags__slug=slug)
                ).distinct()

        return queryset


class PageViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"
    filter_backends = [SpellFilterBackend] + list(api_settings.DEFAULT_FILTER_BACKENDS)
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
    filterset_fields = filterset_fields + [
        "category__slug",
        "subcategory__slug",
        "tags__slug",
    ]
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


class SpellIndexView(APIView):
    """Spell index: filterable by level, school and casting class.

    Always returns the whole set (no pagination) so the index page can group
    spells by level and offer live filters.
    """

    SCHOOLS = [
        "Abjuration", "Conjuration", "Divination", "Enchantment",
        "Evocation", "Illusion", "Necromancy", "Transmutation",
    ]
    CLASSES = [
        "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
        "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
    ]

    def get(self, request):
        params = request.query_params
        queryset = visible_pages(request).filter(page_type="spell")

        level = params.get("level")
        if level not in (None, ""):
            try:
                queryset = queryset.filter(structured_data__level=int(level))
            except (TypeError, ValueError):
                pass

        school = params.get("school")
        if school:
            queryset = queryset.filter(structured_data__school__iexact=school)

        klass = params.get("class")
        if klass and klass in self.CLASSES:
            queryset = queryset.filter(
                Q(structured_data__classes__contains=[klass])
                | Q(tags__slug=klass)
            ).distinct()

        results = PageListSerializer(queryset.order_by("title")[:600], many=True).data

        groups = []
        for value, label in [(0, "Cantrip")] + [(n, f"Nível {n}") for n in range(1, 10)]:
            groups.append({
                "level": value,
                "label": label,
                "count": sum(
                    1 for row in results
                    if (row.get("structured_data") or {}).get("level") == value
                ),
            })

        return Response({
            "count": len(results),
            "results": results,
            "groups": groups,
            "schools": self.SCHOOLS,
            "classes": self.CLASSES,
        })


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