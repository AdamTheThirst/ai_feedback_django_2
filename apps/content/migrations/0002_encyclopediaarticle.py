# Generated manually for iteration 11 encyclopedia.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Создаёт таблицу статей энциклопедии."""

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EncyclopediaArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("title", models.CharField(max_length=128, verbose_name="Заголовок")),
                ("slug", models.SlugField(max_length=180, unique=True, verbose_name="Slug")),
                ("body", models.TextField(max_length=5000, verbose_name="Текст статьи")),
                ("summary", models.CharField(max_length=255, verbose_name="Краткое описание")),
                ("is_published", models.BooleanField(default=False, verbose_name="Опубликовано")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="encyclopedia_articles_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создал",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="encyclopedia_articles_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Обновил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Статья энциклопедии",
                "verbose_name_plural": "Статьи энциклопедии",
                "indexes": [models.Index(fields=["is_published", "title"], name="idx_encyclopedia_pub_title")],
            },
        )
    ]
