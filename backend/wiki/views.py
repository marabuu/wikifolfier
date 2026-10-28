from __future__ import annotations

import time

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import BrokenLink, Category, Page, PageRevision, Source, Visibility
from .permissions import user_is_owner
from .rendering import render
from .search import search_pages
from .services import save_page_with_derived_data
from .serializers import (
    BrokenLinkSerializer,
    CategorySerializer,
    PageDetailSerializer,
    PageLinkSerializer,
    PageListSerializer,
    PageContentSerializer,
    PageRevisionSerializer,
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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    from .models import Tag

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class SpellFilterBackend(DjangoFilterBackend):
    """Extra filters for the spell index: level, school and casting class."""

    SPELL_CLASSES = {
        "artificer", "barbarian", "bard", "cleric", "druid", "fighter",
        "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard",
        "runescaper", "filho-da-magia", "heroi",
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
    filterset_fields = {
        "page_type": ["exact"],
        "source": ["exact"],
        "edition": ["exact"],
        "visibility": ["exact"],
        "category": ["exact"],
        "is_published": ["exact"],
        "parent_page__slug": ["exact"],
        # The home page and changelog must only show pages changed through
        # the application, which are marked with this timestamp.
        "app_modified_at": ["exact", "isnull"],
        # Friendly filters: the frontend works with readable slugs, not FK ids.
        "category__slug": ["exact"],
        "subcategory__slug": ["exact"],
        "tags__slug": ["exact"],
    }
    search_fields = ["title", "subtitle"]
    ordering_fields = ["title", "updated_at", "app_modified_at", "page_type"]

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

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def content(self, request, slug=None):
        """Save a markdown-only revision. Tags and all page metadata stay untouched."""
        if not user_is_owner(request.user):
            return Response({"detail": "Apenas o proprietário pode editar."}, status=403)
        page = self.get_object()
        serializer = PageContentSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data.get("source_content", page.source_content)
        if content == page.source_content:
            return Response(PageDetailSerializer(page, context={"request": request}).data)
        PageRevision.objects.create(
            page=page, content=page.source_content, status="saved", changed_by=request.user
        )
        page.source_content = content
        page.app_modified_at = timezone.now()
        save_page_with_derived_data(page)
        return Response(PageDetailSerializer(page, context={"request": request}).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def revisions(self, request, slug=None):
        if not user_is_owner(request.user):
            return Response({"detail": "Apenas o proprietário pode consultar revisões."}, status=403)
        return Response(PageRevisionSerializer(self.get_object().revisions.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path=r"revisions/(?P<revision_id>[^/.]+)/rollback", permission_classes=[IsAuthenticated])
    def rollback(self, request, slug=None, revision_id=None):
        if not user_is_owner(request.user):
            return Response({"detail": "Apenas o proprietário pode restaurar revisões."}, status=403)
        page = self.get_object()
        revision = get_object_or_404(PageRevision, pk=revision_id, page=page)
        PageRevision.objects.create(
            page=page, content=page.source_content, status="rolled_back", changed_by=request.user
        )
        page.source_content = revision.content
        save_page_with_derived_data(page)
        revision.status = "restored"
        revision.save(update_fields=["status"])
        return Response(PageDetailSerializer(page, context={"request": request}).data)


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


class SpellIndexItemSerializer(serializers.ModelSerializer):
    """Light payload for the spell index.

    Deliberately omits `excerpt`: building it renders and strips the whole HTML
    body of every spell, which took ~9s for 464 pages on each request.
    """

    class Meta:
        model = Page
        fields = ("id", "slug", "title", "page_type", "url_path", "structured_data")


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
        "runescaper", "filho-da-magia", "heroi",
    ]

    CACHE_TTL = 60.0
    _cache: dict = {}
    _cache_time: dict = {}

    def get(self, request):
        params = request.query_params
        level = params.get("level")
        school = params.get("school")
        klass = params.get("class")

        key = (level, school, klass)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - self._cache_time.get(key, 0) < self.CACHE_TTL:
            return Response(cached)

        # Unearthed Arcana spells have their own page and stay out of the index.
        # The has_key guard matters: without it, `NOT (path LIKE 'ua:%')` is NULL
        # in SQL for spells that have no wikidot_path key at all (folfier/homebrew
        # spells), silently dropping them from the index.
        queryset = visible_pages(request).filter(page_type="spell")
        queryset = queryset.exclude(
            Q(structured_data__has_key="wikidot_path"),
            Q(structured_data__wikidot_path__startswith="ua:"),
        )

        if level not in (None, ""):
            try:
                queryset = queryset.filter(structured_data__level=int(level))
            except (TypeError, ValueError):
                pass

        if school:
            queryset = queryset.filter(structured_data__school__iexact=school)

        if klass:
            slug = klass.strip().lower()
            if slug in self.CLASSES:
                # Corresponde ao slug (como os importadores gravam) e também à
                # tag da classe. A normalização em minúsculas evita falhar quando
                # os dados guardam a classe com acento/maiusculas (ex.: "Runescaper",
                # "Filho da Magia", "Herói").
                queryset = queryset.filter(
                    Q(structured_data__classes__contains=[slug])
                    | Q(tags__slug=slug)
                ).distinct()

        rows = queryset.order_by("title")[:600]
        results = SpellIndexItemSerializer(rows, many=True).data

        counts = {level_value: 0 for level_value, _ in
                  [(0, "Cantrip")] + [(n, f"Nível {n}") for n in range(1, 10)]}
        for row in results:
            value = (row.get("structured_data") or {}).get("level")
            if isinstance(value, int) and value in counts:
                counts[value] += 1

        groups = [
            {"level": value, "label": label, "count": counts[value]}
            for value, label in
            [(0, "Cantrip")] + [(n, f"Nível {n}") for n in range(1, 10)]
        ]

        payload = {
            "count": len(results),
            "results": results,
            "groups": groups,
            "schools": self.SCHOOLS,
            "classes": self.CLASSES,
        }
        self._cache[key] = payload
        self._cache_time[key] = now
        return Response(payload)


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
