"""Модели технического жизненного цикла анализа завершённого диалога."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus
from apps.core.models import PublicIdModel, TimestampedModel


class AnalysisRun(PublicIdModel, TimestampedModel):
    """Фиксирует процесс выполнения аналитики по одной диалоговой сессии.

    Контекст использования:
    - создаётся после завершения диалога, если есть пользовательские реплики;
    - хранит технический статус, время выполнения и диагностическую ошибку.

    Параметры:
    - `dialog`: связанная сессия диалога;
    - `status`: текущий статус выполнения из `AnalysisRunStatus`;
    - `started_at`/`finished_at`: интервальные метки выполнения;
    - `llm_attempt_count`: суммарное число попыток вызова LLM;
    - `error_code`/`error_message`: данные о последней ошибке.

    Возвращает:
    - запись запуска анализа, связанную с одним диалогом.

    Исключения и особые случаи:
    - применяется ограничение один-к-одному с диалогом для V1.

    Побочные эффекты:
    - участвует в построении пользовательского результата и диагностике проблем аналитики.
    """

    dialog = models.OneToOneField(
        "dialogs.DialogSession",
        on_delete=models.PROTECT,
        related_name="analysis_run",
        verbose_name="Диалог",
    )
    status = models.CharField(
        max_length=16,
        choices=AnalysisRunStatus.choices,
        default=AnalysisRunStatus.PENDING,
        verbose_name="Статус анализа",
    )
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Запущен")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершён")
    llm_attempt_count = models.PositiveIntegerField(default=0, verbose_name="Число попыток LLM")
    error_code = models.CharField(max_length=64, blank=True, verbose_name="Код ошибки")
    error_message = models.TextField(blank=True, verbose_name="Описание ошибки")

    class Meta:
        """Мета-настройки таблицы запусков анализа."""

        verbose_name = "Запуск анализа"
        verbose_name_plural = "Запуски анализа"
        indexes = [
            models.Index(fields=["status"], name="idx_analysis_status"),
            models.Index(fields=["started_at"], name="idx_analysis_started_at"),
        ]

    def __str__(self) -> str:
        """Возвращает компактную строку для представления запуска анализа.

        Контекст использования:
        - применяется в админке и технических логах.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку вида `<dialog_public_id> — <status>`.

        Исключения и особые случаи:
        - не ожидаются.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.dialog.public_id} — {self.status}"


class AnalysisResult(TimestampedModel):
    """Хранит результат одного аналитического критерия внутри запуска анализа.

    Контекст использования:
    - создаётся для каждого активного `AnalysisPrompt` игры;
    - фиксирует snapshot-поля критерия, итоговый балл и статус валидации ответа LLM.

    Параметры:
    - `analysis_run`: родительский запуск анализа;
    - `analysis_prompt`: критерий, по которому получен результат;
    - snapshot-поля (`sort_order_snapshot`, `alias_snapshot`, `title_snapshot`, `header_snapshot_text`, `comment_snapshot_text`);
    - `rating`, `rating_min`, `rating_max`, `analysis_text`;
    - `raw_llm_response_text`, `parsed_json_snapshot`, `validation_status`, `validation_error_message`, `llm_attempt_count`.

    Возвращает:
    - запись результата критерия.

    Исключения и особые случаи:
    - комбинация `(analysis_run, analysis_prompt)` уникальна;
    - `rating` валидируется как неотрицательное целое значение.

    Побочные эффекты:
    - отсутствуют.
    """

    analysis_run = models.ForeignKey(
        "analysis.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Запуск анализа",
    )
    analysis_prompt = models.ForeignKey(
        "content.AnalysisPrompt",
        on_delete=models.PROTECT,
        related_name="analysis_results",
        verbose_name="Аналитический промт",
    )
    sort_order_snapshot = models.PositiveIntegerField(verbose_name="Порядок критерия")
    alias_snapshot = models.SlugField(max_length=120, verbose_name="Alias критерия")
    title_snapshot = models.CharField(max_length=255, verbose_name="Название критерия")
    header_snapshot_text = models.CharField(max_length=255, verbose_name="Заголовок карточки")
    comment_snapshot_text = models.TextField(blank=True, verbose_name="Комментарий критерия")
    rating = models.SmallIntegerField(validators=[MinValueValidator(0)], verbose_name="Оценка")
    rating_min = models.SmallIntegerField(verbose_name="Минимум шкалы")
    rating_max = models.SmallIntegerField(verbose_name="Максимум шкалы")
    analysis_text = models.TextField(verbose_name="Текст разбора")
    raw_llm_response_text = models.TextField(blank=True, verbose_name="Сырой ответ LLM")
    parsed_json_snapshot = models.JSONField(null=True, blank=True, verbose_name="Сохранённый JSON")
    validation_status = models.CharField(
        max_length=24,
        choices=AnalysisValidationStatus.choices,
        default=AnalysisValidationStatus.VALID,
        verbose_name="Статус валидации",
    )
    validation_error_message = models.TextField(blank=True, verbose_name="Ошибка валидации")
    llm_attempt_count = models.PositiveIntegerField(default=1, verbose_name="Попытки LLM по критерию")

    class Meta:
        """Мета-настройки таблицы результатов анализа."""

        verbose_name = "Результат анализа"
        verbose_name_plural = "Результаты анализа"
        ordering = ["sort_order_snapshot", "id"]
        constraints = [
            models.UniqueConstraint(fields=["analysis_run", "analysis_prompt"], name="uniq_analysis_result_prompt_per_run"),
        ]
        indexes = [
            models.Index(fields=["analysis_run", "sort_order_snapshot"], name="idx_analysis_result_sort"),
            models.Index(fields=["validation_status"], name="idx_analysis_result_validation"),
        ]

    def __str__(self) -> str:
        """Возвращает краткое представление результата для админки и логов.

        Контекст использования:
        - применяется в списках административного интерфейса и диагностике.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку вида `<analysis_run_id> / <alias_snapshot> / <rating>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.analysis_run_id} / {self.alias_snapshot} / {self.rating}"
