from django.contrib import admin
from django.utils.html import format_html

from .models import BrokenLink, Category, ImportRun, Page, PageLink, Tag


class PageLinkInline(admin.TabularInline):
    model = PageLink
    fk_name = "source_page"
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "page_type", "source", "category", "visibility", "is_published")
    list_filter = ("page_type", "source", "visibility", "is_published", "category")
    search_fields = ("title", "subtitle", "source_content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [PageLinkInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "subtitle", "slug", "page_type", "category", "parent_page")}),
        ("Metadados", {
            "fields": ("source", "edition", "visibility", "is_published", "tags", "position")
        }),
        ("Conteúdo", {"fields": ("source_content", "rendered_content", "structured_data")}),
        ("Auditoria", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "sidebar_group", "in_sidebar", "position")
    list_filter = ("sidebar_group", "in_sidebar")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(PageLink)
admin.site.register(BrokenLink)
admin.site.register(ImportRun)

admin.site.site_header = "Compendium da Campanha"
admin.site.site_title = "Compendium"
admin.site.index_title = "Administração do compêndio"