from django.db import migrations


def move_homebrew_class_spell_lists(apps, schema_editor):
    Page = apps.get_model("wiki", "Page")
    Category = apps.get_model("wiki", "Category")

    subclasses = Category.objects.filter(slug="subclasses").first()
    if subclasses is None:
        return

    pages = Page.objects.filter(
        source__in=("homebrew", "folfier"),
        page_type="spell",
        parent_page__isnull=False,
        title__iendswith=" Spell List",
    ).select_related("parent_page")

    for page in pages:
        if page.parent_page.page_type != "class":
            continue
        page.page_type = "subclass"
        page.category_id = subclasses.pk
        page.subcategory_id = None
        page.save(update_fields=["page_type", "category", "subcategory"])


def restore_homebrew_class_spell_lists(apps, schema_editor):
    Page = apps.get_model("wiki", "Page")
    Category = apps.get_model("wiki", "Category")

    spells = Category.objects.filter(slug="spells").first()
    if spells is None:
        return

    pages = Page.objects.filter(
        source__in=("homebrew", "folfier"),
        page_type="subclass",
        parent_page__isnull=False,
        title__iendswith=" Spell List",
    ).select_related("parent_page")

    for page in pages:
        if page.parent_page.page_type != "class":
            continue
        page.page_type = "spell"
        page.category_id = spells.pk
        page.save(update_fields=["page_type", "category"])


class Migration(migrations.Migration):
    dependencies = [("wiki", "0002_page_subcategory")]

    operations = [
        migrations.RunPython(
            move_homebrew_class_spell_lists,
            restore_homebrew_class_spell_lists,
        ),
    ]
