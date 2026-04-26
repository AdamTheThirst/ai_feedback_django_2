"""Представления модуля dialogs для lifecycle, таймера и чата V1."""

import traceback

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from apps.auditlog.models import AuditLogEntry
from apps.core.enums import AuditLogLevel, DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogSession
from apps.dialogs.services.chat import DialogSendMessageError, send_user_message
from apps.dialogs.services.lifecycle import (
    DialogFinishError,
    finish_dialog,
    get_dialog_seconds_remaining,
    maybe_finish_dialog_by_timeout,
)


def log_dialog_api_error(
    *,
    request: HttpRequest,
    dialog: DialogSession,
    event_type: str,
    message: str,
    error: Exception,
    context_json: dict | None = None,
) -> AuditLogEntry:
    """Сохраняет непредвиденную ошибку API диалога в audit log.

    Контекст использования:
    - вызывается в `except Exception` блоках endpoint-ов dialogs;
    - даёт администратору видимость причин клиентских сообщений «Ошибка сети».

    Параметры:
    - `request`: исходный HTTP-запрос пользователя;
    - `dialog`: диалог, в контексте которого произошла ошибка;
    - `event_type`: машинный тип события;
    - `message`: краткий текст события;
    - `error`: исключение, которое нужно зафиксировать;
    - `context_json`: дополнительный структурированный контекст.

    Возвращает:
    - созданную запись `AuditLogEntry`.

    Исключения и особые случаи:
    - при `context_json=None` сохраняется только базовый контекст.

    Побочные эффекты:
    - создаёт запись в БД audit log.
    """

    context = {
        "path": request.path,
        "method": request.method,
        "dialog_public_id": str(dialog.public_id),
        "error_class": error.__class__.__name__,
    }
    if context_json:
        context.update(context_json)

    return AuditLogEntry.objects.create(
        level=AuditLogLevel.ERROR,
        event_type=event_type,
        message=message,
        actor_user=request.user if request.user.is_authenticated else None,
        dialog=dialog,
        context_json=context,
        traceback_text=traceback.format_exc(),
    )


class DialogChatView(LoginRequiredMixin, DetailView):
    """Отображает чатовый экран активной диалоговой сессии пользователя.

    Контекст использования:
    - открывается после успешного старта сценария на главной странице;
    - показывает условия, стартовое сообщение, историю и серверно-синхронизированный таймер.

    Параметры:
    - принимает `public_id` диалога из URL.

    Возвращает:
    - HTML-страницу `dialogs/chat.html`.

    Исключения и особые случаи:
    - пользователь может открыть только свой диалог.

    Побочные эффекты:
    - при истечении таймера может завершить диалог серверно до рендера страницы.
    """

    template_name = "dialogs/chat.html"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        """Ограничивает выборку диалогами текущего пользователя.

        Контекст использования:
        - защищает от доступа к чужому диалогу по прямому URL.

        Параметры:
        - отсутствуют.

        Возвращает:
        - queryset диалогов, принадлежащих текущему пользователю.

        Исключения и особые случаи:
        - при отсутствии объекта возвращается 404.

        Побочные эффекты:
        - отсутствуют.
        """

        return (
            DialogSession.objects.filter(user=self.request.user)
            .select_related("game", "scenario")
            .prefetch_related("messages")
        )

    def get_context_data(self, **kwargs):
        """Формирует контекст экрана чата с сообщениями, таймером и UI-флагами.

        Контекст использования:
        - вызывается шаблоном `dialogs/chat.html`.

        Параметры:
        - `**kwargs`: дополнительные данные базового класса.

        Возвращает:
        - словарь контекста для рендера UI чата.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - может обновить статус диалога через автозавершение по таймеру.
        """

        context = super().get_context_data(**kwargs)
        dialog: DialogSession = maybe_finish_dialog_by_timeout(self.object)
        context["object"] = dialog
        context["messages"] = dialog.messages.order_by("sequence_no", "id")
        context["can_send"] = dialog.status == DialogStatus.ACTIVE and not dialog.pending_response
        context["can_finish"] = dialog.status == DialogStatus.ACTIVE
        context["seconds_remaining"] = get_dialog_seconds_remaining(dialog)
        context["message_role_user"] = DialogMessageRole.USER
        context["message_role_assistant"] = DialogMessageRole.ASSISTANT
        context["dialog_status"] = dialog.status
        return context


class DialogSendMessageApiView(LoginRequiredMixin, View):
    """Обрабатывает JSON-отправку сообщения пользователя в активный диалог.

    Контекст использования:
    - вызывается JavaScript-логикой чатового экрана без полной перезагрузки страницы.

    Параметры:
    - принимает `public_id` диалога и POST-поля `text`, `client_message_id`.

    Возвращает:
    - `JsonResponse` со структурой новых сообщений или ошибкой.

    Исключения и особые случаи:
    - при нарушении инвариантов возвращает статус `400` с кодом ошибки.

    Побочные эффекты:
    - создаёт новые сообщения и обновляет состояние диалога.
    """

    def post(self, request: HttpRequest, public_id) -> JsonResponse:
        """Выполняет отправку сообщения и возвращает JSON-результат.

        Контекст использования:
        - endpoint для кнопки «Отправить» и Enter в чатовом UI.

        Параметры:
        - `request`: POST-запрос с текстом сообщения;
        - `public_id`: внешний UUID целевого диалога.

        Возвращает:
        - JSON с `user_message`, `assistant_message`, `dialog_status`.

        Исключения и особые случаи:
        - `DialogSendMessageError` обрабатывается как контролируемая ошибка уровня API.

        Побочные эффекты:
        - создаёт записи сообщений и обновляет счётчики сессии.
        """

        dialog = get_object_or_404(DialogSession, public_id=public_id, user=request.user)
        maybe_finish_dialog_by_timeout(dialog)
        text = request.POST.get("text", "")
        client_message_id = request.POST.get("client_message_id")

        try:
            payload = send_user_message(dialog=dialog, text=text, client_message_id=client_message_id)
            return JsonResponse({"ok": True, **payload})
        except DialogSendMessageError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            log_dialog_api_error(
                request=request,
                dialog=dialog,
                event_type="dialogs.send_message.unhandled_error",
                message="Непредвиденная ошибка при отправке сообщения в диалоге.",
                error=exc,
            )
            return JsonResponse({"ok": False, "error": "Внутренняя ошибка сервера при отправке сообщения."}, status=500)


class DialogFinishApiView(LoginRequiredMixin, View):
    """Завершает диалог вручную или по таймеру через JSON-endpoint.

    Контекст использования:
    - вызывается кнопкой «Дай обратную связь» и клиентским обработчиком истечения времени.

    Параметры:
    - принимает `public_id` и POST-поле `reason`.

    Возвращает:
    - JSON со статусом и метаданными завершения.

    Исключения и особые случаи:
    - повторный вызов идемпотентен и возвращает уже сохранённое финальное состояние.

    Побочные эффекты:
    - переводит `DialogSession` в финальный статус.
    """

    def post(self, request: HttpRequest, public_id) -> JsonResponse:
        """Выполняет завершение диалога по явной причине клиента.

        Контекст использования:
        - endpoint для ручного завершения и завершения по таймеру.

        Параметры:
        - `request`: POST-запрос;
        - `public_id`: UUID диалога текущего пользователя.

        Возвращает:
        - JSON c полями `dialog_status`, `ended_reason`, `ended_at`.

        Исключения и особые случаи:
        - при невалидной причине возвращает HTTP 400.

        Побочные эффекты:
        - обновляет запись сессии в БД.
        """

        dialog = get_object_or_404(DialogSession, public_id=public_id, user=request.user)
        reason = request.POST.get("reason", DialogEndedReason.MANUAL_FEEDBACK)

        try:
            finished_dialog = finish_dialog(dialog=dialog, reason=reason)
        except DialogFinishError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            log_dialog_api_error(
                request=request,
                dialog=dialog,
                event_type="dialogs.finish.unhandled_error",
                message="Непредвиденная ошибка при завершении диалога.",
                error=exc,
                context_json={"finish_reason": reason},
            )
            return JsonResponse({"ok": False, "error": "Внутренняя ошибка сервера при завершении диалога."}, status=500)

        return JsonResponse(
            {
                "ok": True,
                "dialog_status": finished_dialog.status,
                "ended_reason": finished_dialog.ended_reason,
                "ended_at": finished_dialog.ended_at.isoformat() if finished_dialog.ended_at else None,
            }
        )


class DialogPageLeaveApiView(LoginRequiredMixin, View):
    """Обрабатывает сигнал ухода пользователя со страницы диалога.

    Контекст использования:
    - вызывается браузером через `sendBeacon` при `pagehide`/`beforeunload`;
    - защищает от потери завершения сессии при закрытии вкладки.

    Параметры:
    - принимает `public_id` диалога и авторизованную cookie-сессию пользователя.

    Возвращает:
    - JSON с подтверждением фиксации причины `page_leave`.

    Исключения и особые случаи:
    - повторный вызов безопасен и не дублирует финальные изменения.

    Побочные эффекты:
    - завершает активный диалог как прерванный.
    """

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        """Отключает CSRF-проверку только для сценария фонового `sendBeacon`.

        Контекст использования:
        - `sendBeacon` не всегда может стабильно передать CSRF-заголовок.

        Параметры:
        - стандартные аргументы CBV `dispatch`.

        Возвращает:
        - результат обработки базового `dispatch`.

        Исключения и особые случаи:
        - доступ остаётся ограничен авторизацией пользователя.

        Побочные эффекты:
        - отсутствуют.
        """

        return super().dispatch(*args, **kwargs)

    def post(self, request: HttpRequest, public_id) -> JsonResponse:
        """Фиксирует уход пользователя со страницы как завершение `page_leave`.

        Контекст использования:
        - endpoint для механизма безопасного завершения при закрытии страницы.

        Параметры:
        - `request`: POST-запрос;
        - `public_id`: UUID диалоговой сессии.

        Возвращает:
        - JSON с текущим финальным состоянием диалога.

        Исключения и особые случаи:
        - отсутствуют; для уже завершённой сессии возвращается текущий статус.

        Побочные эффекты:
        - обновляет `client_aborted_at` и финальный статус диалога.
        """

        dialog = get_object_or_404(DialogSession, public_id=public_id, user=request.user)
        try:
            dialog.client_aborted_at = timezone.now()
            dialog.save(update_fields=["client_aborted_at", "updated_at"])
            finished_dialog = finish_dialog(dialog=dialog, reason=DialogEndedReason.PAGE_LEAVE)
            return JsonResponse(
                {
                    "ok": True,
                    "dialog_status": finished_dialog.status,
                    "ended_reason": finished_dialog.ended_reason,
                }
            )
        except Exception as exc:
            log_dialog_api_error(
                request=request,
                dialog=dialog,
                event_type="dialogs.page_leave.unhandled_error",
                message="Непредвиденная ошибка при фиксации ухода со страницы диалога.",
                error=exc,
            )
            return JsonResponse({"ok": False, "error": "Внутренняя ошибка сервера при фиксации page_leave."}, status=500)


class DialogPlaceholderRedirectView(LoginRequiredMixin, View):
    """Перенаправляет старый placeholder-маршрут на полноценный чатовый экран.

    Контекст использования:
    - сохраняет обратную совместимость ссылок из предыдущего шага.

    Параметры:
    - принимает `public_id` диалога из URL.

    Возвращает:
    - redirect на `dialogs:chat`.

    Исключения и особые случаи:
    - если диалог не найден или чужой, возвращается 404.

    Побочные эффекты:
    - отсутствуют.
    """

    def get(self, request: HttpRequest, public_id) -> HttpResponse:
        """Находит диалог текущего пользователя и перенаправляет в чат.

        Контекст использования:
        - поддерживает переходы по устаревшему URL placeholder.

        Параметры:
        - `request`: текущий HTTP-запрос;
        - `public_id`: UUID диалоговой сессии.

        Возвращает:
        - HTTP redirect на маршрут `dialogs:chat`.

        Исключения и особые случаи:
        - при отсутствии диалога возвращается 404.

        Побочные эффекты:
        - отсутствуют.
        """

        dialog = get_object_or_404(DialogSession, public_id=public_id, user=request.user)
        return redirect("dialogs:chat", public_id=dialog.public_id)
