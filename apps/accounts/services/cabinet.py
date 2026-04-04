"""Сервисы формирования данных личного кабинета пользователя."""

from collections import defaultdict

from apps.analysis.models import AnalysisResult
from apps.core.enums import AnalysisRunStatus, DialogStatus
from apps.dialogs.models import DialogSession


def build_cabinet_dashboard(user) -> dict:
    """Собирает агрегированные показатели, индикаторы и историю игр пользователя.

    Контекст использования:
    - вызывается view личного кабинета для рендера карточек «Мои показатели»;
    - формирует данные сильных/западающих индикаторов и историю завершённых игр с анализом.

    Параметры:
    - `user`: авторизованный пользователь, для которого строится дашборд.

    Возвращает:
    - словарь со статистикой, списками индикаторов и queryset истории.

    Исключения и особые случаи:
    - при отсутствии завершённых сессий с анализом возвращаются нулевые и пустые состояния.

    Побочные эффекты:
    - отсутствуют.
    """

    all_sessions_qs = DialogSession.objects.filter(user=user)
    total_sessions = all_sessions_qs.count()
    interrupted_attempts = all_sessions_qs.filter(status=DialogStatus.ABORTED).count()

    analyzed_sessions = list(
        DialogSession.objects.filter(user=user, analysis_run__status=AnalysisRunStatus.COMPLETED)
        .select_related("game", "scenario", "analysis_run")
        .order_by("-ended_at", "-id")
    )

    session_scores = []
    for session in analyzed_sessions:
        results = list(session.analysis_run.results.all())
        n_score = sum(item.rating for item in results)
        m_score = sum(item.rating_max for item in results)
        session_scores.append({"session": session, "score_n": n_score, "score_m": m_score})

    average_score = round(sum(item["score_n"] for item in session_scores) / len(session_scores), 2) if session_scores else None
    best_score = max((item["score_n"] for item in session_scores), default=None)

    by_game = defaultdict(list)
    for item in session_scores:
        game_title = item["session"].game.title if item["session"].game else "Без игры"
        by_game[game_title].append(item["score_n"])
    average_by_game = [
        {"game_title": game_title, "avg_score": round(sum(scores) / len(scores), 2)}
        for game_title, scores in sorted(by_game.items(), key=lambda kv: kv[0].casefold())
    ]

    indicator_rows = AnalysisResult.objects.filter(analysis_run__dialog__user=user, analysis_run__status=AnalysisRunStatus.COMPLETED)

    aggregate = {}
    for row in indicator_rows:
        key = row.alias_snapshot
        if key not in aggregate:
            aggregate[key] = {
                "title": row.title_snapshot,
                "sum": 0,
                "count": 0,
                "low_count": 0,
            }
        aggregate[key]["sum"] += row.rating
        aggregate[key]["count"] += 1
        if row.rating < 3:
            aggregate[key]["low_count"] += 1

    weak_indicators = []
    strong_indicators = []
    for alias, data in aggregate.items():
        avg = round(data["sum"] / data["count"], 2)
        entry = {
            "alias": alias,
            "title": data["title"],
            "avg_rating": avg,
            "count": data["count"],
            "low_count": data["low_count"],
        }
        if data["low_count"] > 0 and avg < 3:
            weak_indicators.append(entry)
        if avg >= 4 and data["low_count"] == 0:
            strong_indicators.append(entry)

    weak_indicators.sort(key=lambda item: (item["avg_rating"], -item["low_count"], item["title"].casefold()))
    strong_indicators.sort(key=lambda item: (-item["avg_rating"], -item["count"], item["title"].casefold()))

    return {
        "total_sessions": total_sessions,
        "completed_sessions": len(analyzed_sessions),
        "interrupted_attempts": interrupted_attempts,
        "average_score": average_score,
        "best_score": best_score,
        "average_by_game": average_by_game,
        "weak_indicators": weak_indicators,
        "strong_indicators": strong_indicators,
        "history_scores": session_scores,
    }
