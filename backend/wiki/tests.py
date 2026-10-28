from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from wiki.models import BrokenLink, Category, Page, PageType, Source
from wiki.rendering import render
from wiki.services import save_page_with_derived_data


def make_page(title, **kwargs):
    tags = kwargs.pop("tags", None)
    page = Page(
        title=title,
        page_type=kwargs.pop("page_type", PageType.OTHER),
        source=kwargs.pop("source", Source.CUSTOM),
        source_content=kwargs.pop("source_content", ""),
        **kwargs,
    )
    save_page_with_derived_data(page, tags)
    return page


class ModelTests(TestCase):
    def test_slug_generated_from_title(self):
        page = Page(title="Rune Mage")
        page.save()
        self.assertEqual(page.slug, "rune-mage")

    def test_url_path_uses_category(self):
        category = Category.objects.create(name="Classes")
        page = make_page("Wizard", category=category)
        self.assertEqual(page.url_path, "/classes/wizard")

    def test_no_homebrew_category_is_created(self):
        self.assertFalse(Category.objects.filter(name__icontains="homebrew").exists())
        self.assertFalse(Category.objects.filter(name__icontains="campaign").exists())

    def test_source_is_metadata_only(self):
        official = make_page("Wizard", source=Source.WIKIDOT)
        homebrew = make_page("Rune Mage", source=Source.HOMEBREW)
        self.assertEqual(official.source_label, "Wikidot")
        self.assertEqual(homebrew.source_label, "Homebrew")

    def test_category_hierarchy(self):
        root = Category.objects.create(name="Equipment")
        child = Category.objects.create(name="Weapons", parent=root)
        self.assertEqual(child.ancestors, [root])

    def test_visibility_filtering(self):
        make_page("Public Lore")
        make_page("Secret Ruin", visibility="gm_only")
        anon = type("U", (), {"is_authenticated": False, "is_staff": False})()
        self.assertEqual(Page.objects.visible_to(anon).count(), 1)


class RenderingTests(SimpleTestCase):
    """Pure rendering tests: runnable without a database."""
    def test_headings_and_paragraphs(self):
        result = render("## Heading\n\nText.")
        self.assertIn("<h2>Heading</h2>", result.html)
        self.assertIn("<p>Text.</p>", result.html)

    def test_tables_render(self):
        result = render("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<table>", result.html)
        self.assertIn("<td>", result.html)

    def test_lists_render(self):
        self.assertIn("<ul>", render("- one\n- two").html)

    def test_internal_links_collected(self):
        result = render("See [Fireball](/spells/fireball).")
        self.assertEqual(result.internal_links, [("fireball", "Fireball")])

    def test_external_links_not_collected(self):
        self.assertEqual(render("[W](https://dnd5e.wikidot.com/)").internal_links, [])

    def test_scripts_are_sanitized(self):
        self.assertNotIn("<script>", render("<script>alert(1)</script>").html)


class LinkTests(TestCase):
    def test_link_creation_and_backlinks(self):
        fireball = make_page("Fireball", source_content="A bright streak.")
        make_page("Wizard", source_content="Learn [Fireball](/fireball).")
        self.assertEqual(fireball.incoming_links().count(), 1)
        self.assertEqual(fireball.incoming_links().first().source_page.title, "Wizard")

    def test_broken_link_recorded(self):
        make_page("Wizard", source_content="See [Unknown](/unknown).")
        self.assertEqual(BrokenLink.objects.count(), 1)


class ApiTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Classes")
        make_page(
            "Wizard",
            page_type=PageType.CLASS,
            source=Source.WIKIDOT,
            category=self.category,
            source_content="Wizards cast spells.",
        )
        make_page(
            "Rune Mage",
            page_type=PageType.CLASS,
            source=Source.HOMEBREW,
            category=self.category,
            source_content="Rune magic.",
        )
        make_page("Secret", visibility="gm_only")

    def test_list_pages(self):
        response = self.client.get(reverse("page-list"))
        self.assertEqual(response.status_code, 200)
        titles = {row["title"] for row in response.data["results"]}
        self.assertEqual(titles, {"Wizard", "Rune Mage"})

    def test_homebrew_listed_together_with_wikidot(self):
        response = self.client.get(reverse("page-list"), {"page_type": "class"})
        self.assertEqual(response.data["count"], 2)

    def test_changelog_filter_only_returns_pages_edited_in_the_app(self):
        changed = Page.objects.get(slug="wizard")
        changed.app_modified_at = timezone.now()
        changed.save(update_fields=["app_modified_at"])

        response = self.client.get(
            reverse("page-list"),
            {"app_modified_at__isnull": "false", "ordering": "-app_modified_at"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], "wizard")

    def test_detail_by_slug(self):
        response = self.client.get(reverse("page-detail", args=["wizard"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Wizard")

    def test_gm_only_hidden_from_anonymous(self):
        self.assertEqual(
            self.client.get(reverse("page-detail", args=["secret"])).status_code, 404
        )

    def test_gm_only_visible_to_staff(self):
        User.objects.create_superuser("gm", "gm@example.com", "pw")
        self.client.login(username="gm", password="pw")
        self.assertEqual(
            self.client.get(reverse("page-detail", args=["secret"])).status_code, 200
        )

    def test_search_endpoint(self):
        response = self.client.get(reverse("search"), {"q": "Wizards"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["title"], "Wizard")

    def test_search_filters_by_source(self):
        response = self.client.get(reverse("search"), {"q": "", "source": "homebrew"})
        self.assertEqual(response.data["count"], 1)

    def test_anonymous_cannot_create_page(self):
        response = self.client.post(
            reverse("page-list"),
            data='{"title":"Hack"}',
            content_type="application/json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_staff_can_create_page(self):
        User.objects.create_superuser("gm2", "gm2@example.com", "pw")
        self.client.login(username="gm2", password="pw")
        with patch.dict("os.environ", {"OWNER_USERNAME": "gm2"}):
            response = self.client.post(
                reverse("page-list"),
                data='{"title":"Alert","page_type":"feat","source_content":"## Benefits"}',
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn("<h2>Benefits</h2>", Page.objects.get(title="Alert").rendered_content)

    def test_navigation_endpoint(self):
        Category.objects.create(name="Spells")
        Category.objects.create(name="Locations", sidebar_group="campaign")
        response = self.client.get(reverse("navigation"))
        core = {c["name"] for c in response.data["core"]}
        campaign = {c["name"] for c in response.data["campaign"]}
        self.assertIn("Classes", core)
        self.assertIn("Locations", campaign)
        self.assertNotIn("Locations", core)

    def test_backlinks_endpoint(self):
        make_page("Fireball")
        make_page("Sorcerer", source_content="Casts [Fireball](/fireball).")
        response = self.client.get(reverse("page-backlinks", args=["fireball"]))
        self.assertEqual(len(response.data), 1)

    def test_preview_endpoint_requires_auth(self):
        response = self.client.post(
            reverse("page-preview"), data="{}", content_type="application/json"
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(render("[W](https://dnd5e.wikidot.com/)").internal_links, [])

    def test_owner_content_edit_keeps_tags_and_can_rollback(self):
        owner = User.objects.create_superuser("owner", "owner@example.com", "pw")
        page = Page.objects.get(slug="wizard")
        page.source_content = "Original"
        save_page_with_derived_data(page, ["arcane"])
        self.client.force_login(owner)
        with patch.dict("os.environ", {"OWNER_USERNAME": "owner"}):
            response = self.client.patch(
                reverse("page-content", args=["wizard"]),
                data='{"source_content":"Edited [link](https://example.com)"}',
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200, response.data)
            page.refresh_from_db()
            self.assertEqual({tag.slug for tag in page.tags.all()}, {"arcane"})
            revision = page.revisions.get()
            response = self.client.post(
                reverse("page-rollback", args=["wizard", revision.id]),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200, response.data)
        page.refresh_from_db()
        self.assertEqual(page.source_content, "Original")

    def test_scripts_are_sanitized(self):
        self.assertNotIn("<script>", render("<script>alert(1)</script>").html)
