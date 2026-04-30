# Generated manually for iteration 12 personal timer.

from django.db import migrations, models


class Migration(migrations.Migration):
    """Добавляет персональную настройку длительности диалога пользователю."""

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="preferred_dialog_duration_minutes",
            field=models.PositiveSmallIntegerField(default=10, verbose_name="Персональный таймер, мин"),
        ),
    ]
