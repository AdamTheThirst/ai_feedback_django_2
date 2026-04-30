# Generated manually for iteration 6 dialog lifecycle runtime.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Расширяет DialogSession и создаёт таблицу сообщений диалога."""

    dependencies = [
        ("content", "0001_initial"),
        ("dialogs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dialogsession",
            name="conditions_snapshot_text",
            field=models.TextField(blank=True, verbose_name="Снимок условий"),
        ),
        migrations.AddField(
            model_name="dialogsession",
            name="opening_message_snapshot_text",
            field=models.TextField(blank=True, verbose_name="Снимок стартового сообщения"),
        ),
        migrations.AddField(
            model_name="dialogsession",
            name="pending_response",
            field=models.BooleanField(default=False, verbose_name="Ожидание ответа ассистента"),
        ),
        migrations.AddField(
            model_name="dialogsession",
            name="game",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dialog_sessions",
                to="content.game",
                verbose_name="Игра",
            ),
        ),
        migrations.AddField(
            model_name="dialogsession",
            name="scenario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dialog_sessions",
                to="content.scenario",
                verbose_name="Сценарий",
            ),
        ),
        migrations.AddField(
            model_name="dialogsession",
            name="scenario_prompt_used",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dialog_sessions",
                to="content.scenarioprompt",
                verbose_name="Использованный промт",
            ),
        ),
        migrations.CreateModel(
            name="DialogMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence_no", models.PositiveIntegerField(verbose_name="Порядковый номер")),
                (
                    "role",
                    models.CharField(
                        choices=[("assistant", "Ассистент"), ("user", "Пользователь")],
                        max_length=16,
                        verbose_name="Роль",
                    ),
                ),
                ("text", models.TextField(verbose_name="Текст")),
                ("char_count", models.PositiveIntegerField(verbose_name="Количество символов")),
                ("client_message_id", models.UUIDField(blank=True, null=True, verbose_name="Клиентский ID сообщения")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Создано")),
                (
                    "dialog",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="dialogs.dialogsession",
                        verbose_name="Диалог",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сообщение диалога",
                "verbose_name_plural": "Сообщения диалога",
                "ordering": ["sequence_no", "id"],
                "indexes": [models.Index(fields=["dialog", "created_at"], name="idx_dialog_message_created")],
            },
        ),
        migrations.AddConstraint(
            model_name="dialogmessage",
            constraint=models.UniqueConstraint(fields=("dialog", "sequence_no"), name="uniq_dialog_message_seq"),
        ),
        migrations.AddConstraint(
            model_name="dialogmessage",
            constraint=models.UniqueConstraint(
                condition=models.Q(("client_message_id__isnull", False)),
                fields=("dialog", "client_message_id"),
                name="uniq_dialog_client_message_id",
            ),
        ),
    ]
