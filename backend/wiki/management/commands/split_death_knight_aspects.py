"""Split the Death Knight's Aspects of Death into linked subclass pages."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Category, Page, PageType
from wiki.services import save_page_with_derived_data


PARENT_SLUG = "cavaleiro-da-morte"
ASPECTS_MARKER = "\n## Aspectos da Morte\n"
FROST_MARKER = "\n### Morte Congelante\n"
CORRUPTION_MARKER = "\n### Morte Corruptora\n"
BLOOD_MARKER = "\n### Morte Sangrenta\n"

SUBCLASSES = (
    ("Morte Congelante", "cavaleiro-da-morte-morte-congelante"),
    ("Morte Corruptora", "cavaleiro-da-morte-morte-corruptora"),
    ("Morte Sangrenta", "cavaleiro-da-morte-morte-sangrenta"),
)


class Command(BaseCommand):
    help = "Move Cavaleiro da Morte's Aspectos da Morte into linked subclass pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        parent = Page.objects.filter(slug=PARENT_SLUG).first()
        category = Category.objects.filter(slug="subclasses").first()
        if not parent or not category:
            raise CommandError("Cavaleiro da Morte ou a categoria Subclasses não foi encontrado.")

        if "(/subclasses/cavaleiro-da-morte-morte-congelante)" in parent.source_content:
            self.stdout.write(self.style.SUCCESS("Os Aspectos da Morte já foram separados."))
            return

        if ASPECTS_MARKER not in parent.source_content:
            raise CommandError("A seção 'Aspectos da Morte' não foi encontrada na classe.")

        class_content, aspects_content = parent.source_content.split(ASPECTS_MARKER, 1)
        markers = (FROST_MARKER, CORRUPTION_MARKER, BLOOD_MARKER)
        if any(marker not in aspects_content for marker in markers):
            raise CommandError("Não foi possível encontrar os três Aspectos da Morte.")

        introduction, frost_content = aspects_content.split(FROST_MARKER, 1)
        frost_content, corruption_content = frost_content.split(CORRUPTION_MARKER, 1)
        corruption_content, blood_content = corruption_content.split(BLOOD_MARKER, 1)
        bodies = (frost_content, corruption_content, blood_content)
        children = tuple(
            ((title, slug), f"# {title}\n\n{introduction.strip()}\n\n{body.strip()}")
            for (title, slug), body in zip(SUBCLASSES, bodies, strict=True)
        )
        links = "\n".join(
            f"- [{title}](/subclasses/{slug})" for (title, slug), _content in children
        )
        new_parent_content = (
            class_content.rstrip()
            + "\n\n## Aspectos da Morte\n\n"
            + "No 3º nível, escolha um dos seguintes Aspectos da Morte:\n\n"
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
        self.stdout.write(self.style.SUCCESS("Aspectos da Morte separados em três subclasses."))
