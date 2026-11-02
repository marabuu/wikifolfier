"""Split the Shaman's Primitive Paths (Caminhos Primitivos) into linked subclass pages."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Category, Page, PageType
from wiki.services import save_page_with_derived_data


PARENT_SLUG = "xama"
PATHS_MARKER = "\n## Caminhos Primitivos\n"
RESTAURACAO_MARKER = "\n### Caminho da Restauração\n"
APERFEICOAMENTO_MARKER = "\n### Caminho do Aperfeiçoamento\n"
ELEMENTAL_MARKER = "\n### Caminho Elemental\n"

SUBCLASSES = (
    ("Caminho da Restauração", "xama-caminho-da-restauracao"),
    ("Caminho do Aperfeiçoamento", "xama-caminho-do-aperfeicoamento"),
    ("Caminho Elemental", "xama-caminho-elemental"),
)


class Command(BaseCommand):
    help = "Move Xamã's Caminhos Primitivos into linked subclass pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        parent = Page.objects.filter(slug=PARENT_SLUG).first()
        category = Category.objects.filter(slug="subclasses").first()
        if not parent or not category:
            raise CommandError("Xamã ou a categoria Subclasses não foi encontrado.")

        if "(/subclasses/xama-caminho-da-restauracao)" in parent.source_content:
            self.stdout.write(self.style.SUCCESS("Os Caminhos Primitivos já foram separados."))
            return

        if PATHS_MARKER not in parent.source_content:
            raise CommandError("A seção 'Caminhos Primitivos' não foi encontrada na classe.")

        class_content, paths_content = parent.source_content.split(PATHS_MARKER, 1)
        markers = (RESTAURACAO_MARKER, APERFEICOAMENTO_MARKER, ELEMENTAL_MARKER)
        if any(marker not in paths_content for marker in markers):
            raise CommandError("Não foi possível encontrar os três Caminhos Primitivos.")

        introduction, rest_content = paths_content.split(RESTAURACAO_MARKER, 1)
        rest_content, aperfeicoamento_content = rest_content.split(APERFEICOAMENTO_MARKER, 1)
        aperfeicoamento_content, elemental_content = aperfeicoamento_content.split(ELEMENTAL_MARKER, 1)
        bodies = (rest_content, aperfeicoamento_content, elemental_content)

        children = tuple(
            ((title, slug), f"# {title}\n\n{introduction.strip()}\n\n{body.strip()}")
            for (title, slug), body in zip(SUBCLASSES, bodies, strict=True)
        )
        links = "\n".join(
            f"- [{title}](/subclasses/{slug})" for (title, slug), _content in children
        )

        # Update inline mention under "### Caminho Primitivo" as well
        class_content_updated = class_content.replace(
            "escolhe entre o **Caminho da Restauração**, o **Caminho do Aperfeiçoamento** ou o **Caminho Elemental**; todos detalhados ao final desta classe.",
            "escolhe entre o [Caminho da Restauração](/subclasses/xama-caminho-da-restauracao), o [Caminho do Aperfeiçoamento](/subclasses/xama-caminho-do-aperfeicoamento) ou o [Caminho Elemental](/subclasses/xama-caminho-elemental); todos detalhados ao final desta classe.",
        )

        new_parent_content = (
            class_content_updated.rstrip()
            + "\n\n## Caminhos Primitivos\n\n"
            + "No 1º nível, escolha um dos seguintes Caminhos Primitivos:\n\n"
            + links
        )

        if options["dry_run"]:
            self.stdout.write("Seriam criadas/atualizadas as subclasses:")
            for (title, slug), _content in children:
                self.stdout.write(f"- {title}: /subclasses/{slug}")
            return

        for (title, slug), content in children:
            child, _created = Page.objects.get_or_create(slug=slug)
            child.title = title
            child.page_type = PageType.SUBCLASS
            child.source = parent.source
            child.edition = parent.edition
            child.category = category
            child.parent_page = parent
            child.visibility = parent.visibility
            child.is_published = parent.is_published
            child.source_content = content
            save_page_with_derived_data(child)

        parent.source_content = new_parent_content
        save_page_with_derived_data(parent)
        self.stdout.write(self.style.SUCCESS("Caminhos Primitivos separados em três subclasses."))
