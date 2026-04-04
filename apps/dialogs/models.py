"""Модели жизненного цикла игрового диалога пользователя."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.enums import DialogEndedReason, DialogMessageRole, DialogStatus
from apps.core.models import PublicIdModel, TimestampedModel


class DialogSession(PublicIdModel, TimestampedModel):
    """Хранит жизненный цикл диалоговой сессии пользователя.

    Контекст использования:
    - создаётся при старте сценария и живёт до финального состояния;
    - используется как основной контейнер статуса и технических атрибутов диалога.

    Параметры:
    - `user`: владелец сессии;
    - `game`/`scenario`: зафиксированные ссылки сценария запуска;
    - `scenario_prompt_used`: версия промта, активная на старте;
    - `status` и `ended_reason`: состояние жизненного цикла;
    - `conditions_snapshot_text` и `opening_message_snapshot_text`: снимки контента;
    - `pending_response`: технический флаг ожидания ответа ассистента.

    Возвращает:
    - запись с текущим состоянием диалога.

    Исключения и особые случаи:
    - в БД ограничивается единственный активный диалог на пользователя.

    Побочные эффекты:
    - запись участвует в проверках запуска новых сценариев и в последующей аналитике.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Пользователь",
    )
    game = models.ForeignKey("content.Game", on_delete=models.PROTECT, related_name="dialog_sessions", verbose_name="Игра", null=True, blank=True)
    scenario = models.ForeignKey(
        "content.Scenario", on_delete=models.PROTECT, related_name="dialog_sessions", verbose_name="Сценарий", null=True, blank=True
    )
    scenario_prompt_used = models.ForeignKey(
        "content.ScenarioPrompt",
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Использованный промт",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=DialogStatus.choices,
        default=DialogStatus.ACTIVE,
        verbose_name="Статус диалога",
    )
    ended_reason = models.CharField(
        max_length=32,
        choices=DialogEndedReason.choices,
        blank=True,
        verbose_name="Причина завершения",
    )
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Начат")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершён")
    user_message_count = models.PositiveIntegerField(default=0, verbose_name="Сообщений пользователя")
    assistant_message_count = models.PositiveIntegerField(default=0, verbose_name="Сообщений ассистента")
    conditions_snapshot_text = models.TextField(verbose_name="Снимок условий", blank=True)
    opening_message_snapshot_text = models.TextField(verbose_name="Снимок стартового сообщения", blank=True)
    pending_response = models.BooleanField(default=False, verbose_name="Ожидание ответа ассистента")
    effective_duration_seconds = models.PositiveIntegerField(default=600, verbose_name="Эффективная длительность, сек")
    last_client_activity_at = models.DateTimeField(null=True, blank=True, verbose_name="Последняя клиентская активность")
    client_aborted_at = models.DateTimeField(null=True, blank=True, verbose_name="Время клиентского прерывания")

    class Meta:
        """Мета-настройки таблицы диалогов."""

        verbose_name = "Диалоговая сессия"
        verbose_name_plural = "Диалоговые сессии"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status=DialogStatus.ACTIVE),
                name="uniq_active_dialog_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_dialog_user_status"),
            models.Index(fields=["started_at"], name="idx_dialog_started_at"),
        ]

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление сессии для админки.

        Контекст использования:
        - отображается в Django Admin, логах и отладочных выводах.

        Параметры:
        - не принимает аргументов.

        Возвращает:
        - строку вида `<email/username> — <статус> — <public_id>`.

        Исключения и особые случаи:
        - если у пользователя нет email, используется строковое представление пользователя.

        Побочные эффекты:
        - отсутствуют.
        """

        user_label = getattr(self.user, "email", None) or str(self.user)
        return f"{user_label} — {self.status} — {self.public_id}"


class DialogMessage(models.Model):
    """Хранит отдельную реплику в рамках диалоговой сессии.

    Контекст использования:
    - фиксирует историю сообщений пользователя и ассистента;
    - используется для восстановления ленты чата и передачи контекста в LLM.

    Параметры:
    - `dialog`: родительская сессия;
    - `sequence_no`: порядок сообщения;
    - `role`: роль отправителя;
    - `text` и `char_count`: текст и его длина;
    - `client_message_id`: idempotency-идентификатор клиентской отправки.

    Возвращает:
    - запись сообщения диалога.

    Исключения и особые случаи:
    - комбинация `(dialog, sequence_no)` уникальна;
    - комбинация `(dialog, client_message_id)` уникальна для защиты от дублей.

    Побочные эффекты:
    - отсутствуют.
    """

    dialog = models.ForeignKey("dialogs.DialogSession", on_delete=models.CASCADE, related_name="messages", verbose_name="Диалог")
    sequence_no = models.PositiveIntegerField(verbose_name="Порядковый номер")
    role = models.CharField(max_length=16, choices=DialogMessageRole.choices, verbose_name="Роль")
    text = models.TextField(verbose_name="Текст")
    char_count = models.PositiveIntegerField(verbose_name="Количество символов")
    client_message_id = models.UUIDField(null=True, blank=True, verbose_name="Клиентский ID сообщения")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")

    class Meta:
        """Мета-настройки таблицы сообщений диалога."""

        verbose_name = "Сообщение диалога"
        verbose_name_plural = "Сообщения диалога"
        ordering = ["sequence_no", "id"]
        constraints = [
            models.UniqueConstraint(fields=["dialog", "sequence_no"], name="uniq_dialog_message_seq"),
            models.UniqueConstraint(
                fields=["dialog", "client_message_id"],
                condition=Q(client_message_id__isnull=False),
                name="uniq_dialog_client_message_id",
            ),
        ]
        indexes = [models.Index(fields=["dialog", "created_at"], name="idx_dialog_message_created")]

    def save(self, *args, **kwargs) -> None:
        """Сохраняет сообщение и автоматически пересчитывает длину текста.

        Контекст использования:
        - гарантирует согласованность поля `char_count` с фактическим `text`.

        Параметры:
        - `*args`, `**kwargs`: стандартные аргументы сохранения ORM.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - записывает сообщение в базу данных.
        """

        self.char_count = len(self.text or "")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает краткое представление сообщения для диагностики.

        Контекст использования:
        - используется в административном отображении и логах.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку `<dialog_id>#<sequence_no> <role>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.dialog_id}#{self.sequence_no} {self.role}"
