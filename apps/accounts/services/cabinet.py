"""Сервисы формирования данных личного кабинета пользователя."""

from apps.core.enums import AnalysisRunStatus, DialogStatus
from apps.dialogs.models import DialogSession


def build_cabinet_dashboard(user) -> dict:
    """Собирает упрощённые метрики и историю сессий для личного кабинета.

    Контекст использования:
    - вызывается view личного кабинета для отображения базовой статистики и истории игр;
    - реализует новый формат кабинета без рейтингов и агрегированных баллов аналитики.

    Параметры:
    - `user`: авторизованный пользователь, для которого строятся данные кабинета.

    Возвращает:
    - словарь с количеством завершённых/незавершённых сессий и историей сессий пользователя.

    Исключения и особые случаи:
    - при отсутствии сессий возвращаются нулевые значения и пустая история.

    Побочные эффекты:
    - отсутствуют.
    """

    all_sessions_qs = DialogSession.objects.filter(user=user).select_related("game", "scenario", "analysis_run")
    total_sessions = all_sessions_qs.count()
    completed_sessions = all_sessions_qs.filter(status=DialogStatus.FINISHED).count()
    unfinished_sessions = total_sessions - completed_sessions

    history_sessions = list(all_sessions_qs.order_by("-ended_at", "-started_at", "-id"))

    completed_with_analysis = 0
    for session in history_sessions:
        run = getattr(session, "analysis_run", None)
        has_analysis = bool(run and run.status == AnalysisRunStatus.COMPLETED)
        session.has_analysis_result = has_analysis
        if has_analysis:
            completed_with_analysis += 1

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "unfinished_sessions": unfinished_sessions,
        "completed_with_analysis": completed_with_analysis,
        "history_sessions": history_sessions,
    }
