"""Сервис формирования view-model для экрана результатов диалога."""

from apps.dialogs.models import DialogSession


def build_dialog_results_view_model(dialog: DialogSession) -> dict:
    """Собирает данные для страницы результата конкретного диалога.

    Контекст использования:
    - вызывается HTML-представлением экрана результатов;
    - возвращает карточки текстовой аналитики без числовых оценок.

    Параметры:
    - `dialog`: завершённая диалоговая сессия пользователя.

    Возвращает:
    - словарь с метаданными диалога и массивом карточек анализа.

    Исключения и особые случаи:
    - если `AnalysisRun` отсутствует, возвращается контролируемое пустое состояние.

    Побочные эффекты:
    - отсутствуют.
    """

    analysis_run = getattr(dialog, "analysis_run", None)
    if not analysis_run:
        return {
            "analysis_run": None,
            "cards": [],
            "empty_state_message": "Для этого диалога анализ не формировался.",
        }

    cards = list(analysis_run.results.order_by("sort_order_snapshot", "id"))

    return {
        "analysis_run": analysis_run,
        "cards": cards,
        "empty_state_message": "",
    }
