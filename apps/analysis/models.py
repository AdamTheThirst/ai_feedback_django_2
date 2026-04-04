"""Модели технического жизненного цикла анализа завершённого диалога."""

from django.db import models
from django.utils import timezone

from apps.core.enums import AnalysisRunStatus
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
