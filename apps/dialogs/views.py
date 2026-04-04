"""Представления модуля dialogs для lifecycle и чата V1."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView

from apps.core.enums import DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogSession
from apps.dialogs.services.chat import DialogSendMessageError, send_user_message


class DialogChatView(LoginRequiredMixin, DetailView):
    """Отображает чатовый экран активной диалоговой сессии пользователя.

    Контекст использования:
    - открывается после успешного старта сценария на главной странице;
    - показывает условия, стартовое сообщение и историю сообщений.

    Параметры:
    - принимает `public_id` диалога из URL.

    Возвращает:
    - HTML-страницу `dialogs/chat.html`.

    Исключения и особые случаи:
    - пользователь может открыть только свой диалог.

    Побочные эффекты:
    - отсутствуют.
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
        """Формирует контекст экрана чата с сообщениями и UI-флагами.

        Контекст использования:
        - вызывается шаблоном `dialogs/chat.html`.

        Параметры:
        - `**kwargs`: дополнительные данные базового класса.

        Возвращает:
        - словарь контекста для рендера UI чата.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        context = super().get_context_data(**kwargs)
        dialog: DialogSession = self.object
        context["messages"] = dialog.messages.order_by("sequence_no", "id")
        context["can_send"] = dialog.status == DialogStatus.ACTIVE and not dialog.pending_response
        context["message_role_user"] = DialogMessageRole.USER
        context["message_role_assistant"] = DialogMessageRole.ASSISTANT
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
        text = request.POST.get("text", "")
        client_message_id = request.POST.get("client_message_id")

        try:
            payload = send_user_message(dialog=dialog, text=text, client_message_id=client_message_id)
            return JsonResponse({"ok": True, **payload})
        except DialogSendMessageError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)


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
