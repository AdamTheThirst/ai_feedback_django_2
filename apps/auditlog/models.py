"""Модели технического журнала событий и ошибок платформы."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.enums import AuditLogLevel


class AuditLogEntry(models.Model):
    """Хранит техническое событие системы для диагностики и аудита.

    Контекст использования:
    - записывает важные события жизненного цикла диалога и анализа;
    - позволяет отследить ошибки JSON-валидации, падения LLM и служебные операции.

    Параметры:
    - `created_at`: время события;
    - `level`: уровень критичности;
    - `event_type`: машинный тип события;
    - `message`: краткое описание;
    - `actor_user`, `dialog`, `analysis_run`: опциональные связи с сущностями;
    - `object_type`, `object_id`, `context_json`, `traceback_text`: расширенный контекст.

    Возвращает:
    - запись аудита с контекстом события.

    Исключения и особые случаи:
    - поля связей опциональны, чтобы поддерживать системные события без пользователя.

    Побочные эффекты:
    - отсутствуют.
    """

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    level = models.CharField(max_length=16, choices=AuditLogLevel.choices, default=AuditLogLevel.INFO, verbose_name="Уровень")
    event_type = models.CharField(max_length=128, verbose_name="Тип события")
    message = models.TextField(verbose_name="Сообщение")
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_log_entries",
        verbose_name="Пользователь-инициатор",
    )
    dialog = models.ForeignKey(
        "dialogs.DialogSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_log_entries",
        verbose_name="Диалог",
    )
    analysis_run = models.ForeignKey(
        "analysis.AnalysisRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_log_entries",
        verbose_name="Запуск анализа",
    )
    object_type = models.CharField(max_length=128, blank=True, verbose_name="Тип объекта")
    object_id = models.CharField(max_length=128, blank=True, verbose_name="ID объекта")
    context_json = models.JSONField(null=True, blank=True, verbose_name="Контекст JSON")
    traceback_text = models.TextField(blank=True, verbose_name="Трассировка")

    class Meta:
        """Мета-настройки таблицы журнала аудита."""

        verbose_name = "Запись audit log"
        verbose_name_plural = "Записи audit log"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["level", "created_at"], name="idx_audit_level_created"),
            models.Index(fields=["event_type", "created_at"], name="idx_audit_event_created"),
        ]

    def __str__(self) -> str:
        """Возвращает краткое представление записи журнала.

        Контекст использования:
        - используется в админке и технической диагностике.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку вида `<created_at> <level> <event_type>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.created_at.isoformat()} {self.level} {self.event_type}"
