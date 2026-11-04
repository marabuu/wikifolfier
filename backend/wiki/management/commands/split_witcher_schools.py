"""Split Witcher's Escolas Witcher into linked subclass pages."""
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wiki.models import Category, Page, PageType, Source
from wiki.services import save_page_with_derived_data


PARENT_SLUG = "witcher"

SUBCLASSES = (
    (
        "Escola do Lobo",
        "witcher-escola-do-lobo",
        "Especialização em combate equilibrado.",
        """# Escola do Lobo

Ao alcançar o 3º nível, você escolhe uma escola para seguir, que representa o treinamento especializado. A Escola do Lobo é focada na especialização em combate equilibrado.

### Nível 3: Especialização da Escola do Lobo

- **Bônus em ataques com espadas:** +1 para jogadas de ataque e dano ao usar espadas longas, curtas, espadas grandes ou rapieras.
- **Reflexos aprimorados:** Adicione seu modificador de Destreza em sua CA se estiver usando armadura leve.

### Nível 10: Tática de Matilha

Você tem vantagem caso outro aliado esteja na distância de combate corpo a corpo do alvo.

### Nível 15: Mestre de Lâminas

Espadas têm o dobro de dados de dano.
""",
    ),
    (
        "Escola do Urso",
        "witcher-escola-do-urso",
        "Foco em resistência e combate de proximidade.",
        """# Escola do Urso

Ao alcançar o 3º nível, você escolhe uma escola para seguir, que representa o treinamento especializado. A Escola do Urso tem foco em resistência e combate de proximidade.

### Nível 3: Especialização da Escola do Urso

- Aumenta seu HP em +1 por nível de Witcher.
- **Armadura robusta:** Você pode usar armadura média sem perder mobilidade, sem desvantagem em Furtividade.

### Nível 10: Predador Intimidador

Escolha uma criatura por turno: esta criatura tem desvantagem para acertar ataques em qualquer um que não seja você.

### Nível 15: Força de Urso

Você tem vantagem para atacar e se defender da ação Shove (Empurrão). Além disso, você pode usar a ação Shove como ação bônus.
""",
    ),
    (
        "Escola da Víbora",
        "witcher-escola-da-vibora",
        "Especialização em ataques rápidos e venenos.",
        """# Escola da Víbora

Ao alcançar o 3º nível, você escolhe uma escola para seguir, que representa o treinamento especializado. A Escola da Víbora é especializada em ataques rápidos e venenos.

### Nível 3: Especialização da Escola da Víbora

- **Ataques precisos:** Seus acertos críticos causam +2d6 de dano de veneno (poison).
- **Resistência a veneno:** Você é imune a venenos e à condição Envenenado.

### Nível 10: Peçonhento

Seu veneno impede que seus danos de veneno e cortante sejam reduzidos de qualquer forma.

### Nível 15: Veneno Mortífero

Seus ataques básicos causam +2d6 de dano de veneno (poison).
""",
    ),
)


class Command(BaseCommand):
    help = "Move Witcher's Escolas into linked subclass pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        parent = Page.objects.filter(slug=PARENT_SLUG).first()
        category = Category.objects.filter(slug="subclasses").first()
        if not parent or not category:
            raise CommandError("Witcher ou a categoria Subclasses não foi encontrada.")

        if "(/subclasses/witcher-escola-do-lobo)" in parent.source_content and parent.child_pages.filter(slug="witcher-escola-do-lobo").exists():
            self.stdout.write(self.style.SUCCESS("As Escolas Witcher já foram separadas em subclasses."))
            return

        pattern = r'(### N[í\uFFFD]vel 3: Escolas Witcher\s*\n\s*Ao alcan[ç\uFFFD]ar o 3[º\uFFFD] n[í\uFFFD]vel[^\n]*\n)(.*?)(### N[í\uFFFD]vel 5: Ataque extra)'
        match = re.search(pattern, parent.source_content, re.DOTALL)
        if not match:
            raise CommandError("Não foi possível localizar a seção 'Escolas Witcher' na página.")

        header = match.group(1)
        next_section = match.group(3)

        links_inline = "\n".join(
            f"- [{title}](/subclasses/{slug}): {subtitle}"
            for title, slug, subtitle, _content in SUBCLASSES
        )
        links_bottom = "\n".join(
            f"- [{title}](/subclasses/{slug})"
            for title, slug, subtitle, _content in SUBCLASSES
        )

        replacement = f"{header}\n{links_inline}\n\n{next_section}"
        new_content = parent.source_content[:match.start()] + replacement + parent.source_content[match.end():]

        if "## Subclasses" not in new_content:
            new_content = new_content.rstrip() + f"\n\n## Subclasses\n\n{links_bottom}\n"

        if options["dry_run"]:
            self.stdout.write("Seriam criadas as seguintes subclasses:")
            for title, slug, subtitle, _content in SUBCLASSES:
                self.stdout.write(f"- {title} ({slug}): /subclasses/{slug}")
            return

        for title, slug, subtitle, content in SUBCLASSES:
            child, _created = Page.objects.get_or_create(slug=slug)
            child.title = title
            child.subtitle = subtitle
            child.page_type = PageType.SUBCLASS
            child.source = parent.source
            child.edition = parent.edition
            child.category = category
            child.parent_page = parent
            child.visibility = parent.visibility
            child.is_published = parent.is_published
            child.source_content = content.strip()
            save_page_with_derived_data(child)
            self.stdout.write(f"Criada/atualizada subclasse: {title} ({slug})")

        parent.source_content = new_content
        save_page_with_derived_data(parent)
        self.stdout.write(self.style.SUCCESS("Escolas Witcher separadas com sucesso em páginas de subclasse."))
