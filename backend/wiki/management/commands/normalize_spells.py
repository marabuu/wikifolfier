"""Normalize spell metadata across all sources (Wikidot, Homebrew, Folfier).

Ensures all spells have complete structured data:
- level (int, 0-9)
- school (standard capitalized English name)
- classes (list of lowercase class slugs)
- casting_time (string)
- range (string)
- duration (string)
- components (string)

Also reclassifies Wikidot school listing pages (e.g. 'abjuration-spells') as rules.
"""
from __future__ import annotations

import re
import unicodedata
from django.core.management.base import BaseCommand
from django.db import transaction

from wiki.models import Category, Page, PageType
from wiki.services import save_page_with_derived_data
from wiki.views import SpellIndexView

SCHOOL_MAP = {
    # English
    "abjuration": "Abjuration",
    "conjuration": "Conjuration",
    "divination": "Divination",
    "enchantment": "Enchantment",
    "evocation": "Evocation",
    "illusion": "Illusion",
    "necromancy": "Necromancy",
    "transmutation": "Transmutation",
    # Portuguese / Accents
    "abjuracao": "Abjuration",
    "abjuração": "Abjuration",
    "conjuracao": "Conjuration",
    "conjuração": "Conjuration",
    "invocacao": "Conjuration",
    "invocação": "Conjuration",
    "adivinhacao": "Divination",
    "adivinhação": "Divination",
    "encantamento": "Enchantment",
    "evocacao": "Evocation",
    "evocação": "Evocation",
    "ilusao": "Illusion",
    "ilusão": "Illusion",
    "necromancia": "Necromancy",
    "transmutacao": "Transmutation",
    "transmutação": "Transmutation",
}

CLASS_SLUG_MAP = {
    # English
    "artificer": "artificer",
    "barbarian": "barbarian",
    "bard": "bard",
    "cleric": "cleric",
    "druid": "druid",
    "fighter": "fighter",
    "monk": "monk",
    "paladin": "paladin",
    "ranger": "ranger",
    "rogue": "rogue",
    "sorcerer": "sorcerer",
    "warlock": "warlock",
    "wizard": "wizard",
    "hero": "heroi",
    "magicborn": "filho-da-magia",
    "runescaper": "runescaper",
    "witcher": "witcher",
    "dovahkiin": "dovahkiin",
    # Portuguese
    "artifice": "artificer",
    "barbaro": "barbarian",
    "bardo": "bard",
    "clerigo": "cleric",
    "druida": "druid",
    "guerreiro": "fighter",
    "monge": "monk",
    "paladino": "paladin",
    "patrulheiro": "ranger",
    "cacador": "ranger",
    "ladino": "rogue",
    "feiticeiro": "sorcerer",
    "bruxo": "warlock",
    "mago": "wizard",
    "heroi": "heroi",
    "filho-da-magia": "filho-da-magia",
    "filho da magia": "filho-da-magia",
    "nascido da magia": "filho-da-magia",
    "nascido-da-magia": "filho-da-magia",
    "cacador de demonios": "cacador-de-demonios",
    "cacador-de-demonios": "cacador-de-demonios",
    "cavaleiro da morte": "cavaleiro-da-morte",
    "cavaleiro-da-morte": "cavaleiro-da-morte",
    "death knight": "cavaleiro-da-morte",
    "demon hunter": "cacador-de-demonios",
    "shaman": "xama",
    "xama": "xama",
}

# Explicit class assignments for homebrew spells imported from Azeroth/Warcraft 5e
HOMEBREW_CLASSES = {
    "acerto-concussivo": ["ranger", "rogue"],
    "acoite-mental": ["cleric", "warlock"],
    "agrilhoar-morto-vivo": ["cleric", "paladin"],
    "armadilha-congelante": ["ranger"],
    "armadilha-explosiva": ["ranger"],
    "aterramento": ["xama"],
    "avivar": ["druid"],
    "bloco-de-gelo": ["sorcerer", "wizard"],
    "bomba-viva": ["sorcerer", "wizard"],
    "calcinacao-mental": ["cleric", "warlock"],
    "caminho-de-gelo": ["cavaleiro-da-morte", "xama"],
    "chamado-ancestral": ["cleric", "druid", "xama"],
    "choque-terreno": ["xama"],
    "chuva-estelar": ["druid"],
    "comando-para-matar": ["ranger"],
    "cutilada-da-alma": ["cacador-de-demonios"],
    "danca-de-laminas": ["cacador-de-demonios"],
    "destruicao-congelante": ["cavaleiro-da-morte", "xama"],
    "escravizar-demonio": ["warlock"],
    "escudo-de-raios": ["xama"],
    "escudo-do-vingador": ["paladin"],
    "espinhos-demoniacos": ["cacador-de-demonios"],
    "espirito-da-redencao": ["cleric"],
    "espiritos-ferais": ["xama"],
    "estouro-da-manada": ["druid", "ranger"],
    "explosao-arcana": ["sorcerer", "wizard"],
    "explosao-cadaverica": ["cavaleiro-da-morte"],
}

# Known folfier schools when not mentioned in the opening lines
FOLFIER_SCHOOLS = {
    "afiamento-cortante": "Transmutation",
    "foice-gelida": "Evocation",
    "imbuir-magia": "Transmutation",
    "impacto-de-fogo": "Evocation",
    "impacto-relampejante": "Evocation",
    "power-word": "Enchantment",
    "power-word-grace": "Enchantment",
    "sopro-de-sindragosa": "Evocation",
}

WIKIDOT_SCHOOL_PAGES = {
    "abjuration-spells",
    "conjuration-spells",
    "divination-spells",
    "enchantment-spells",
    "evocation-spells",
    "illusion-spells",
    "necromancy-spells",
    "transmutation-spells",
}


def clean_ascii(s: str) -> str:
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c)).lower()


def clean_field(val: str) -> str:
    val = val.strip()
    val = re.sub(r"^[*_#:\s]+", "", val)
    val = re.sub(r"[*_#\s]+$", "", val)
    return val.strip()


def parse_spell_data(text: str, slug: str = "") -> dict:
    data: dict = {}
    norm = clean_ascii(text)

    # 1) Markdown header like *1º círculo, transmutação* or *Truque, encantamento*
    m1 = re.search(r"\*(?:(\d+)o?\s*circulo|truque)\s*,\s*([^\*]+)\*", norm)
    if m1:
        lvl = m1.group(1)
        data["level"] = int(lvl) if lvl else 0
        sch_raw = re.sub(r"\(.*?\)", "", m1.group(2)).strip()
        data["school"] = SCHOOL_MAP.get(sch_raw, sch_raw.capitalize())

    # 2) 8th-Level spell Divination, 5nd-level transmutation
    if "level" not in data:
        m2 = re.search(r"(\d+)(?:st|nd|rd|th)?-level\s+(?:spell\s+)?([a-z]+)", norm)
        if m2:
            data["level"] = int(m2.group(1))
            sch = m2.group(2).strip()
            data["school"] = SCHOOL_MAP.get(sch, sch.capitalize())

    # 3) Evocation cantrip
    if "level" not in data:
        m3 = re.search(r"([a-z]+)\s+cantrip", norm)
        if m3:
            data["level"] = 0
            sch = m3.group(1).strip()
            data["school"] = SCHOOL_MAP.get(sch, sch.capitalize())

    # 4) Cantrip alone
    if "level" not in data:
        if re.search(r"\bcantrip\b|\btruque\b", norm):
            data["level"] = 0

    # 5) Magia de 5º círculo [school]
    if "level" not in data:
        m5 = re.search(r"magia\s+de\s+(\d+)o?\s*circulo(?:\s+([a-z]+))?", norm)
        if m5:
            data["level"] = int(m5.group(1))
            if m5.group(2):
                sch = m5.group(2).strip()
                data["school"] = SCHOOL_MAP.get(sch, sch.capitalize())

    # If school still not found, check known folfier schools or look for school words
    if not data.get("school"):
        if slug in FOLFIER_SCHOOLS:
            data["school"] = FOLFIER_SCHOOLS[slug]
        else:
            for sch_k, sch_v in SCHOOL_MAP.items():
                if re.search(rf"\b{sch_k}\b", norm[:300]):
                    data["school"] = sch_v
                    break

    # Parse key-value fields
    fields_spec = [
        (r"(?:tempo de conjura[çc][ãa]o|casting time)\s*:?\*?:?\s*(.+)", "casting_time"),
        (r"(?:alcance|range)\s*:?\*?:?\s*(.+)", "range"),
        (r"(?:componentes?|components?)\s*:?\*?:?\s*(.+)", "components"),
        (r"(?:dura[çc][ãa]o|duration)\s*:?\*?:?\s*(.+)", "duration"),
        (r"(?:spell lists?|lista de magias)\s*:?\.?\*?:?\s*(.+)", "classes"),
    ]

    for pattern, key in fields_spec:
        m = re.search(rf"(?:^|[\n\r])[-#*]*\s*(?:\*\*)?{pattern}", text, re.I)
        if m:
            val = clean_field(m.group(1))
            if key == "classes":
                raw_cls = re.split(r"[,;/]", val)
                classes = []
                for c in raw_cls:
                    cleaned_c = clean_ascii(c.strip())
                    if cleaned_c in CLASS_SLUG_MAP:
                        classes.append(CLASS_SLUG_MAP[cleaned_c])
                    elif cleaned_c:
                        classes.append(cleaned_c)
                if classes:
                    data["classes"] = sorted(set(classes))
            else:
                data[key] = val

    # Fallback for homebrew classes
    if not data.get("classes") and slug in HOMEBREW_CLASSES:
        data["classes"] = HOMEBREW_CLASSES[slug]

    return data


class Command(BaseCommand):
    help = "Normalize spell metadata across all sources."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Reclassify Wikidot school pages to Rule
        rules_category, _ = Category.objects.get_or_create(
            slug="rules",
            defaults={"name": "Rules", "position": 100, "in_sidebar": True, "sidebar_group": "core"},
        )
        for slug in WIKIDOT_SCHOOL_PAGES:
            page = Page.objects.filter(slug=slug).first()
            if page:
                page.page_type = PageType.RULE
                page.category = rules_category
                save_page_with_derived_data(page)
                self.stdout.write(self.style.SUCCESS(f"Reclassificada como regra: {slug}"))

        # 2) Handle Holy Star of Mystra
        holy = Page.objects.filter(slug="holy-star-of-mystra").first()
        if holy:
            holy.structured_data = {
                "level": 7,
                "school": "Evocation",
                "classes": ["cleric", "wizard"],
                "casting_time": "1 action",
                "range": "Self",
                "components": "V, S, M (a holy symbol of Mystra)",
                "duration": "1 minute (concentration)",
                "wikidot_path": "spell:holy-star-of-mystra",
            }
            save_page_with_derived_data(holy)
            self.stdout.write(self.style.SUCCESS("Normalizada: holy-star-of-mystra"))

        # 3) Normalize all spells
        spells = Page.objects.filter(page_type=PageType.SPELL)
        updated_count = 0

        for spell in spells:
            text = spell.source_content or ""
            parsed = parse_spell_data(text, slug=spell.slug)

            sd = dict(spell.structured_data or {})
            changed = False

            # Level
            if sd.get("level") is None and "level" in parsed:
                sd["level"] = parsed["level"]
                changed = True

            # School
            school = sd.get("school")
            if not school and "school" in parsed:
                sd["school"] = parsed["school"]
                changed = True
            elif school and school.lower() in SCHOOL_MAP:
                canonical_school = SCHOOL_MAP[school.lower()]
                if school != canonical_school:
                    sd["school"] = canonical_school
                    changed = True

            # Classes
            existing_classes = sd.get("classes") or []
            if not existing_classes and "classes" in parsed:
                sd["classes"] = parsed["classes"]
                changed = True
            elif existing_classes:
                normalized_classes = []
                for c in existing_classes:
                    clean_c = clean_ascii(c)
                    normalized_classes.append(CLASS_SLUG_MAP.get(clean_c, c.lower().strip()))
                normalized_classes = sorted(set(normalized_classes))
                if normalized_classes != existing_classes:
                    sd["classes"] = normalized_classes
                    changed = True

            # Textual fields
            for key in ("casting_time", "range", "duration", "components"):
                if not sd.get(key) and key in parsed:
                    sd[key] = parsed[key]
                    changed = True

            if changed:
                spell.structured_data = sd
                save_page_with_derived_data(spell)
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Normalizada: {spell.title} ({spell.slug}) -> {sd}"))

        # Clear views cache
        SpellIndexView._cache.clear()
        SpellIndexView._cache_time.clear()

        self.stdout.write(self.style.SUCCESS(f"Concluído! {updated_count} magias atualizadas."))
