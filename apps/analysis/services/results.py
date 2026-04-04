"""Сервис формирования view-model для экрана результатов диалога."""

from apps.analysis.models import AnalysisRun
from apps.dialogs.models import DialogSession


def build_dialog_results_view_model(dialog: DialogSession) -> dict:
    """Собирает данные для страницы результата конкретного диалога.

    Контекст использования:
    - вызывается HTML-представлением экрана результатов;
    - агрегирует сумму `N из M`, карточки критериев и признаки частичных ошибок.

    Параметры:
    - `dialog`: завершённая диалоговая сессия пользователя.

    Возвращает:
    - словарь с метаданными диалога, суммой баллов и массивом карточек анализа.

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
            "total_score": 0,
            "max_score": 0,
            "has_partial_issues": False,
            "empty_state_message": "Для этого диалога анализ не формировался.",
        }

    cards = list(analysis_run.results.order_by("sort_order_snapshot", "id"))
    total_score = sum(card.rating for card in cards)
    max_score = sum(card.rating_max for card in cards)
    has_partial_issues = any(card.validation_error_message for card in cards)

    return {
        "analysis_run": analysis_run,
        "cards": cards,
        "total_score": total_score,
        "max_score": max_score,
        "has_partial_issues": has_partial_issues,
        "empty_state_message": "",
    }
