"""Parser, filter, link and module tests. Pure unit tests, no database."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wikidot.filters import is_excluded  # noqa: E402
from wikidot.links import normalize_href, path_to_slug, resolve  # noqa: E402
from wikidot.modules import handle_module  # noqa: E402
from wikidot.parser import ParseResult, WikidotParser  # noqa: E402


class FilterTests(unittest.TestCase):
    def test_monsters_are_excluded(self):
        for path in ("creature:adult-red-dragon", "monster:goblin", "bestiary:wyrm"):
            excluded, reason = is_excluded(path, "Adult Red Dragon")
            self.assertTrue(excluded, path)
            self.assertTrue(reason)

    def test_stat_blocks_are_excluded(self):
        self.assertTrue(is_excluded("stat:commoner", "Commoner")[0])
        self.assertTrue(is_excluded("npc:shopkeeper", "Shopkeeper")[0])

    def test_stat_block_titles_are_excluded(self):
        self.assertTrue(is_excluded("page:xyz", "Appendix Z: Zombie")[0])
        self.assertTrue(is_excluded("page:abc", "Commoner (Monster)")[0])
        self.assertTrue(is_excluded("page:def", "Goblin Statblock")[0])

    def test_in_scope_pages_pass(self):
        cases = [
            ("spell:fireball", "Fireball"),
            ("wizard", "Wizard"),
            ("wizard:main", "Wizard"),
            ("wizard:evocation", "School of Evocation"),
            ("artificer:alchemist", "Alchemist"),
            ("species:elf", "Elf"),
            ("background:acolyte", "Acolyte"),
            ("feat:alert", "Alert"),
            ("magic-item:bag-of-holding", "Bag of Holding"),
            ("equipment:tool", "Tool"),
        ]
        for path, title in cases:
            excluded, reason = is_excluded(path, title)
            self.assertFalse(excluded, f"{path} should be imported ({reason})")

class ParserTests(unittest.TestCase):
    """parse() returns Markdown; parse_page() returns a full ParseResult."""

    def setUp(self):
        self.parser = WikidotParser()

    def test_headings(self):
        markdown = self.parser.parse("<h1>Fireball</h1><h2>At Higher Levels</h2>")
        self.assertIn("## At Higher Levels", markdown)

    def test_paragraphs(self):
        self.assertIn("A bright streak flashes.",
                      self.parser.parse("<p>A bright streak flashes.</p>"))

    def test_bold_and_italic(self):
        markdown = self.parser.parse("<p><b>Fire</b> and <i>cold</i></p>")
        self.assertIn("**Fire**", markdown)
        self.assertIn("*cold*", markdown)

    def test_links(self):
        result = ParseResult()
        self.parser.parse('<p><a href="/spell:magic-missile">Magic Missile</a></p>',
                          result=result)
        self.assertEqual(result.links, [("magic-missile", "Magic Missile")])

    def test_external_link_preserved(self):
        markdown = self.parser.parse('<p><a href="https://example.com/x">Out</a></p>')
        self.assertIn("(https://example.com/x)", markdown)

    def test_anchor_link_ignored(self):
        result = ParseResult()
        self.parser.parse('<p><a href="#section">Jump</a></p>', result=result)
        self.assertEqual(result.links, [])

    def test_images_collected(self):
        result = ParseResult()
        self.parser.parse('<img src="https://static.wikidot.com/a.png" alt="x">',
                          result=result)
        self.assertEqual(result.images, ["https://static.wikidot.com/a.png"])

    def test_unordered_list(self):
        markdown = self.parser.parse("<ul><li>one</li><li>two</li></ul>")
        self.assertIn("- one", markdown)
        self.assertIn("- two", markdown)

    def test_ordered_list(self):
        self.assertIn("1. first", self.parser.parse("<ol><li>first</li></ol>"))

    def test_table(self):
        markdown = self.parser.parse(
            "<table><tr><th>Level</th><th>Bonus</th></tr>"
            "<tr><td>1st</td><td>+2</td></tr></table>"
        )
        self.assertIn("| Level | Bonus |", markdown)
        self.assertIn("| --- | --- |", markdown)
        self.assertIn("| 1st | +2 |", markdown)

    def test_nested_bold_in_table(self):
        markdown = self.parser.parse(
            "<table><tr><th><b>HP</b></th></tr><tr><td>6</td></tr></table>"
        )
        self.assertIn("**HP**", markdown)

    def test_known_module_is_understood(self):
        result = ParseResult()
        markdown = self.parser.parse(
            '<div class="module-spell" data-options=\'{"castingtime":"1 action"}\'>'
            "stats</div><p>Body.</p>", result=result,
        )
        self.assertIn("**Casting Time:** 1 action", markdown)
        self.assertEqual(result.unknown_constructs, [])

    def test_unknown_construct_preserves_text(self):
        result = ParseResult()
        markdown = self.parser.parse(
            '<div class="module-whatever" data-options="{}">Keep me</div>', result=result,
        )
        self.assertIn("Keep me", markdown)
        self.assertTrue(result.unknown_constructs)

    def test_source_line_captured_and_removed(self):
        result = ParseResult()
        markdown = self.parser.parse("<p>Source: Player's Handbook</p><p>Body.</p>",
                                     result=result)
        self.assertEqual(result.source_label, "Player's Handbook")
        self.assertNotIn("Source:", markdown)

    def test_parse_page_extracts_title_and_tags(self):
        page = (
            '<div id="page-content"><p>Body text.</p></div>'
            '<div class="page-tags"><a href="/system:page-tags/tag/evocation#pages">'
            "evocation</a></div>"
            "<title>Fireball - DND 5e (2024)</title>"
        )
        result = self.parser.parse_page(page, "spell:fireball")
        self.assertEqual(result.title, "Fireball")
        self.assertEqual(result.tags, ["evocation"])
        self.assertIn("Body text.", result.markdown)


class ModuleTests(unittest.TestCase):
    def test_spell_module_parsed(self):
        options = (
            '{"castingtime":"1 action","range":"150 feet",'
            '"components":"V, S, M","duration":"Instantaneous",'
            '"classes":["Wizard","Sorcerer"]}'
        )
        result = handle_module("module-spell", options)
        self.assertTrue(result.understood)
        self.assertIn("**Casting Time:** 1 action", result.markdown)
        self.assertIn("**Range:** 150 feet", result.markdown)
        self.assertIn("**Classes:**", result.markdown)

    def test_unknown_module_flagged(self):
        result = handle_module("module-mystery", '{"a":1}')
        self.assertFalse(result.understood)
        self.assertEqual(result.name, "unknown")


class ExtractionTests(unittest.TestCase):
    """The article region must be isolated from site chrome."""

    PAGE = (
        '<div id="page-content">'
        "<p>Real content</p>"
        '<script>var $j = 1;</script>'
        '<div class="content-separator" style="display: none:"></div>'
        "<p>More content</p>"
        "</div>"
        '<div id="action-area"><a href="#">toolbar</a></div>'
        '<div class="page-tags"><a href="/system:page-tags/tag/evocation#pages">evocation</a></div>'
        "<title>Fireball - DND 5e (2024)</title>"
    )

    def test_content_isolated_from_chrome(self):
        from wikidot.extract import extract_article

        article = extract_article(self.PAGE)
        self.assertIn("Real content", article)
        self.assertIn("More content", article)
        self.assertNotIn("toolbar", article)
        self.assertNotIn("page-tags", article)

    def test_scripts_removed(self):
        from wikidot.extract import extract_article

        self.assertNotIn("$j", extract_article(self.PAGE))

    def test_separator_divs_removed(self):
        from wikidot.extract import extract_article

        self.assertNotIn("content-separator", extract_article(self.PAGE))

    def test_title_strips_site_suffix(self):
        from wikidot.extract import extract_title

        self.assertEqual(extract_title(self.PAGE), "Fireball")

    def test_tags_extracted(self):
        from wikidot.extract import extract_tags

        self.assertEqual(extract_tags(self.PAGE), ["evocation"])

    def test_missing_container_returns_empty(self):
        from wikidot.extract import extract_article

        self.assertEqual(extract_article("<html><body>nope</body></html>"), "")


class ScopeMappingTests(unittest.TestCase):
    """Namespace -> PageType, verified against real 2024 wiki paths."""

    def test_class_landing_pages(self):
        from wikidot.filters import page_type_for

        self.assertEqual(page_type_for("wizard"), "class")
        self.assertEqual(page_type_for("wizard:main"), "class")

    def test_subclasses(self):
        from wikidot.filters import page_type_for

        self.assertEqual(page_type_for("artificer:alchemist"), "subclass")
        self.assertEqual(page_type_for("wizard:evocation"), "subclass")

    def test_core_types(self):
        from wikidot.filters import page_type_for

        cases = {
            "spell:fireball": "spell",
            "feat:alert": "feat",
            "background:acolyte": "background",
            "species:elf": "species",
            "magic-item:bag-of-holding": "magic_item",
            "equipment:tool": "equipment",
        }
        for path, expected in cases.items():
            self.assertEqual(page_type_for(path), expected, path)

    def test_monsters_never_imported(self):
        from wikidot.filters import is_excluded

        for path in ("creature:dragon", "monster:goblin", "stat:commoner",
                     "bestiary:wyrm", "encounter:cave"):
            self.assertTrue(is_excluded(path)[0], path)

    def test_creature_titles_rejected(self):
        from wikidot.filters import is_excluded

        self.assertTrue(is_excluded("spell:x", "Goblin Statblock")[0])
        self.assertTrue(is_excluded("spell:y", "Appendix Z: Zombie")[0])
        self.assertTrue(is_excluded("spell:z", "Commoner (Monster)")[0])

    def test_chrome_rejected(self):
        from wikidot.filters import is_excluded

class StructuredDataTests(unittest.TestCase):
    """Spell and item headers, in both the 2024 and 2014 layouts."""

    def test_spell_2024_header(self):
        from wikidot.converter import Converter
        from wikidot.parser import ParseResult

        parsed = ParseResult(
            markdown="*Level 3 Evocation (Sorcerer, Wizard)*\n\n"
                     "**Casting Time:** Action\n\n**Range:** 150 feet\n\n"
                     "**Components:** V, S, M (a ball of bat guano and sulfur)\n\n"
                     "**Duration:** Instantaneous\n\nA bright streak flashes."
        )
        data = Converter._spell_data(parsed)
        self.assertEqual(data["level"], 3)
        self.assertEqual(data["school"], "Evocation")
        self.assertEqual(data["range"], "150 feet")
        self.assertEqual(data["components"], "V, S, M (a ball of bat guano and sulfur)")
        self.assertEqual(data["duration"], "Instantaneous")
        self.assertEqual(data["casting_time"], "Action")

    def test_cantrip_header(self):
        from wikidot.converter import Converter
        from wikidot.parser import ParseResult

        parsed = ParseResult(markdown="*Evocation Cantrip (Warlock)*\n\nYou hurl a beam.")
        data = Converter._spell_data(parsed)
        self.assertEqual(data["level"], 0)
        self.assertEqual(data["school"], "Evocation")

    def test_spell_2014_header(self):
        from wikidot.converter import Converter
        from wikidot.parser import ParseResult

        parsed = ParseResult(
            markdown="*3rd-level evocation*\n\n**Casting Time:** 1 action\n\n"
                     "**Range:** 150 feet\n\nA bright streak flashes."
        )
        data = Converter._spell_data(parsed)
        self.assertEqual(data["level"], 3)
        self.assertEqual(data["school"], "Evocation")

    def test_magic_item_header(self):
        from wikidot.converter import Converter
        from wikidot.parser import ParseResult

        parsed = ParseResult(markdown="*Wondrous Item, Uncommon*\n\nThis bag has an interior.")
        data = Converter._item_data(parsed)
        self.assertEqual(data["rarity"], "Uncommon")
        self.assertEqual(data["item_type"], "Wondrous Item")


class MarkdownIntegrityTests(unittest.TestCase):
    def test_emphasis_is_not_destroyed(self):
        """'*italic*' + newline + '**bold**' must survive untouched."""
        from wikidot.parser import WikidotParser

        html = "<p><em>Level 3 Evocation</em></p><p><strong>Range:</strong> 150 feet</p>"
        markdown = WikidotParser().parse(html)
        self.assertIn("*Level 3 Evocation*", markdown)
        self.assertIn("**Range:**", markdown)
        self.assertNotIn("Evocation**Range", markdown)

    def test_no_html_leaks_into_markdown(self):
        from wikidot.parser import WikidotParser

        html = '<p>Text with <strong>bold</strong> and <a href="/spell:x">link</a></p>'
        markdown = WikidotParser().parse(html)
        self.assertNotIn("<strong>", markdown)
        self.assertNotIn("<p>", markdown)


    def test_normalize_absolute_wikidot(self):
        self.assertEqual(
            normalize_href("https://dnd5e.wikidot.com/spell:fireball"), "spell:fireball"
        )

    def test_normalize_relative(self):
        self.assertEqual(normalize_href("/spell:fireball"), "spell:fireball")

    def test_external_rejected(self):
        self.assertIsNone(normalize_href("https://example.com/x"))

    def test_anchor_rejected(self):
        self.assertIsNone(normalize_href("#top"))

    def test_path_to_slug(self):
        self.assertEqual(path_to_slug("spell:magic-missile"), "magic-missile")

    def test_resolve_relative_same_namespace(self):
        self.assertEqual(resolve("spell:fireball", "/fireball"), "fireball")


if __name__ == "__main__":
    unittest.main(verbosity=2)
    def test_rules_pages_pass(self):
        self.assertFalse(is_excluded("page:conditions", "Conditions")[0])
        self.assertFalse(is_excluded("page:combat", "Combat")[0])

    def test_unknown_namespace_is_skipped(self):
        self.assertTrue(is_excluded("some-random-ns:thing", "Thing")[0])
