"""Import a Foundry VTT compendium module as an isolated website module.

The command accepts the checked-out directory of a Foundry module.  It keeps
the original HTML in ``source_content`` and records the Foundry system data in
``structured_data`` so the import remains lossless enough for later adapters.
Creature actors, macros and roll tables are intentionally skipped because the
website has no matching page templates for them.
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from wiki.models import Category, ContentModule, Page, PageType
from wiki.services import save_page_with_derived_data


PACK_TYPES = {
    "backgrounds": "background",
    "classes": "class",
    "feats": "feat",
    "items": "equipment",
    "races": "species",
    "spells": "spell",
    "subclasses": "subclass",
    "trade-goods": "equipment",
    "background-features": "other",
    "class-features": "other",
    "racial-features": "other",
    "creature-abilities": "other",
    "journals": "rule",
}

CATEGORY_SLUGS = {
    "class": "classes", "subclass": "subclasses", "species": "species",
    "background": "backgrounds", "feat": "feats", "spell": "spells",
    "equipment": "equipment", "rule": "rules", "other": "rules",
}


class Command(BaseCommand):
    help = "Importa os compêndios .db de um módulo Foundry como módulo isolado."

    def add_arguments(self, parser):
        parser.add_argument("module_path", help="Pasta do módulo Foundry")
        parser.add_argument("--slug", default="5e-complete")
        parser.add_argument("--name", default="5e Complete Compendium")
        parser.add_argument("--module-version", dest="module_version", default="")
        parser.add_argument("--source-url", default="https://github.com/ObsidimanWizard/5e-complete")
        parser.add_argument("--replace", action="store_true", help="Remove apenas as páginas deste módulo antes de importar")

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(options["module_path"])
        packs = root / "packs"
        if not packs.is_dir():
            raise CommandError(f"Pasta de compêndios não encontrada: {packs}")

        module, _ = ContentModule.objects.update_or_create(
            slug=options["slug"],
            defaults={
                "name": options["name"],
                "version": options["module_version"],
                "source_url": options["source_url"],
                "description": "Compêndio importado do módulo Foundry VTT 5e Complete.",
                "is_enabled": True,
            },
        )
        if options["replace"]:
            Page.objects.filter(module=module).delete()

        created = updated = skipped = 0
        for db_path in sorted(packs.glob("*.db")):
            pack_name = db_path.stem.removeprefix("5e-")
            page_type = PACK_TYPES.get(pack_name)
            if not page_type:
                skipped += 1
                continue
            category = self._category(CATEGORY_SLUGS[page_type])
            for raw in db_path.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                entry = json.loads(raw)
                name = (entry.get("name") or "Sem nome").strip()
                system = entry.get("system") or {}
                html = ((system.get("description") or {}).get("value") or "").strip()
                if not html:
                    html = f"<p>{name}</p>"
                entry_id = entry.get("_id") or slugify(name)
                slug = f"{module.slug}-{slugify(pack_name)}-{slugify(name)}-{entry_id}"[:180]
                structured = {
                    "foundry_id": entry_id,
                    "foundry_pack": db_path.name,
                    "foundry_type": entry.get("type", ""),
                    "foundry_system": system,
                    "image": entry.get("img", ""),
                }
                page, is_new = Page.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title": name,
                        "page_type": page_type,
                        "source": "custom",
                        "edition": "D&D 5e",
                        "module": module,
                        "category": category,
                        "source_content": html,
                        "structured_data": structured,
                        "visibility": "public",
                        "is_published": True,
                        "position": 0,
                    },
                )
                save_page_with_derived_data(page)
                created += int(is_new)
                updated += int(not is_new)

        self.stdout.write(self.style.SUCCESS(
            f"Módulo {module.slug}: {created} criada(s), {updated} atualizada(s), {skipped} pack(s) ignorado(s)."
        ))

    @staticmethod
    def _category(slug: str):
        return Category.objects.get_or_create(
            slug=slug,
            defaults={"name": slug.replace("-", " ").title(), "sidebar_group": "core"},
        )[0]
