from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import serializers

from .models import Category, Page, PageLink, Tag
from .rendering import strip_html
from .services import save_page_with_derived_data


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    page_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = (
            "id", "name", "slug", "parent", "description",
            "position", "in_sidebar", "sidebar_group", "children", "page_count",
        )

    def get_children(self, obj: Category):
        return CategorySerializer(obj.children.all(), many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class PageListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    subcategory = CategorySerializer(read_only=True)
    source_label = serializers.CharField(read_only=True)
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = (
            "id", "slug", "title", "subtitle", "page_type", "source", "source_label",
            "edition", "category", "subcategory", "url_path", "visibility", "excerpt",
            "structured_data",
        )

    def get_excerpt(self, obj: Page) -> str:
        return strip_html(obj.rendered_content)


class PageDetailSerializer(PageListSerializer):
    tags = TagSerializer(many=True, read_only=True)
    parent_page = PageListSerializer(read_only=True)

    class Meta(PageListSerializer.Meta):
        fields = [
            f for f in PageListSerializer.Meta.fields if f != "structured_data"
        ] + [
            "source_content",
            "rendered_content",
            "structured_data",
            "tags",
            "parent_page",
            "created_at",
            "updated_at",
        ]


class PageWriteSerializer(serializers.ModelSerializer):
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=60), write_only=True, required=False
    )

    class Meta:
        model = Page
        fields = (
            "id", "slug", "title", "subtitle", "page_type", "source", "edition",
            "category", "parent_page", "source_content", "structured_data",
            "visibility", "is_published", "position", "tag_names",
        )

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", [])
        page = Page(**validated_data)
        save_page_with_derived_data(page, tag_names)
        return page

    def update(self, instance, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        save_page_with_derived_data(instance, tag_names)
        return instance


class PageLinkSerializer(serializers.ModelSerializer):
    source_title = serializers.CharField(source="source_page.title", read_only=True)
    target_title = serializers.CharField(source="target_page.title", read_only=True)
    target_path = serializers.CharField(source="target_page.url_path", read_only=True)

    class Meta:
        model = PageLink
        fields = ("id", "source_page", "target_page", "link_text",
                  "source_title", "target_title", "target_path")


class BrokenLinkSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    href = serializers.CharField(read_only=True)
    link_text = serializers.CharField(read_only=True)
    source_page = serializers.CharField(source="source_page.title", read_only=True)