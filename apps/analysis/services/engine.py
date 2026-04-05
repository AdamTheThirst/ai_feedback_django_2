"""Сервис запуска аналитики по завершённому диалогу и сохранения текстовых ответов модели."""

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
    """Описывает нормализованный результат обработки текстового ответа аналитической модели.

    Контекст использования:
    - используется как типизированный контракт между обработчиком ответа LLM и движком сохранения результата.

    Параметры:
    - `status`: итоговый статус валидации;
    - `rating`: техническое значение рейтинга для совместимости с текущей схемой БД;
    - `text`: финальный текст аналитического комментария;
    - `normalized_json`: всегда `None`, так как анализ хранится как обычный текст;
    - `error_message`: техническое описание причины ошибки.

    Возвращает:
    - dataclass-объект для единообразной обработки результата.

    Исключения и особые случаи:
    - допускает `normalized_json=None` для всех ответов новой текстовой схемы.

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
    """Нормализует текстовый ответ аналитической модели без JSON-парсинга.

    Контекст использования:
    - применяется движком анализа для каждого ответа LLM;
    - реализует новый контракт: модель возвращает обычный текст аналитики.

    Параметры:
    - `raw_response_text`: сырой текст ответа модели;
    - `rating_min`: минимальный балл шкалы критерия (технический параметр совместимости);
    - `rating_max`: максимальный балл шкалы критерия (технический параметр совместимости).

    Возвращает:
    - `ParsedAnalysisResponse` со статусом `valid` или `invalid_schema` для пустого ответа.

    Исключения и особые случаи:
    - пустой или пробельный ответ помечается как невалидный и заменяется fallback-текстом.

    Побочные эффекты:
    - отсутствуют.
    """

    _ = rating_max
    cleaned_text = (raw_response_text or "").strip()
    if not cleaned_text:
        return ParsedAnalysisResponse(
            status=AnalysisValidationStatus.INVALID_SCHEMA,
            rating=rating_min,
            text="Не удалось получить текст аналитики.",
            normalized_json=None,
            error_message="Пустой текстовый ответ аналитической модели.",
        )

    return ParsedAnalysisResponse(
        status=AnalysisValidationStatus.VALID,
        rating=rating_min,
        text=cleaned_text,
        normalized_json=None,
        error_message="",
    )


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
    - используется движком аналитики для логирования старта, ошибок и невалидных ответов.

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
    - сохраняет текстовые ответы аналитики в `AnalysisResult`.

    Параметры:
    - `dialog`: завершённая или прерванная сессия.

    Возвращает:
    - созданный/обновлённый `AnalysisRun`, либо `None`, если анализ не должен запускаться.

    Исключения и особые случаи:
    - при отсутствии пользовательских реплик возвращает `None` без создания `AnalysisRun`;
    - при пустом ответе модели создаёт `AnalysisResult` со статусом `fallback_saved`.

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
                    event_type="analysis.invalid_text",
                    message="Ответ аналитической модели пустой, сохранён fallback.",
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
