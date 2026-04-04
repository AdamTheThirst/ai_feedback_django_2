# Generated manually for iteration 2 bootstrap schema.

import django.db.models.deletion
import django.db.models.functions.datetime
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    """Создаёт базовую таблицу запусков анализа для V1."""

    initial = True

    dependencies = [
        ("dialogs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ожидает запуска"),
                            ("running", "Выполняется"),
                            ("completed", "Завершён успешно"),
                            ("failed", "Завершён с ошибкой"),
                            ("skipped", "Пропущен"),
                        ],
                        default="pending",
                        max_length=16,
                        verbose_name="Статус анализа",
                    ),
                ),
                ("started_at", models.DateTimeField(default=django.db.models.functions.datetime.Now, verbose_name="Запущен")),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="Завершён")),
                ("llm_attempt_count", models.PositiveIntegerField(default=0, verbose_name="Число попыток LLM")),
                ("error_code", models.CharField(blank=True, max_length=64, verbose_name="Код ошибки")),
                ("error_message", models.TextField(blank=True, verbose_name="Описание ошибки")),
                (
                    "dialog",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_run",
                        to="dialogs.dialogsession",
                        verbose_name="Диалог",
                    ),
                ),
            ],
            options={
                "verbose_name": "Запуск анализа",
                "verbose_name_plural": "Запуски анализа",
                "indexes": [
                    models.Index(fields=["status"], name="idx_analysis_status"),
                    models.Index(fields=["started_at"], name="idx_analysis_started_at"),
                ],
            },
        ),
    ]
