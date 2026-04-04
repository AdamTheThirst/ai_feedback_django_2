"""Сервис оркестрации отправки сообщений в активном диалоге."""

import uuid

from django.core.cache import cache
from django.db import transaction

from apps.core.enums import DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession
from apps.integrations.services.llm_chat import generate_game_reply


class DialogSendMessageError(Exception):
    """Ошибка сервисного уровня при отправке сообщения в диалоге.

    Контекст использования:
    - выбрасывается, когда действие отправки сообщения недопустимо в текущем состоянии.

    Параметры:
    - принимает текст причины ошибки в стандартном механизме исключений Python.

    Возвращает:
    - экземпляр исключения для передачи в API-слой.

    Исключения и особые случаи:
    - используется только в рамках модуля dialogs.

    Побочные эффекты:
    - отсутствуют.
    """


def dialog_send_lock_key(dialog_id: int) -> str:
    """Возвращает ключ кэша для краткоживущей блокировки отправки сообщений.

    Контекст использования:
    - защищает от конкурентной двойной отправки в один и тот же диалог.

    Параметры:
    - `dialog_id`: внутренний идентификатор диалоговой сессии.

    Возвращает:
    - строковый ключ для работы с кэшем.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    return f"dialog:send-lock:{dialog_id}"


@transaction.atomic
def send_user_message(dialog: DialogSession, text: str, client_message_id: str | None = None) -> dict:
    """Сохраняет пользовательскую реплику, генерирует ответ и возвращает JSON-данные.

    Контекст использования:
    - вызывается API-endpoint-ом отправки сообщений в рамках активного диалога.

    Параметры:
    - `dialog`: активная сессия пользователя;
    - `text`: текст пользовательского сообщения;
    - `client_message_id`: клиентский UUID для idempotency защиты.

    Возвращает:
    - словарь с двумя сообщениями (`user_message`, `assistant_message`) и статусом диалога.

    Исключения и особые случаи:
    - `DialogSendMessageError`, если диалог не активен, сообщение пустое или запрос конкурентный.

    Побочные эффекты:
    - создаёт записи `DialogMessage`;
    - изменяет счётчики и технические поля `DialogSession`.
    """

    if dialog.status != DialogStatus.ACTIVE:
        raise DialogSendMessageError("Диалог уже завершён.")

    message_text = (text or "").strip()
    if not message_text:
        raise DialogSendMessageError("Сообщение не может быть пустым.")

    lock_key = dialog_send_lock_key(dialog.id)
    if not cache.add(lock_key, "1", timeout=10):
        raise DialogSendMessageError("Сообщение уже отправляется. Дождитесь ответа.")

    try:
        parsed_client_uuid = None
        if client_message_id:
            parsed_client_uuid = uuid.UUID(client_message_id)
            existing = DialogMessage.objects.filter(dialog=dialog, client_message_id=parsed_client_uuid).first()
            if existing:
                assistant = (
                    DialogMessage.objects.filter(dialog=dialog, sequence_no=existing.sequence_no + 1, role=DialogMessageRole.ASSISTANT)
                    .order_by("id")
                    .first()
                )
                return {
                    "user_message": _message_payload(existing),
                    "assistant_message": _message_payload(assistant) if assistant else None,
                    "dialog_status": dialog.status,
                }

        dialog.pending_response = True
        dialog.last_client_activity_at = dialog.last_client_activity_at or dialog.started_at
        dialog.save(update_fields=["pending_response", "last_client_activity_at", "updated_at"])

        last_sequence = dialog.messages.order_by("-sequence_no").values_list("sequence_no", flat=True).first() or 0
        user_message = DialogMessage.objects.create(
            dialog=dialog,
            sequence_no=last_sequence + 1,
            role=DialogMessageRole.USER,
            text=message_text,
            client_message_id=parsed_client_uuid,
        )

        assistant_text = generate_game_reply(dialog=dialog, user_text=message_text)
        assistant_message = DialogMessage.objects.create(
            dialog=dialog,
            sequence_no=user_message.sequence_no + 1,
            role=DialogMessageRole.ASSISTANT,
            text=assistant_text,
        )

        dialog.user_message_count += 1
        dialog.assistant_message_count += 1
        dialog.pending_response = False
        dialog.last_client_activity_at = assistant_message.created_at
        dialog.save(
            update_fields=[
                "user_message_count",
                "assistant_message_count",
                "pending_response",
                "last_client_activity_at",
                "updated_at",
            ]
        )

        return {
            "user_message": _message_payload(user_message),
            "assistant_message": _message_payload(assistant_message),
            "dialog_status": dialog.status,
        }
    finally:
        cache.delete(lock_key)


def _message_payload(message: DialogMessage | None) -> dict | None:
    """Преобразует сообщение ORM в словарь для JSON-ответа.

    Контекст использования:
    - внутренний helper сервиса отправки сообщений.

    Параметры:
    - `message`: экземпляр `DialogMessage` или `None`.

    Возвращает:
    - словарь с полями сообщения или `None`, если сообщение отсутствует.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    if message is None:
        return None
    return {
        "id": message.id,
        "sequence_no": message.sequence_no,
        "role": message.role,
        "text": message.text,
        "created_at": message.created_at.isoformat(),
    }
