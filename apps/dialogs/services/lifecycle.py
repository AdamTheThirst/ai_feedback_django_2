"""Сервис жизненного цикла завершения диалога и таймерных переходов."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.enums import DialogEndedReason, DialogStatus
from apps.dialogs.models import DialogSession


class DialogFinishError(Exception):
    """Ошибка сервисного уровня при попытке завершить диалог.

    Контекст использования:
    - используется API-представлениями завершения сессии для контролируемого ответа клиенту.

    Параметры:
    - принимает текст ошибки в базовом конструкторе `Exception`.

    Возвращает:
    - экземпляр исключения с пояснением причины отказа.

    Исключения и особые случаи:
    - поднимается только для валидационных ошибок входного запроса.

    Побочные эффекты:
    - отсутствуют.
    """


def get_dialog_seconds_remaining(dialog: DialogSession, now=None) -> int:
    """Возвращает оставшееся время активной сессии в секундах.

    Контекст использования:
    - применяется для серверной синхронизации клиентского таймера и проверки автозавершения.

    Параметры:
    - `dialog`: целевая диалоговая сессия;
    - `now`: момент времени для расчёта, если не передан — берётся `timezone.now()`.

    Возвращает:
    - неотрицательное число секунд до истечения таймера.

    Исключения и особые случаи:
    - если в сессии не задана длительность, используется безопасный дефолт `600`.

    Побочные эффекты:
    - отсутствуют.
    """

    current_dt = now or timezone.now()
    duration_seconds = int(dialog.effective_duration_seconds or 600)
    elapsed_seconds = int((current_dt - dialog.started_at).total_seconds())
    return max(duration_seconds - max(elapsed_seconds, 0), 0)


@transaction.atomic
def maybe_finish_dialog_by_timeout(dialog: DialogSession, now=None) -> DialogSession:
    """Завершает активный диалог по таймеру, если время вышло.

    Контекст использования:
    - вызывается перед отправкой сообщений и при открытии экрана чата;
    - предотвращает отправку реплик после истечения лимита времени.

    Параметры:
    - `dialog`: сессия, которую требуется проверить;
    - `now`: текущий момент времени для детерминированных тестов.

    Возвращает:
    - обновлённый экземпляр `DialogSession`.

    Исключения и особые случаи:
    - если диалог уже не активен, возвращается без изменений.

    Побочные эффекты:
    - может перевести диалог в финальное состояние через `finish_dialog`.
    """

    if dialog.status != DialogStatus.ACTIVE:
        return dialog
    if get_dialog_seconds_remaining(dialog=dialog, now=now) > 0:
        return dialog
    return finish_dialog(dialog=dialog, reason=DialogEndedReason.TIMEOUT, now=now)


@transaction.atomic
def finish_dialog(dialog: DialogSession, reason: str, now=None) -> DialogSession:
    """Переводит активный диалог в финальное состояние с указанной причиной.

    Контекст использования:
    - единая точка завершения для ручной кнопки, таймера и сигнала ухода со страницы.

    Параметры:
    - `dialog`: целевая диалоговая сессия;
    - `reason`: код причины завершения из `DialogEndedReason`;
    - `now`: текущий момент времени для тестов.

    Возвращает:
    - экземпляр `DialogSession` после фиксации финального статуса.

    Исключения и особые случаи:
    - `DialogFinishError`, если передан неподдерживаемый `reason`.
    - повторный вызов для уже завершённого диалога идемпотентен и не меняет данные.

    Побочные эффекты:
    - обновляет `status`, `ended_reason`, `ended_at`, `pending_response`, `last_client_activity_at`;
    - записывает изменения в БД;
    - запускает анализ через `AnalysisService`, если в диалоге есть пользовательские реплики.
    """

    supported_reasons = {
        DialogEndedReason.MANUAL_FEEDBACK,
        DialogEndedReason.TIMEOUT,
        DialogEndedReason.PAGE_LEAVE,
        DialogEndedReason.INACTIVE_TIMEOUT,
    }
    if reason not in supported_reasons:
        raise DialogFinishError("Недопустимая причина завершения диалога.")

    dialog.refresh_from_db()
    if dialog.status != DialogStatus.ACTIVE:
        return dialog

    current_dt = now or timezone.now()
    final_status = DialogStatus.FINISHED
    final_reason = reason

    if dialog.user_message_count == 0:
        final_status = DialogStatus.ANALYSIS_SKIPPED
        final_reason = DialogEndedReason.NO_USER_MESSAGES
    elif reason in {DialogEndedReason.PAGE_LEAVE, DialogEndedReason.INACTIVE_TIMEOUT}:
        final_status = DialogStatus.ABORTED

    dialog.status = final_status
    dialog.ended_reason = final_reason
    dialog.ended_at = current_dt
    dialog.pending_response = False
    dialog.last_client_activity_at = current_dt
    dialog.save(
        update_fields=[
            "status",
            "ended_reason",
            "ended_at",
            "pending_response",
            "last_client_activity_at",
            "updated_at",
        ]
    )

    if dialog.user_message_count > 0:
        from apps.analysis.services.engine import run_analysis_for_dialog

        run_analysis_for_dialog(dialog)

    return dialog


@transaction.atomic
def finalize_stale_page_leave_dialogs(now=None) -> int:
    """Добивает сессии после клиентского ухода, если финальный сигнал не дошёл повторно.

    Контекст использования:
    - серверный fallback-механизм для сценария разрыва вкладки/соединения;
    - вызывается в пользовательских endpoint-ах перед проверкой активных сессий.

    Параметры:
    - `now`: момент времени для тестов, по умолчанию `timezone.now()`.

    Возвращает:
    - количество диалогов, переведённых в `aborted/inactive_timeout`.

    Исключения и особые случаи:
    - если подходящих сессий нет, возвращается `0`.

    Побочные эффекты:
    - массово обновляет таблицу `DialogSession`.
    """

    current_dt = now or timezone.now()
    grace_seconds = int(getattr(settings, "DIALOG_CLIENT_ABORT_GRACE_SECONDS", 20))
    threshold_dt = current_dt - timedelta(seconds=max(grace_seconds, 1))

    stale_qs = DialogSession.objects.filter(
        status=DialogStatus.ACTIVE,
        client_aborted_at__isnull=False,
        client_aborted_at__lte=threshold_dt,
    )
    stale_ids = list(stale_qs.values_list("id", flat=True))
    if not stale_ids:
        return 0

    updated = DialogSession.objects.filter(id__in=stale_ids, status=DialogStatus.ACTIVE).update(
        status=DialogStatus.ABORTED,
        ended_reason=DialogEndedReason.INACTIVE_TIMEOUT,
        ended_at=current_dt,
        pending_response=False,
        last_client_activity_at=current_dt,
        updated_at=current_dt,
    )
    return updated
