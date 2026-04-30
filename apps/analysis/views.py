"""HTML-представления модуля анализа результатов диалога."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.core.enums import DialogStatus
from apps.dialogs.models import DialogSession
from apps.exports.services.pdf import build_result_pdf

from .services.results import build_dialog_results_view_model


class DialogResultsView(LoginRequiredMixin, View):
    """Отображает страницу результата конкретного диалога пользователя.

    Контекст использования:
    - открывается после завершения диалога и выполнения аналитики;
    - показывает сумму `N из M` и карточки критериев.

    Параметры:
    - `public_id` диалоговой сессии из URL.

    Возвращает:
    - HTML-страницу `dialogs/results.html`.

    Исключения и особые случаи:
    - доступ ограничен только владельцем диалога;
    - для активного диалога выполняется redirect обратно в чат.

    Побочные эффекты:
    - отсутствуют.
    """

    template_name = "dialogs/results.html"

    def get(self, request: HttpRequest, public_id) -> HttpResponse:
        """Рендерит экран результата для завершённого диалога текущего пользователя.

        Контекст использования:
        - endpoint `GET /dialogs/<dialog_public_id>/results/`.

        Параметры:
        - `request`: HTTP-запрос авторизованного пользователя;
        - `public_id`: внешний UUID диалога.

        Возвращает:
        - HTML со сводкой `N из M` и карточками анализа.

        Исключения и особые случаи:
        - для чужого диалога возвращается 404.

        Побочные эффекты:
        - отсутствуют.
        """

        dialog = get_object_or_404(
            DialogSession.objects.select_related("game", "scenario", "analysis_run"),
            public_id=public_id,
            user=request.user,
        )
        if dialog.status == DialogStatus.ACTIVE:
            return redirect("dialogs:chat", public_id=dialog.public_id)

        view_model = build_dialog_results_view_model(dialog)
        context = {
            "dialog": dialog,
            **view_model,
        }
        return render(request, self.template_name, context)


class DialogExportPdfView(LoginRequiredMixin, View):
    """Формирует и отдаёт PDF-экспорт результата диалога владельцу сессии.

    Контекст использования:
    - вызывается кнопкой «Экспорт результатов в PDF» на странице результатов.

    Параметры:
    - `public_id`: UUID диалоговой сессии.

    Возвращает:
    - `HttpResponse` c контент-типом `application/pdf`.

    Исключения и особые случаи:
    - доступ к чужому диалогу запрещён (404);
    - для активного диалога выполняется redirect в чат.

    Побочные эффекты:
    - отсутствуют.
    """

    def get(self, request: HttpRequest, public_id) -> HttpResponse:
        """Генерирует PDF и возвращает файл в ответе на GET-запрос.

        Контекст использования:
        - endpoint `GET /dialogs/<dialog_public_id>/export-pdf/`.

        Параметры:
        - `request`: HTTP-запрос авторизованного пользователя;
        - `public_id`: внешний UUID диалога.

        Возвращает:
        - PDF-файл с именем `dialog-<public_id>.pdf`.

        Исключения и особые случаи:
        - если диалог активен, пользователь перенаправляется в чат.

        Побочные эффекты:
        - отсутствуют.
        """

        dialog = get_object_or_404(
            DialogSession.objects.select_related("game", "scenario", "analysis_run").prefetch_related("messages"),
            public_id=public_id,
            user=request.user,
        )
        if dialog.status == DialogStatus.ACTIVE:
            return redirect("dialogs:chat", public_id=dialog.public_id)

        pdf_bytes = build_result_pdf(dialog)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="dialog-{dialog.public_id}.pdf"'
        return response
