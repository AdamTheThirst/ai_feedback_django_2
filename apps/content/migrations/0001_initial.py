# Generated manually for iteration 4 content domain schema.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    """Создаёт контентные таблицы игр, сценариев, промтов и медиа."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Game",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("slug", models.SlugField(max_length=120, unique=True, verbose_name="Slug")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("short_description", models.TextField(blank=True, verbose_name="Краткое описание")),
                ("sort_order", models.PositiveIntegerField(default=100, verbose_name="Порядок")),
                ("is_published", models.BooleanField(default=True, verbose_name="Опубликована")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_game_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
            ],
            options={
                "verbose_name": "Игра",
                "verbose_name_plural": "Игры",
                "ordering": ["sort_order", "title"],
                "indexes": [models.Index(fields=["is_published", "is_archived", "sort_order"], name="idx_game_public_order")],
            },
        ),
        migrations.CreateModel(
            name="ScenarioMediaAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("title", models.CharField(max_length=255, verbose_name="Название файла")),
                ("file", models.FileField(upload_to="scenario_media/", verbose_name="Файл")),
                ("original_filename", models.CharField(blank=True, max_length=255, verbose_name="Исходное имя")),
                ("mime_type", models.CharField(blank=True, max_length=100, verbose_name="MIME-тип")),
                ("file_size_bytes", models.BigIntegerField(blank=True, null=True, verbose_name="Размер, байт")),
                ("checksum_sha256", models.CharField(blank=True, max_length=64, verbose_name="SHA256")),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="uploaded_media_assets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Загрузил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Медиа-ресурс сценария",
                "verbose_name_plural": "Медиа-ресурсы сценариев",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SystemPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("key", models.SlugField(max_length=120, unique=True, verbose_name="Ключ")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("prompt_text", models.TextField(verbose_name="Текст системного промта")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активный")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_systemprompt_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
            ],
            options={
                "verbose_name": "Системный промт",
                "verbose_name_plural": "Системные промты",
            },
        ),
        migrations.CreateModel(
            name="Scenario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("slug", models.SlugField(max_length=120, verbose_name="Slug")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("short_description", models.TextField(blank=True, verbose_name="Краткое описание")),
                ("conditions_text", models.TextField(verbose_name="Условия сценария")),
                ("opening_message_text", models.TextField(verbose_name="Стартовое сообщение персонажа")),
                ("sort_order", models.PositiveIntegerField(default=100, verbose_name="Порядок")),
                ("is_published", models.BooleanField(default=True, verbose_name="Опубликован")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_scenario_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenarios",
                        to="content.game",
                        verbose_name="Игра",
                    ),
                ),
                (
                    "media_asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scenarios",
                        to="content.scenariomediaasset",
                        verbose_name="Медиа-ресурс",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сценарий",
                "verbose_name_plural": "Сценарии",
                "ordering": ["game", "sort_order", "title"],
                "indexes": [models.Index(fields=["game", "is_published", "is_archived"], name="idx_scenario_game_public")],
            },
        ),
        migrations.CreateModel(
            name="AnalysisPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("alias", models.SlugField(max_length=120, verbose_name="Alias")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("header_text", models.CharField(max_length=255, verbose_name="Заголовок карточки")),
                ("comment_text", models.TextField(blank=True, verbose_name="Комментарий")),
                ("prompt_text", models.TextField(verbose_name="Текст аналитического промта")),
                ("sort_order", models.PositiveIntegerField(default=100, verbose_name="Порядок")),
                ("min_rating", models.SmallIntegerField(default=0, verbose_name="Минимальный балл")),
                ("max_rating", models.SmallIntegerField(default=5, verbose_name="Максимальный балл")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активный")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_analysisprompt_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_prompts",
                        to="content.game",
                        verbose_name="Игра",
                    ),
                ),
            ],
            options={
                "verbose_name": "Аналитический промт",
                "verbose_name_plural": "Аналитические промты",
                "ordering": ["game", "sort_order"],
            },
        ),
        migrations.CreateModel(
            name="ScenarioPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="В архиве")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивировано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("title", models.CharField(max_length=255, verbose_name="Название версии")),
                ("prompt_text", models.TextField(verbose_name="Текст промта")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активный")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_scenarioprompt_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
                (
                    "scenario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scenario_prompts",
                        to="content.scenario",
                        verbose_name="Сценарий",
                    ),
                ),
            ],
            options={
                "verbose_name": "Игровой промт",
                "verbose_name_plural": "Игровые промты",
            },
        ),
        migrations.AddField(
            model_name="scenariomediaasset",
            name="previous_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="next_versions",
                to="content.scenariomediaasset",
                verbose_name="Предыдущая версия",
            ),
        ),
        migrations.AddConstraint(
            model_name="analysisprompt",
            constraint=models.UniqueConstraint(fields=("game", "alias"), name="uniq_analysis_alias_in_game"),
        ),
        migrations.AddConstraint(
            model_name="analysisprompt",
            constraint=models.UniqueConstraint(fields=("game", "sort_order"), name="uniq_analysis_sort_in_game"),
        ),
        migrations.AddConstraint(
            model_name="scenario",
            constraint=models.UniqueConstraint(fields=("game", "slug"), name="uniq_scenario_slug_in_game"),
        ),
        migrations.AddConstraint(
            model_name="scenario",
            constraint=models.UniqueConstraint(fields=("game", "sort_order"), name="uniq_scenario_sort_in_game"),
        ),
        migrations.AddConstraint(
            model_name="scenarioprompt",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("scenario",),
                name="uniq_active_prompt_per_scenario",
            ),
        ),
    ]
