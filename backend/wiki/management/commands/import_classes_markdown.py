"""Importa classes de um arquivo Markdown para o banco de dados.

Cada classe deve estar separada por um cabeçalho de nível 1 (# Nome da Classe).
O conteúdo após o cabeçalho até o próximo cabeçalho # é o conteúdo da classe.

Uso:
    python manage.py import_classes_markdown <caminho_arquivo.md> [--source homebrew]
"""
from __future__ import annotations

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from wiki.models import Category, Page
from wiki.services import save_page_with_derived_data
from wiki.rendering import render


class Command(BaseCommand):
    help = "Importa classes de um arquivo Markdown para o banco de dados."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Caminho para o arquivo .md")
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

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")

        source = options["source"]
        edition = options["edition"]

        text = path.read_text(encoding="utf-8")
        classes = self._split_classes(text)

        if not classes:
            self.stdout.write(self.style.WARNING("Nenhuma classe encontrada no arquivo."))
            return

        category, _ = Category.objects.get_or_create(
            slug="classes",
            defaults={
                "name": "Classes",
                "position": 10,
                "in_sidebar": True,
                "sidebar_group": "core",
            },
        )

        created = 0
        updated = 0

        for title, content in classes:
            slug = slugify(title)[:120]
            page, is_new = Page.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "subtitle": "",
                    "page_type": "class",
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
    def _split_classes(text: str) -> list[tuple[str, str]]:
        """Divide o markdown em classes separadas por cabeçalho de nível 1 (# Nome)."""
        lines = text.splitlines()
        classes: list[tuple[str, str]] = []
        current_title: str | None = None
        current_lines: list[str] = []

        for line in lines:
            match = re.match(r"^#\s+(.+)", line)
            if match:
                if current_title is not None:
                    classes.append((current_title, "\n".join(current_lines)))
                current_title = match.group(1).strip()
                current_lines = []
            else:
                if current_title is not None:
                    current_lines.append(line)

        if current_title is not None:
            classes.append((current_title, "\n".join(current_lines)))

        return classes