"""Представления модуля dialogs для текущего этапа маршрутизации."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from apps.dialogs.models import DialogSession


class DialogPlaceholderView(LoginRequiredMixin, DetailView):
    """Показывает техническую страницу активного диалога до реализации чата.

    Контекст использования:
    - временная точка входа после нажатия кнопки сценария;
    - позволяет проверить, что запуск сценария и маршрутизация работают.

    Параметры:
    - получает `public_id` диалога из URL.

    Возвращает:
    - HTML-страницу `dialogs/placeholder.html`.

    Исключения и особые случаи:
    - пользователь может открыть только свой диалог.

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "dialogs/placeholder.html"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        """Ограничивает выборку диалогами текущего пользователя.

        Контекст использования:
        - защищает от доступа к чужому диалогу по прямому URL.

        Параметры:
        - отсутствуют.

        Возвращает:
        - queryset диалогов только текущего пользователя.

        Исключения и особые случаи:
        - при отсутствии объекта пользователь получает 404.

        Побочные эффекты:
        - отсутствуют.
        """

        return DialogSession.objects.filter(user=self.request.user)
