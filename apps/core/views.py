"""Базовые пользовательские представления приложения core."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    """Отображает стартовую страницу после успешной авторизации.

    Контекст использования:
    - служит защищённой домашней страницей для авторизованного пользователя;
    - в следующих итерациях будет расширена до выбора игр и сценариев.

    Параметры:
    - входные данные берутся из HTTP-запроса и user-сессии.

    Возвращает:
    - HTML-страницу `pages/home.html`.

    Исключения и особые случаи:
    - анонимный пользователь перенаправляется на `LOGIN_URL`.

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "pages/home.html"
