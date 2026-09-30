"""Parser, filter, link and module tests. Pure unit tests, no database."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wikidot.filters import is_excluded  # noqa: E402
from wikidot.links import normalize_href, path_to_slug, resolve  # noqa: E402
from wikidot.modules import handle_module  # noqa: E402
from wikidot.parser import WikidotParser  # noqa: E402


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
            ("class:wizard", "Wizard"),
            ("subclass:evocation", "Evocation"),
            ("species:elf", "Elf"),
            ("background:acolyte", "Acolyte"),
            ("feat:alert", "Alert"),
            ("item:bag-of-holding", "Bag of Holding"),
            ("weapon:longsword", "Longsword"),
            ("armor:chain-mail", "Chain Mail"),
        ]
        for path, title in cases:
            excluded, reason = is_excluded(path, title)
            self.assertFalse(excluded, f"{path} should be imported ({reason})")

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = WikidotParser()

    def test_headings(self):
        result = self.parser.parse("<h1>Fireball</h1><h2>At Higher Levels</h2>")
        self.assertIn("## At Higher Levels", result.markdown)

    def test_paragraphs(self):
        result = self.parser.parse("<p>A bright streak flashes.</p>")
        self.assertIn("A bright streak flashes.", result.markdown)

    def test_bold_and_italic(self):
        result = self.parser.parse("<p><b>Fire</b> and <i>cold</i></p>")
        self.assertIn("**Fire**", result.markdown)
        self.assertIn("*cold*", result.markdown)

    def test_links(self):
        html = '<a href="/spell:magic-missile">Magic Missile</a>'
        result = self.parser.parse(f"<p>{html}</p>")
        self.assertIn("[Magic Missile](/magic-missile)", result.markdown)
        self.assertEqual(result.links, [("magic-missile", "Magic Missile")])

    def test_external_link_preserved(self):
        html = '<a href="https://example.com/x">Outside</a>'
        result = self.parser.parse(f"<p>{html}</p>")
        self.assertIn("(https://example.com/x)", result.markdown)
        self.assertEqual(result.links, [])

    def test_anchor_link_ignored(self):
        result = self.parser.parse('<p><a href="#section">Jump</a></p>')
        self.assertEqual(result.links, [])

    def test_images_collected(self):
        html = '<img src="https://static.wikidot.com/a.png" alt="x">'
        result = self.parser.parse(html)
        self.assertEqual(result.images, ["https://static.wikidot.com/a.png"])
        self.assertIn("![a.png]", result.markdown)

    def test_unordered_list(self):
        result = self.parser.parse("<ul><li>one</li><li>two</li></ul>")
        self.assertIn("- one", result.markdown)
        self.assertIn("- two", result.markdown)

    def test_ordered_list(self):
        result = self.parser.parse("<ol><li>first</li><li>second</li></ol>")
        self.assertIn("1. first", result.markdown)

    def test_table(self):
        html = """
        <table>
          <tr><th>Level</th><th>Bonus</th></tr>
          <tr><td>1st</td><td>+2</td></tr>
        </table>
        """
        result = self.parser.parse(html)
        self.assertIn("| Level | Bonus |", result.markdown)
        self.assertIn("| --- | --- |", result.markdown)
        self.assertIn("| 1st | +2 |", result.markdown)

    def test_nested_bold_in_table(self):
        html = "<table><tr><th><b>HP</b></th></tr><tr><td>6</td></tr></table>"
        result = self.parser.parse(html)
        self.assertIn("**HP**", result.markdown)

    def test_module_is_reported_not_dropped(self):
        html = (
            '<div class="module-spell" data-options=\'{"castingtime":"1 action"}\'>'
            "Spell stats</div><p>Body text.</p>"
        )
        result = self.parser.parse(html)
        self.assertIn("**Casting Time:** 1 action", result.markdown)
        self.assertIn("Body text.", result.markdown)
        self.assertEqual(result.unknown_constructs, [])

    def test_unknown_construct_preserves_text(self):
        html = '<div class="module-whatever" data-options="{}">Keep me</div>'
        result = self.parser.parse(html)
        self.assertIn("Keep me", result.markdown)
        self.assertTrue(result.unknown_constructs)

    def test_subtitle_extracted_from_caption(self):
        html = (
            '<h1>Wizard</h1>'
            '<div class="page-title"><div class="caption">Wizards are magic-users</div></div>'
        )
        result = self.parser.parse(html)
        self.assertEqual(result.subtitle, "Wizards are magic-users")

    def test_source_label_extracted(self):
        result = self.parser.parse("<p>Source: Player's Handbook</p>")
        self.assertEqual(result.source_label, "Player's Handbook")


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


class LinkTests(unittest.TestCase):
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