"""Split the Demon Hunter's Fel Secrets into linked subclass pages."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Category, Page, PageType
from wiki.services import save_page_with_derived_data


PARENT_SLUG = "cacador-de-demonios"
SECRETS_MARKER = "\n## Segredos Vis\n"
DEVASTATION_MARKER = "\n### Devastação\n"
VENGEANCE_MARKER = "\n### Vingança\n"

SUBCLASSES = (
    ("Devastação", "cacador-de-demonios-devastacao"),
    ("Vingança", "cacador-de-demonios-vinganca"),
)


class Command(BaseCommand):
    help = "Move Caçador de Demônios' Segredos Vis into linked subclass pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        parent = Page.objects.filter(slug=PARENT_SLUG).first()
        category = Category.objects.filter(slug="subclasses").first()
        if not parent or not category:
            raise CommandError("Caçador de Demônios ou a categoria Subclasses não foi encontrado.")

        if "(/subclasses/cacador-de-demonios-devastacao)" in parent.source_content:
            self.stdout.write(self.style.SUCCESS("Os Segredos Vis já foram separados."))
            return

        if SECRETS_MARKER not in parent.source_content:
            raise CommandError("A seção 'Segredos Vis' não foi encontrada na classe.")

        class_content, secrets_content = parent.source_content.split(SECRETS_MARKER, 1)
        if DEVASTATION_MARKER not in secrets_content or VENGEANCE_MARKER not in secrets_content:
            raise CommandError("Não foi possível encontrar Devastação e Vingança nos Segredos Vis.")

        introduction, devastation_content = secrets_content.split(DEVASTATION_MARKER, 1)
        devastation_content, vengeance_content = devastation_content.split(VENGEANCE_MARKER, 1)

        children = (
            (SUBCLASSES[0], f"# Devastação\n\n{introduction.strip()}\n\n{devastation_content.strip()}"),
            (SUBCLASSES[1], f"# Vingança\n\n{introduction.strip()}\n\n{vengeance_content.strip()}"),
        )
        links = "\n".join(
            f"- [{title}](/subclasses/{slug})" for (title, slug), _content in children
        )
        new_parent_content = (
            class_content.rstrip()
            + "\n\n## Segredos Vis\n\n"
            + "No 3º nível, escolha um dos seguintes Segredos Vis:\n\n"
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
        self.stdout.write(self.style.SUCCESS("Segredos Vis separados em Devastação e Vingança."))
