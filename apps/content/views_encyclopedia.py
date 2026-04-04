"""Пользовательские представления раздела «Энциклопедия»."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from apps.content.models import EncyclopediaArticle
from apps.content.services.encyclopedia import encyclopedia_title_sort_key


class EncyclopediaListView(LoginRequiredMixin, View):
    """Показывает список опубликованных статей энциклопедии с пагинацией.

    Контекст использования:
    - пользовательский экран `/encyclopedia/` после авторизации;
    - поддерживает сортировку по правилу: цифры → кириллица → латиница.

    Параметры:
    - query-параметр `page` для пагинации.

    Возвращает:
    - HTML-страницу `encyclopedia/list.html`.

    Исключения и особые случаи:
    - отображаются только `is_published=True` статьи.

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "encyclopedia/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Рендерит страницу списка статей с пагинацией по 10 элементов.

        Контекст использования:
        - endpoint публичного списка энциклопедии для авторизованного пользователя.

        Параметры:
        - `request`: HTTP-запрос, может содержать `?page=`.

        Возвращает:
        - HTML со списком статей текущей страницы.

        Исключения и особые случаи:
        - при некорректном `page` используется ближайшая валидная страница.

        Побочные эффекты:
        - отсутствуют.
        """

        articles = list(EncyclopediaArticle.objects.filter(is_published=True).order_by("id"))
        articles.sort(key=encyclopedia_title_sort_key)

        paginator = Paginator(articles, 10)
        page_obj = paginator.get_page(request.GET.get("page"))

        return render(
            request,
            self.template_name,
            {
                "page_obj": page_obj,
                "articles": page_obj.object_list,
            },
        )


class EncyclopediaDetailView(LoginRequiredMixin, View):
    """Показывает детальную страницу опубликованной статьи энциклопедии.

    Контекст использования:
    - открывается по маршруту `/encyclopedia/<slug>/`.

    Параметры:
    - `slug` статьи из URL.

    Возвращает:
    - HTML-страницу `encyclopedia/detail.html`.

    Исключения и особые случаи:
    - неопубликованные статьи недоступны пользователю (404).

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "encyclopedia/detail.html"

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        """Рендерит страницу одной опубликованной статьи по её slug.

        Контекст использования:
        - endpoint детальной страницы энциклопедии.

        Параметры:
        - `request`: текущий HTTP-запрос;
        - `slug`: URL-идентификатор статьи.

        Возвращает:
        - HTML с заголовком и содержимым статьи.

        Исключения и особые случаи:
        - для неопубликованной/несуществующей статьи возвращается 404.

        Побочные эффекты:
        - отсутствуют.
        """

        article = get_object_or_404(EncyclopediaArticle, slug=slug, is_published=True)
        return render(request, self.template_name, {"article": article})
