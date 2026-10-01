"""Core data model for the compendium.

Everything in the system — official, homebrew or campaign specific — is a `Page`.
The only difference between them is the `source` metadata field.
"""
from __future__ import annotations

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.text import slugify


class Source(models.TextChoices):
    OFFICIAL = "official", "Official"
    WIKIDOT = "wikidot", "Wikidot"
    HOMEBREW = "homebrew", "Homebrew"
    CAMPAIGN = "campaign", "Campaign"
    CUSTOM = "custom", "Custom"
    # The campaign's own authored content, imported from .docx.
    FOLFIER = "folfier", "Folfier"


class Visibility(models.TextChoices):
    PUBLIC = "public", "Public"
    GM_ONLY = "gm_only", "GM Only"


class PageType(models.TextChoices):
    CLASS = "class", "Class"
    SUBCLASS = "subclass", "Subclass"
    SPECIES = "species", "Species"
    BACKGROUND = "background", "Background"
    FEAT = "feat", "Feat"
    SPELL = "spell", "Spell"
    MAGIC_ITEM = "magic_item", "Magic Item"
    EQUIPMENT = "equipment", "Equipment"
    WEAPON = "weapon", "Weapon"
    ARMOR = "armor", "Armor"
    ADVENTURING_GEAR = "adventuring_gear", "Adventuring Gear"
    RULE = "rule", "Rule"
    CONDITION = "condition", "Condition"
    LOCATION = "location", "Location"
    NPC = "npc", "NPC"
    FACTION = "faction", "Faction"
    LORE = "lore", "Lore"
    EVENT = "event", "Event"
    SESSION = "session", "Session"
    HOUSE_RULE = "house_rule", "House Rule"
    OTHER = "other", "Other"


# Deliberately out of scope: monsters, creatures and stat blocks.
EXCLUDED_PAGE_TYPES = {"monster", "creature", "stat_block"}


class Category(models.Model):
    """Hierarchical navigation category (Classes, Spells, Locations, ...)."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=100)
    in_sidebar = models.BooleanField(default=True)
    sidebar_group = models.CharField(
        max_length=60,
        default="core",
        help_text="'core' for rulebook groups, 'campaign' for campaign-only content.",
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def ancestors(self):
        chain, node = [], self.parent
        while node:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    @property
    def root(self):
        return self.ancestors[0] if self.ancestors else self

    def get_absolute_url(self) -> str:
        return f"/{self.slug}"


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
class PageQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not (user and user.is_authenticated and user.is_staff):
            return self.filter(visibility=Visibility.PUBLIC)
        return self

    def published(self):
        return self.filter(is_published=True)


class Page(models.Model):
    """A single compendium page. Official, homebrew and campaign content alike."""

    slug = models.SlugField(max_length=180, unique=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    page_type = models.CharField(
        max_length=32, choices=PageType.choices, default=PageType.OTHER, db_index=True
    )
    source = models.CharField(
        max_length=32, choices=Source.choices, default=Source.CUSTOM, db_index=True
    )
    edition = models.CharField(max_length=60, blank=True, default="D&D 2024")
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="pages"
    )
    subcategory = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_pages",
        help_text=(
            "Grouping inside the category: spell level, feat kind, Unearthed "
            "Arcana. Never changes the page URL, which stays under `category`."
        ),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="pages")

    source_content = models.TextField(
        blank=True, help_text="Editable Markdown source. Never store HTML only."
    )
    rendered_content = models.TextField(blank=True)
    structured_data = models.JSONField(
        default=dict, blank=True, help_text="Template data (spell fields, item rarity, ...)"
    )

    visibility = models.CharField(
        max_length=16, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True
    )
    is_published = models.BooleanField(default=True, db_index=True)
    position = models.PositiveIntegerField(default=100)
    parent_page = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_pages",
        help_text="Used by subclasses to point at their parent class.",
    )

    search_vector = SearchVectorField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PageQuerySet.as_manager()

    class Meta:
        ordering = ["title"]
        indexes = [
            GinIndex(fields=["search_vector"], name="page_search_vector_idx"),
            models.Index(fields=["page_type", "category"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180]
        super().save(*args, **kwargs)
        self.update_search_vector()

    def update_search_vector(self) -> None:
        from .search import build_search_vector

        Page.objects.filter(pk=self.pk).update(search_vector=build_search_vector(self))

    # --- structure -------------------------------------------------------
    @property
    def url_path(self) -> str:
        if self.category and self.category.slug:
            return f"/{self.category.slug}/{self.slug}"
        return f"/{self.slug}"

    def get_absolute_url(self) -> str:
        return self.url_path

    @property
    def breadcrumb_trail(self):
        trail = []
        if self.category:
            trail.extend(self.category.ancestors)
            trail.append(self.category)
        trail.append(self)
        return trail

    @property
    def source_label(self) -> str:
        return self.get_source_display()

    def outgoing_links(self):
        return self.from_links.select_related("target_page")

    def incoming_links(self):
        return self.to_links.select_related("source_page")


class PageLink(models.Model):
    """An internal reference between two pages."""

    source_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="from_links"
    )
    target_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="to_links"
    )
    link_text = models.CharField(max_length=255, blank=True)
    is_broken = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_page", "target_page", "link_text"], name="unique_page_link"
            )
        ]

    def __str__(self) -> str:
        return f"{self.source_page} -> {self.target_page}"


class BrokenLink(models.Model):
    """Reference to a target page that does not exist (yet)."""

    source_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="broken_link_records"
    )
    href = models.CharField(max_length=500)
    link_text = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = [("source_page", "href")]

    def __str__(self) -> str:
        return f"{self.source_page} -> {self.href}"


class ImportRun(models.Model):
    """Report of a single importer execution."""

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    pages_discovered = models.IntegerField(default=0)
    pages_in_scope = models.IntegerField(default=0)
    pages_excluded = models.IntegerField(default=0)
    pages_imported = models.IntegerField(default=0)
    pages_updated = models.IntegerField(default=0)
    assets_downloaded = models.IntegerField(default=0)
    broken_links = models.IntegerField(default=0)
    unknown_constructs = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Import {self.started_at:%Y-%m-%d %H:%M}"