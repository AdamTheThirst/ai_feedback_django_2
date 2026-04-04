"""Модели жизненного цикла игрового диалога пользователя."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.enums import DialogEndedReason, DialogStatus
from apps.core.models import PublicIdModel, TimestampedModel


class DialogSession(PublicIdModel, TimestampedModel):
    """Хранит жизненный цикл диалоговой сессии пользователя.

    Контекст использования:
    - создаётся при старте сценария и живёт до финального состояния;
    - используется как основной контейнер статуса и технических атрибутов диалога.

    Параметры:
    - `user`: владелец сессии;
    - `status`: текущий статус из `DialogStatus`;
    - `ended_reason`: код причины завершения при наличии;
    - `started_at`/`ended_at`: фактические времена старта и завершения;
    - счётчики сообщений и технические метки клиентской активности.

    Возвращает:
    - запись с текущим состоянием диалога.

    Исключения и особые случаи:
    - в БД ограничивается единственный активный диалог на пользователя.

    Побочные эффекты:
    - запись участвует в проверках запуска новых сценариев и в будущей аналитике.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Пользователь",
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
