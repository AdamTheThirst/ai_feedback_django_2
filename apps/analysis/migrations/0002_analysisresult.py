# Generated manually for iteration 8 analytics engine.

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Создаёт таблицу AnalysisResult для хранения результатов по каждому критерию."""

    dependencies = [
        ("analysis", "0001_initial"),
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("sort_order_snapshot", models.PositiveIntegerField(verbose_name="Порядок критерия")),
                ("alias_snapshot", models.SlugField(max_length=120, verbose_name="Alias критерия")),
                ("title_snapshot", models.CharField(max_length=255, verbose_name="Название критерия")),
                ("header_snapshot_text", models.CharField(max_length=255, verbose_name="Заголовок карточки")),
                ("comment_snapshot_text", models.TextField(blank=True, verbose_name="Комментарий критерия")),
                ("rating", models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name="Оценка")),
                ("rating_min", models.SmallIntegerField(verbose_name="Минимум шкалы")),
                ("rating_max", models.SmallIntegerField(verbose_name="Максимум шкалы")),
                ("analysis_text", models.TextField(verbose_name="Текст разбора")),
                ("raw_llm_response_text", models.TextField(blank=True, verbose_name="Сырой ответ LLM")),
                ("parsed_json_snapshot", models.JSONField(blank=True, null=True, verbose_name="Сохранённый JSON")),
                (
                    "validation_status",
                    models.CharField(
                        choices=[
                            ("valid", "Валидный"),
                            ("invalid_json", "Невалидный JSON"),
                            ("invalid_schema", "Невалидная схема"),
                            ("fallback_saved", "Сохранён fallback"),
                        ],
                        default="valid",
                        max_length=24,
                        verbose_name="Статус валидации",
                    ),
                ),
                ("validation_error_message", models.TextField(blank=True, verbose_name="Ошибка валидации")),
                ("llm_attempt_count", models.PositiveIntegerField(default=1, verbose_name="Попытки LLM по критерию")),
                (
                    "analysis_prompt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_results",
                        to="content.analysisprompt",
                        verbose_name="Аналитический промт",
                    ),
                ),
                (
                    "analysis_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="analysis.analysisrun",
                        verbose_name="Запуск анализа",
                    ),
                ),
            ],
            options={
                "verbose_name": "Результат анализа",
                "verbose_name_plural": "Результаты анализа",
                "ordering": ["sort_order_snapshot", "id"],
                "indexes": [
                    models.Index(fields=["analysis_run", "sort_order_snapshot"], name="idx_analysis_result_sort"),
                    models.Index(fields=["validation_status"], name="idx_analysis_result_validation"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="analysisresult",
            constraint=models.UniqueConstraint(
                fields=("analysis_run", "analysis_prompt"),
                name="uniq_analysis_result_prompt_per_run",
            ),
        ),
    ]
