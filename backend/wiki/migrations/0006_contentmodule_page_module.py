from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wiki", "0005_page_app_modified_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentModule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("source_url", models.URLField(blank=True)),
                ("version", models.CharField(blank=True, max_length=40)),
                ("is_enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="page",
            name="module",
            field=models.ForeignKey(blank=True, help_text="Optional isolated compendium module.", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pages", to="wiki.contentmodule"),
        ),
    ]
