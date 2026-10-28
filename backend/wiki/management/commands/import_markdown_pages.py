"""Importa páginas de um arquivo Markdown para o banco de dados.

Cada entrada deve estar separada por um cabeçalho de nível 1 (# Nome da Página).
O conteúdo após o cabeçalho até o próximo cabeçalho # é o conteúdo da página.

Uso:
    python manage.py import_markdown_pages <caminho_arquivo.md> <page_type> [--source homebrew] [--edition D&D 2024]

Exemplos:
    python manage.py import_markdown_pages magias.md spell --source homebrew
    python manage.py import_markdown_pages classes.md class --source homebrew
"""
from __future__ import annotations

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from wiki.models import Category, Page, PageType
from wiki.services import save_page_with_derived_data


class Command(BaseCommand):
    help = "Importa páginas de um arquivo Markdown para o banco de dados."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Caminho para o arquivo .md")
        parser.add_argument(
            "page_type",
            type=str,
            help="Tipo da página (class, spell, feat, background, species, subclass, equipment, ...)",
        )
        parser.add_argument(
            "--source",
            type=str,
            default="homebrew",
            help="Valor do campo source (padrão: homebrew)",
        )
        parser.add_argument(
            "--edition",
            type=str,
            default="D&D 2024",
            help="Valor do campo edition (padrão: D&D 2024)",
        )
        parser.add_argument(
            "--header-level",
            type=int,
            default=1,
            help="Nível do cabeçalho Markdown que separa as páginas (1=#, 2=##, ... padrão: 1)",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")

        page_type = options["page_type"]
        source = options["source"]
        edition = options["edition"]
        header_level = options.get("header_level", 1)

        valid_types = {c for c, _ in PageType.choices}
        if page_type not in valid_types:
            raise CommandError(
                f"page_type inválido '{page_type}'. Valores válidos: {', '.join(sorted(valid_types))}"
            )

        text = path.read_text(encoding="utf-8")
        pages = self._split_pages(text, header_level)

        if not pages:
            self.stdout.write(self.style.WARNING("Nenhuma página encontrada no arquivo."))
            return

        category_slug = {
            "class": "classes",
            "subclass": "subclasses",
            "species": "species",
            "background": "backgrounds",
            "feat": "feats",
            "spell": "spells",
            "equipment": "equipments",
            "magic_item": "magic-items",
            "weapon": "weapons",
            "armor": "armor",
            "adventuring_gear": "adventuring-gear",
            "rule": "rules",
            "condition": "conditions",
        }.get(page_type, page_type + "s")

        category, _ = Category.objects.get_or_create(
            slug=category_slug,
            defaults={
                "name": category_slug.replace("-", " ").title(),
                "position": 100,
                "in_sidebar": True,
                "sidebar_group": "core",
            },
        )

        created = 0
        updated = 0

        for title, content in pages:
            slug = slugify(title)[:120]
            page, is_new = Page.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "subtitle": "",
                    "page_type": page_type,
                    "source": source,
                    "edition": edition,
                    "category": category,
                    "parent_page": None,
                    "source_content": content.strip(),
                    "visibility": "public",
                    "is_published": True,
                    "position": 0,
                    "structured_data": {},
                },
            )
            save_page_with_derived_data(page)
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Criada: {title}"))
            else:
                updated += 1
                self.stdout.write(self.style.HTTP_INFO(f"Atualizada: {title}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído: {created} criada(s), {updated} atualizada(s)."
            )
        )

    @staticmethod
    def _split_pages(text: str, header_level: int = 1) -> list[tuple[str, str]]:
        """Divide o markdown em páginas separadas por cabeçalho de nível N.

        Ex: header_level=1 divide por "# Nome", header_level=2 divide por "## Nome".
        """
        header_prefix = "#" * header_level + " "
        lines = text.splitlines()
        pages: list[tuple[str, str]] = []
        current_title: str | None = None
        current_lines: list[str] = []

        for line in lines:
            match = re.match(rf"^{re.escape(header_prefix)}(.+)", line)
            if match:
                if current_title is not None:
                    pages.append((current_title, "\n".join(current_lines)))
                current_title = match.group(1).strip()
                current_lines = []
            else:
                if current_title is not None:
                    current_lines.append(line)

        if current_title is not None:
            pages.append((current_title, "\n".join(current_lines)))

        return pages