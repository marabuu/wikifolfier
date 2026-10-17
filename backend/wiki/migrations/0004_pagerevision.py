# Generated manually for the in-app content revision history.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wiki", "0003_normalize_homebrew_class_spell_lists"),
    ]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="source",
            field=models.CharField(
                choices=[
                    ("official", "Official"), ("wikidot", "Wikidot"),
                    ("homebrew", "Homebrew"), ("campaign", "Campaign"),
                    ("custom", "Custom"), ("folfier", "Folfier"),
                ],
                db_index=True,
                default="custom",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="PageRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("status", models.CharField(default="saved", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="page_revisions", to=settings.AUTH_USER_MODEL)),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="revisions", to="wiki.page")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
