# Generated manually for iteration 2 bootstrap schema.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.datetime
import uuid


class Migration(migrations.Migration):
    """Создаёт базовую таблицу жизненного цикла диалогов для V1."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DialogSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Активен"),
                            ("finished", "Завершён"),
                            ("aborted", "Прерван"),
                            ("analysis_skipped", "Анализ пропущен"),
                        ],
                        default="active",
                        max_length=32,
                        verbose_name="Статус диалога",
                    ),
                ),
                (
                    "ended_reason",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("manual_feedback", "Кнопка обратной связи"),
                            ("timeout", "Таймер истёк"),
                            ("page_leave", "Покинул страницу"),
                            ("inactive_timeout", "Серверный таймаут неактивности"),
                            ("no_user_messages", "Нет пользовательских реплик"),
                        ],
                        max_length=32,
                        verbose_name="Причина завершения",
                    ),
                ),
                ("started_at", models.DateTimeField(default=django.db.models.functions.datetime.Now, verbose_name="Начат")),
                ("ended_at", models.DateTimeField(blank=True, null=True, verbose_name="Завершён")),
                ("user_message_count", models.PositiveIntegerField(default=0, verbose_name="Сообщений пользователя")),
                ("assistant_message_count", models.PositiveIntegerField(default=0, verbose_name="Сообщений ассистента")),
                (
                    "last_client_activity_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Последняя клиентская активность"),
                ),
                ("client_aborted_at", models.DateTimeField(blank=True, null=True, verbose_name="Время клиентского прерывания")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dialog_sessions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Диалоговая сессия",
                "verbose_name_plural": "Диалоговые сессии",
                "indexes": [
                    models.Index(fields=["user", "status"], name="idx_dialog_user_status"),
                    models.Index(fields=["started_at"], name="idx_dialog_started_at"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="dialogsession",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("user",),
                name="uniq_active_dialog_per_user",
            ),
        ),
    ]
