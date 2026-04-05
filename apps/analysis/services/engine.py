"""Сервис запуска аналитики по завершённому диалогу и валидации JSON-ответов."""

import json
import traceback
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.auditlog.models import AuditLogEntry
from apps.content.models import AnalysisPrompt
from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus, AuditLogLevel, DialogMessageRole
from apps.dialogs.models import DialogSession
from apps.integrations.services.llm_chat import generate_analysis_reply


@dataclass
class ParsedAnalysisResponse:
    """Описывает нормализованный результат парсинга ответа аналитической модели.

    Контекст использования:
    - используется как типизированный контракт между парсером JSON и движком сохранения результата.

    Параметры:
    - `status`: итоговый статус валидации;
    - `rating`: оценка по критерию;
    - `text`: текст аналитического комментария;
    - `normalized_json`: валидный нормализованный JSON при успешном разборе;
    - `error_message`: техническое описание причины ошибки.

    Возвращает:
    - dataclass-объект для единообразной обработки результата.

    Исключения и особые случаи:
    - допускает `normalized_json=None` для невалидных ответов.

    Побочные эффекты:
    - отсутствуют.
    """

    status: str
    rating: int
    text: str
    normalized_json: dict | None
    error_message: str


def build_dialog_transcript(dialog: DialogSession) -> str:
    """Собирает полный транскрипт диалога для передачи в аналитический LLM-вызов.

    Контекст использования:
    - вызывается перед обработкой каждого `AnalysisPrompt`;
    - обеспечивает единый формат контекста для аналитики.

    Параметры:
    - `dialog`: завершённая или прерванная диалоговая сессия.

    Возвращает:
    - строку транскрипта в хронологическом порядке с префиксами ролей.

    Исключения и особые случаи:
    - если сообщений нет, возвращает пустую строку.

    Побочные эффекты:
    - отсутствуют.
    """

    lines = []
    for message in dialog.messages.order_by("sequence_no", "id"):
        role = "Пользователь" if message.role == DialogMessageRole.USER else "Персонаж"
        lines.append(f"{role}: {message.text}")
    return "\n".join(lines)


def parse_analysis_response(raw_response_text: str, rating_min: int, rating_max: int) -> ParsedAnalysisResponse:
    """Валидирует и нормализует JSON-ответ аналитической модели.

    Контекст использования:
    - применяется движком анализа для каждого ответа LLM;
    - реализует обязательный контракт `{rating, text}` и диапазонную проверку рейтинга.

    Параметры:
    - `raw_response_text`: сырой ответ модели;
    - `rating_min`: минимально допустимый балл;
    - `rating_max`: максимально допустимый балл.

    Возвращает:
    - `ParsedAnalysisResponse` со статусом `valid`, `invalid_json` или `invalid_schema`.

    Исключения и особые случаи:
    - при невалидной структуре возвращает статус ошибки без исключения наружу.

    Побочные эффекты:
    - отсутствуют.
    """

    normalized_raw = normalize_analysis_json_text(raw_response_text)
    try:
        payload = json.loads(normalized_raw)
    except json.JSONDecodeError as exc:
        return ParsedAnalysisResponse(
            status=AnalysisValidationStatus.INVALID_JSON,
            rating=rating_min,
            text="Не удалось разобрать ответ аналитической модели.",
            normalized_json=None,
            error_message=f"Невалидный JSON: {exc}",
        )

    if not isinstance(payload, dict):
        return ParsedAnalysisResponse(
            status=AnalysisValidationStatus.INVALID_SCHEMA,
            rating=rating_min,
            text="Ответ аналитической модели имеет неверную структуру.",
            normalized_json=None,
            error_message="Корневой элемент JSON должен быть объектом.",
        )

    rating = payload.get("rating")
    text = payload.get("text")
    if not isinstance(rating, int) or not isinstance(text, str) or not text.strip():
        return ParsedAnalysisResponse(
            status=AnalysisValidationStatus.INVALID_SCHEMA,
            rating=rating_min,
            text="Ответ аналитической модели имеет неверную схему.",
            normalized_json=None,
            error_message="Ожидались поля rating:int и text:str (непустой).",
        )
    if rating < rating_min or rating > rating_max:
        return ParsedAnalysisResponse(
            status=AnalysisValidationStatus.INVALID_SCHEMA,
            rating=rating_min,
            text="Оценка в ответе аналитической модели вне допустимого диапазона.",
            normalized_json=None,
            error_message=f"rating={rating} вне диапазона [{rating_min}, {rating_max}]",
        )

    normalized = {"rating": rating, "text": text.strip()}
    return ParsedAnalysisResponse(
        status=AnalysisValidationStatus.VALID,
        rating=rating,
        text=text.strip(),
        normalized_json=normalized,
        error_message="",
    )


def normalize_analysis_json_text(raw_response_text: str) -> str:
    """Нормализует сырой ответ LLM к JSON-строке для парсинга.

    Контекст использования:
    - применяется перед `json.loads` в аналитическом парсере;
    - повышает устойчивость к форматам вида ```json ... ``` и к тексту вокруг JSON.

    Параметры:
    - `raw_response_text`: исходный текст ответа LLM.

    Возвращает:
    - строку, максимально близкую к JSON-объекту.

    Исключения и особые случаи:
    - если не удаётся выделить объект, возвращает исходную строку.

    Побочные эффекты:
    - отсутствуют.
    """

    raw = (raw_response_text or "").strip()
    if not raw:
        return raw

    if raw.startswith("```"):
        lines = [line for line in raw.splitlines() if not line.strip().startswith("```")]
        raw = "\n".join(lines).strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def log_audit_event(
    *,
    level: str,
    event_type: str,
    message: str,
    dialog: DialogSession | None = None,
    analysis_run: AnalysisRun | None = None,
    context_json: dict | None = None,
    traceback_text: str = "",
) -> AuditLogEntry:
    """Создаёт запись в audit log для технического события анализа.

    Контекст использования:
    - используется движком аналитики для логирования старта, ошибок и невалидных JSON-ответов.

    Параметры:
    - `level`, `event_type`, `message`: базовые атрибуты события;
    - `dialog`, `analysis_run`: связанные сущности;
    - `context_json`: структурированный контекст;
    - `traceback_text`: стек ошибки при исключении.

    Возвращает:
    - созданную запись `AuditLogEntry`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - записывает событие в БД.
    """

    return AuditLogEntry.objects.create(
        level=level,
        event_type=event_type,
        message=message,
        dialog=dialog,
        analysis_run=analysis_run,
        context_json=context_json,
        traceback_text=traceback_text,
    )


@transaction.atomic
def run_analysis_for_dialog(dialog: DialogSession) -> AnalysisRun | None:
    """Запускает анализ завершённого диалога по всем активным `AnalysisPrompt` игры.

    Контекст использования:
    - вызывается после завершения/прерывания диалога, если есть пользовательские реплики;
    - реализует сохранение `AnalysisRun` и `AnalysisResult` в рамках серверного lifecycle.

    Параметры:
    - `dialog`: завершённая или прерванная сессия.

    Возвращает:
    - созданный/обновлённый `AnalysisRun`, либо `None`, если анализ не должен запускаться.

    Исключения и особые случаи:
    - при отсутствии пользовательских реплик возвращает `None` без создания `AnalysisRun`;
    - при невалидном JSON создаёт `AnalysisResult` со статусом `fallback_saved`.

    Побочные эффекты:
    - создаёт/обновляет `AnalysisRun`, `AnalysisResult` и `AuditLogEntry` в БД.
    """

    if dialog.user_message_count <= 0:
        return None

    prompts = AnalysisPrompt.objects.filter(
        game=dialog.game,
        is_active=True,
        is_archived=False,
    ).order_by("sort_order", "id")

    analysis_run, _ = AnalysisRun.objects.get_or_create(
        dialog=dialog,
        defaults={
            "status": AnalysisRunStatus.PENDING,
            "started_at": timezone.now(),
        },
    )
    analysis_run.status = AnalysisRunStatus.RUNNING
    analysis_run.started_at = analysis_run.started_at or timezone.now()
    analysis_run.finished_at = None
    analysis_run.error_code = ""
    analysis_run.error_message = ""
    analysis_run.save(update_fields=["status", "started_at", "finished_at", "error_code", "error_message", "updated_at"])

    log_audit_event(
        level=AuditLogLevel.INFO,
        event_type="analysis.started",
        message="Запущен анализ диалога.",
        dialog=dialog,
        analysis_run=analysis_run,
        context_json={"dialog_public_id": str(dialog.public_id)},
    )

    transcript = build_dialog_transcript(dialog)
    attempts_total = 0

    try:
        for prompt in prompts:
            attempts_total += 1
            raw_response = generate_analysis_reply(dialog=dialog, analysis_prompt=prompt, transcript=transcript)
            parsed = parse_analysis_response(raw_response, prompt.min_rating, prompt.max_rating)

            validation_status = parsed.status
            if parsed.status != AnalysisValidationStatus.VALID:
                validation_status = AnalysisValidationStatus.FALLBACK_SAVED
                log_audit_event(
                    level=AuditLogLevel.WARNING,
                    event_type="analysis.invalid_json",
                    message="Ответ аналитической модели не прошёл валидацию, сохранён fallback.",
                    dialog=dialog,
                    analysis_run=analysis_run,
                    context_json={
                        "analysis_prompt_alias": prompt.alias,
                        "reason": parsed.status,
                        "raw_response_excerpt": (raw_response or "")[:500],
                    },
                )

            AnalysisResult.objects.update_or_create(
                analysis_run=analysis_run,
                analysis_prompt=prompt,
                defaults={
                    "sort_order_snapshot": prompt.sort_order,
                    "alias_snapshot": prompt.alias,
                    "title_snapshot": prompt.title,
                    "header_snapshot_text": prompt.header_text,
                    "comment_snapshot_text": prompt.comment_text,
                    "rating": parsed.rating,
                    "rating_min": prompt.min_rating,
                    "rating_max": prompt.max_rating,
                    "analysis_text": parsed.text,
                    "raw_llm_response_text": raw_response,
                    "parsed_json_snapshot": parsed.normalized_json,
                    "validation_status": validation_status,
                    "validation_error_message": parsed.error_message,
                    "llm_attempt_count": 1,
                },
            )

        analysis_run.llm_attempt_count = attempts_total
        analysis_run.status = AnalysisRunStatus.COMPLETED
        analysis_run.finished_at = timezone.now()
        analysis_run.save(update_fields=["llm_attempt_count", "status", "finished_at", "updated_at"])
        return analysis_run
    except Exception as exc:
        analysis_run.status = AnalysisRunStatus.FAILED
        analysis_run.finished_at = timezone.now()
        analysis_run.error_code = "analysis_engine_error"
        analysis_run.error_message = str(exc)
        analysis_run.llm_attempt_count = attempts_total
        analysis_run.save(
            update_fields=[
                "status",
                "finished_at",
                "error_code",
                "error_message",
                "llm_attempt_count",
                "updated_at",
            ]
        )
        log_audit_event(
            level=AuditLogLevel.ERROR,
            event_type="analysis.failed",
            message="Анализ завершился ошибкой.",
            dialog=dialog,
            analysis_run=analysis_run,
            context_json={"dialog_public_id": str(dialog.public_id), "error": str(exc)},
            traceback_text=traceback.format_exc(),
        )
        return analysis_run
