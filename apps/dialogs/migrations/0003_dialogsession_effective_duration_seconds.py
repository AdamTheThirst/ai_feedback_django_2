# Generated manually for iteration 7 timer support.

from django.db import migrations, models


class Migration(migrations.Migration):
    """Добавляет зафиксированную длительность таймера в DialogSession."""

    dependencies = [
        ("dialogs", "0002_dialog_chat_runtime"),
    ]

    operations = [
        migrations.AddField(
            model_name="dialogsession",
            name="effective_duration_seconds",
            field=models.PositiveIntegerField(default=600, verbose_name="Эффективная длительность, сек"),
        ),
    ]
