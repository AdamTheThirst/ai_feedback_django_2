# Generated manually for iteration 8 analytics audit log.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """Создаёт таблицу AuditLogEntry для технических событий."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("analysis", "0002_analysisresult"),
        ("dialogs", "0003_dialogsession_effective_duration_seconds"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Создано")),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("debug", "Debug"),
                            ("info", "Info"),
                            ("warning", "Warning"),
                            ("error", "Error"),
                            ("critical", "Critical"),
                        ],
                        default="info",
                        max_length=16,
                        verbose_name="Уровень",
                    ),
                ),
                ("event_type", models.CharField(max_length=128, verbose_name="Тип события")),
                ("message", models.TextField(verbose_name="Сообщение")),
                ("object_type", models.CharField(blank=True, max_length=128, verbose_name="Тип объекта")),
                ("object_id", models.CharField(blank=True, max_length=128, verbose_name="ID объекта")),
                ("context_json", models.JSONField(blank=True, null=True, verbose_name="Контекст JSON")),
                ("traceback_text", models.TextField(blank=True, verbose_name="Трассировка")),
                (
                    "actor_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_log_entries",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь-инициатор",
                    ),
                ),
                (
                    "analysis_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_log_entries",
                        to="analysis.analysisrun",
                        verbose_name="Запуск анализа",
                    ),
                ),
                (
                    "dialog",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_log_entries",
                        to="dialogs.dialogsession",
                        verbose_name="Диалог",
                    ),
                ),
            ],
            options={
                "verbose_name": "Запись audit log",
                "verbose_name_plural": "Записи audit log",
                "ordering": ["-created_at", "-id"],
                "indexes": [
                    models.Index(fields=["level", "created_at"], name="idx_audit_level_created"),
                    models.Index(fields=["event_type", "created_at"], name="idx_audit_event_created"),
                ],
            },
        )
    ]
