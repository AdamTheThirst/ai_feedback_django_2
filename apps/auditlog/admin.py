"""Настройки Django Admin для просмотра технических логов платформы."""

from django.contrib import admin

from apps.auditlog.models import AuditLogEntry


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    """Позволяет администратору просматривать и фильтровать журнал событий.

    Контекст использования:
    - используется в стандартном Django Admin;
    - даёт удобный интерфейс для поиска причин ошибок без прямого доступа к БД.

    Параметры:
    - применяет стандартные опции `ModelAdmin` (списки, фильтры, поиск, readonly-поля).

    Возвращает:
    - HTML-интерфейс Django Admin для модели `AuditLogEntry`.

    Исключения и особые случаи:
    - запись лога не редактируется вручную, поля сделаны только для чтения.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = (
        "created_at",
        "level",
        "event_type",
        "short_message",
        "actor_user",
        "dialog",
        "analysis_run",
    )
    list_filter = ("level", "event_type", "created_at")
    search_fields = (
        "event_type",
        "message",
        "traceback_text",
        "dialog__public_id",
        "analysis_run__dialog__public_id",
        "actor_user__email",
    )
    ordering = ("-created_at", "-id")
    readonly_fields = (
        "created_at",
        "level",
        "event_type",
        "message",
        "actor_user",
        "dialog",
        "analysis_run",
        "object_type",
        "object_id",
        "context_json",
        "traceback_text",
    )

    def has_add_permission(self, request):
        """Запрещает ручное создание логов через админку.

        Контекст использования:
        - логи должны формироваться только кодом приложения.

        Параметры:
        - `request`: текущий HTTP-запрос администратора.

        Возвращает:
        - `False`, чтобы скрыть кнопку добавления.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещает удаление логов через админку.

        Контекст использования:
        - сохраняет целостность технической истории событий.

        Параметры:
        - `request`: текущий HTTP-запрос администратора;
        - `obj`: конкретная запись лога (опционально).

        Возвращает:
        - `False`, чтобы убрать действия удаления.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        _ = obj
        return False

    @admin.display(description="Сообщение")
    def short_message(self, obj: AuditLogEntry) -> str:
        """Возвращает сокращённый текст сообщения для колонки списка.

        Контекст использования:
        - упрощает просмотр таблицы логов в списке Django Admin.

        Параметры:
        - `obj`: текущая запись `AuditLogEntry`.

        Возвращает:
        - первые 120 символов сообщения с многоточием при необходимости.

        Исключения и особые случаи:
        - если сообщение короткое, возвращается без изменений.

        Побочные эффекты:
        - отсутствуют.
        """

        message = (obj.message or "").strip()
        if len(message) <= 120:
            return message
        return f"{message[:117]}..."
