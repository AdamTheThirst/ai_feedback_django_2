"""Пользовательские представления главной страницы и входных точек разделов."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.content.models import Game, Scenario
from apps.dialogs.models import DialogSession
from apps.dialogs.services.session import has_active_dialog


class HomeView(LoginRequiredMixin, TemplateView):
    """Отображает главную страницу пользователя со списком игр и сценариев.

    Контекст использования:
    - точка входа после логина для выбора сценария;
    - отображает нижние кнопки «Энциклопедия», «Личный кабинет», «Выйти».

    Параметры:
    - входные данные берутся из сессии пользователя и базы контента.

    Возвращает:
    - HTML-страницу `pages/home.html`.

    Исключения и особые случаи:
    - анонимный пользователь перенаправляется на `LOGIN_URL`.

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        """Формирует контекст главной страницы с опубликованными играми и сценариями.

        Контекст использования:
        - вызывается при рендеринге `HomeView`.

        Параметры:
        - `**kwargs`: дополнительные данные базового класса.

        Возвращает:
        - словарь контекста со списком игр и флагом активного диалога.

        Исключения и особые случаи:
        - если игр нет, возвращается пустой список.

        Побочные эффекты:
        - отсутствуют.
        """

        context = super().get_context_data(**kwargs)
        games = (
            Game.objects.filter(is_published=True, is_archived=False)
            .prefetch_related("scenarios")
            .order_by("sort_order", "title")
        )

        structured_games = []
        for game in games:
            scenarios = game.scenarios.filter(is_published=True, is_archived=False).order_by("sort_order", "title")
            if scenarios.exists():
                structured_games.append({"game": game, "scenarios": scenarios})

        context["games"] = structured_games
        context["has_active_dialog"] = has_active_dialog(self.request.user)
        return context


class ScenarioStartView(LoginRequiredMixin, View):
    """Создаёт новую диалоговую сессию по выбранному сценарию.

    Контекст использования:
    - вызывается кнопкой сценария на главной странице;
    - проверяет ограничение на единственный активный диалог.

    Параметры:
    - получает `game_slug` и `scenario_slug` из URL.

    Возвращает:
    - redirect на страницу активного диалога либо обратно на главную.

    Исключения и особые случаи:
    - если сценарий недоступен, возвращается 404;
    - если активный диалог уже существует, новый не создаётся.

    Побочные эффекты:
    - создаёт запись `DialogSession`.
    """

    def post(self, request: HttpRequest, game_slug: str, scenario_slug: str) -> HttpResponse:
        """Запускает сценарий и создаёт активную сессию диалога.

        Контекст использования:
        - обрабатывает отправку формы запуска сценария.

        Параметры:
        - `request`: HTTP-запрос авторизованного пользователя;
        - `game_slug`: slug игры;
        - `scenario_slug`: slug сценария внутри игры.

        Возвращает:
        - redirect на placeholder-страницу диалога либо обратно на главную страницу.

        Исключения и особые случаи:
        - при наличии активного диалога выводит предупреждение и не создаёт новую запись.

        Побочные эффекты:
        - может создать новую запись `DialogSession` в БД.
        """

        scenario = get_object_or_404(
            Scenario,
            game__slug=game_slug,
            slug=scenario_slug,
            is_published=True,
            is_archived=False,
            game__is_published=True,
            game__is_archived=False,
        )

        if has_active_dialog(request.user):
            messages.warning(request, "У вас уже есть активный диалог. Завершите его перед запуском нового сценария.")
            return redirect("home")

        dialog = DialogSession.objects.create(user=request.user)
        messages.success(request, f"Сценарий «{scenario.title}» запущен.")
        return redirect("dialogs:placeholder", public_id=dialog.public_id)


class EncyclopediaEntryView(LoginRequiredMixin, View):
    """Открывает пользовательскую точку входа в раздел «Энциклопедия».

    Контекст использования:
    - нижняя кнопка главной страницы до полной интеграции энциклопедии в отдельной итерации.

    Параметры:
    - использует только текущий HTTP-запрос.

    Возвращает:
    - HTML-страницу входа в раздел.

    Исключения и особые случаи:
    - анонимные пользователи перенаправляются на вход.

    Побочные эффекты:
    - отсутствуют.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """Рендерит страницу пользовательского входа в энциклопедию.

        Контекст использования:
        - вызывается по маршруту `/encyclopedia/`.

        Параметры:
        - `request`: текущий HTTP-запрос.

        Возвращает:
        - HTML-страницу `pages/encyclopedia_entry.html`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return render(request, "pages/encyclopedia_entry.html")


class CabinetEntryView(LoginRequiredMixin, View):
    """Открывает пользовательскую точку входа в раздел «Личный кабинет».

    Контекст использования:
    - нижняя кнопка главной страницы, ведущая в профильный раздел пользователя.

    Параметры:
    - использует текущий HTTP-запрос.

    Возвращает:
    - HTML-страницу входа в личный кабинет.

    Исключения и особые случаи:
    - анонимные пользователи перенаправляются на страницу входа.

    Побочные эффекты:
    - отсутствуют.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """Рендерит страницу пользовательского входа в личный кабинет.

        Контекст использования:
        - вызывается по маршруту `/cabinet/`.

        Параметры:
        - `request`: текущий HTTP-запрос.

        Возвращает:
        - HTML-страницу `pages/cabinet_entry.html`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return render(request, "pages/cabinet_entry.html")
