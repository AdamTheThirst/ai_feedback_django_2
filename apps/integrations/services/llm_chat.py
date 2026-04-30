"""Интеграционный слой OpenAI-compatible LLM для чата, анализа и энциклопедии."""

import json
from dataclasses import dataclass
from urllib import error, request

from django.conf import settings

from apps.content.models import AnalysisPrompt
from apps.dialogs.models import DialogSession


class LLMIntegrationError(Exception):
    """Описывает техническую ошибку при вызове внешнего LLM endpoint.

    Контекст использования:
    - выбрасывается при ошибках сети, таймаутах, невалидном JSON и пустом ответе;
    - используется сервисами higher-level уровня для корректной бизнес-обработки.

    Параметры:
    - текст ошибки передаётся стандартным механизмом исключений Python.

    Возвращает:
    - экземпляр исключения для обработки в вызывающем слое.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """


@dataclass
class LLMGameReply:
    """Хранит ответ LLM для игрового чата и статус подключения.

    Контекст использования:
    - возвращается из `generate_game_reply` в сервис отправки сообщения;
    - позволяет показать пользователю статус подключения прямо в ленте диалога.

    Параметры:
    - `text`: текст ассистента;
    - `status_text`: строка вида «LLM подключен: <model>».

    Возвращает:
    - dataclass-объект с данными генерации.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    text: str
    status_text: str


def _llm_runtime_config() -> tuple[str, str, str, int]:
    """Возвращает обязательные настройки LLM из Django settings.

    Контекст использования:
    - единая точка чтения runtime-конфига для всех LLM-вызовов;
    - поддерживает одновременно новые переменные и legacy-алиасы.

    Параметры:
    - отсутствуют.

    Возвращает:
    - `(base_url, api_key, model_name, timeout_seconds)`.

    Исключения и особые случаи:
    - выбрасывает `LLMIntegrationError`, если любой обязательный параметр пустой.

    Побочные эффекты:
    - отсутствуют.
    """

    base_url = (
        getattr(settings, "LLM_BASE_URL", "")
        or getattr(settings, "AI_BASE_URL", "")
        or ""
    ).strip().rstrip("/")
    api_key = (
        getattr(settings, "LLM_API_KEY", "")
        or getattr(settings, "AI_API_KEY", "")
        or ""
    ).strip()
    model_name = (
        getattr(settings, "AI_MODEL_NAME", "")
        or getattr(settings, "LLM_MODEL_NAME", "")
        or getattr(settings, "AI_MODEL", "")
        or ""
    ).strip()
    timeout_seconds = int(
        getattr(settings, "LLM_TIMEOUT_SECONDS", 0)
        or getattr(settings, "AI_TIMEOUT_SECONDS", 60)
        or 60
    )

    if not base_url:
        raise LLMIntegrationError("LLM_BASE_URL не настроен.")
    if not api_key:
        raise LLMIntegrationError("LLM_API_KEY не настроен.")
    if not model_name:
        raise LLMIntegrationError("AI_MODEL_NAME не настроен.")

    return base_url, api_key, model_name, timeout_seconds


def _chat_completion(messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 1000) -> tuple[str, str]:
    """Выполняет запрос к OpenAI-compatible `/chat/completions`.

    Контекст использования:
    - общий транспортный вызов для игровых и аналитических генераций;
    - отделяет сетевую часть от бизнес-функций адаптера.

    Параметры:
    - `messages`: сообщения формата Chat Completions;
    - `temperature`: параметр креативности;
    - `max_tokens`: ограничение на длину ответа.

    Возвращает:
    - кортеж `(content, status_text)`.

    Исключения и особые случаи:
    - `LLMIntegrationError` при любых технических проблемах вызова.

    Побочные эффекты:
    - выполняет HTTP-запрос к внешнему LLM-сервису.
    """

    base_url, api_key, model_name, timeout_seconds = _llm_runtime_config()
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = request.Request(
        url=f"{base_url}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.URLError as exc:
        raise LLMIntegrationError(f"Ошибка подключения к LLM: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMIntegrationError(f"LLM вернул невалидный JSON: {exc}") from exc

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMIntegrationError("LLM не вернул choices в ответе.")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise LLMIntegrationError("LLM вернул пустой ответ.")

    return content.strip(), f"LLM подключен: {model_name}"


def _dialog_messages_for_llm(dialog: DialogSession, user_text: str) -> list[dict[str, str]]:
    """Собирает контекст сообщений для генерации ответа персонажа.

    Контекст использования:
    - вызывается перед `generate_game_reply`;
    - гарантирует, что системный промт и история диалога передаются в LLM.

    Параметры:
    - `dialog`: активная сессия;
    - `user_text`: новая реплика пользователя.

    Возвращает:
    - список сообщений формата OpenAI-compatible API.

    Исключения и особые случаи:
    - если в сессии нет `scenario_prompt_used`, применяется безопасный fallback-промт.

    Побочные эффекты:
    - отсутствуют.
    """

    scenario_prompt = (dialog.scenario_prompt_used.prompt_text if dialog.scenario_prompt_used else "").strip()
    if not scenario_prompt:
        scenario_prompt = (
            "Ты — персонаж тренажёра обратной связи. "
            "Отвечай в рамках условий сценария, поддерживай деловой и реалистичный тон."
        )

    messages = [{"role": "system", "content": scenario_prompt}]
    for message in dialog.messages.order_by("sequence_no", "id"):
        role = "user" if message.role == "user" else "assistant"
        messages.append({"role": role, "content": message.text})
    messages.append({"role": "user", "content": user_text})
    return messages


def generate_game_reply(dialog: DialogSession, user_text: str) -> LLMGameReply:
    """Генерирует игровой ответ персонажа через подключенный LLM.

    Контекст использования:
    - вызывается endpoint-ом отправки сообщений в чате;
    - формирует ответ только через внешний LLM, без локальных заглушек.

    Параметры:
    - `dialog`: активная сессия диалога;
    - `user_text`: текст новой реплики пользователя.

    Возвращает:
    - `LLMGameReply` с ответом персонажа и строкой статуса подключения.

    Исключения и особые случаи:
    - при отсутствии текста возвращает мягкое уточнение без LLM-вызова;
    - при технической ошибке выбрасывает `LLMIntegrationError`.

    Побочные эффекты:
    - выполняет внешний HTTP-вызов LLM.
    """

    trimmed = (user_text or "").strip()
    if not trimmed:
        return LLMGameReply(
            text="Пожалуйста, сформулируйте вашу мысль, и мы продолжим диалог.",
            status_text="LLM не использован: пустая реплика.",
        )

    content, status_text = _chat_completion(
        messages=_dialog_messages_for_llm(dialog=dialog, user_text=trimmed),
        temperature=0.4,
        max_tokens=700,
    )
    return LLMGameReply(text=content, status_text=status_text)


def generate_analysis_reply(dialog: DialogSession, analysis_prompt: AnalysisPrompt, transcript: str) -> str:
    """Запрашивает у LLM текст аналитики по одному критерию.

    Контекст использования:
    - вызывается сервисом аналитики для каждого `AnalysisPrompt`;
    - на выходе должен быть обычный текст аналитики.

    Параметры:
    - `dialog`: анализируемая сессия;
    - `analysis_prompt`: критерий и диапазон оценки;
    - `transcript`: полный транскрипт диалога.

    Возвращает:
    - строку текста для сохранения в карточке анализа.

    Исключения и особые случаи:
    - при ошибке LLM возвращает fallback-текст о недоступности аналитики.

    Побочные эффекты:
    - выполняет внешний HTTP-вызов LLM.
    """

    analysis_instruction = (
        f"Сделай разбор диалога по критерию «{analysis_prompt.title}».\n"
        f"Инструкция критерия:\n{analysis_prompt.prompt_text}\n"
        "Верни только текст аналитики без JSON-обёртки."
    )
    messages = [
        {"role": "system", "content": analysis_instruction},
        {
            "role": "user",
            "content": f"Игра: {dialog.game.title if dialog.game else 'Не указана'}\nТранскрипт:\n{transcript}",
        },
    ]
    try:
        content, _ = _chat_completion(messages=messages, temperature=0.1, max_tokens=analysis_prompt.max_tokens)
        return content
    except LLMIntegrationError:
        return "Анализ недоступен из-за ошибки LLM. Повторите позже."


def generate_encyclopedia_summary(title: str, body: str) -> str:
    """Генерирует краткое summary статьи энциклопедии через LLM.

    Контекст использования:
    - используется в админке при автозаполнении summary.

    Параметры:
    - `title`: заголовок статьи;
    - `body`: полный текст статьи.

    Возвращает:
    - summary длиной до 255 символов.

    Исключения и особые случаи:
    - при ошибке LLM возвращает локальный fallback.

    Побочные эффекты:
    - выполняет внешний HTTP-вызов LLM.
    """

    clean_title = (title or "").strip() or "Материал"
    clean_body = " ".join((body or "").split())
    if not clean_body:
        return f"Статья «{clean_title}» описывает ключевые понятия и практические ориентиры по теме."

    messages = [
        {
            "role": "system",
            "content": (
                "Сделай короткое summary статьи на русском языке, "
                "без markdown, одним абзацем, максимум 255 символов."
            ),
        },
        {"role": "user", "content": f"Заголовок: {clean_title}\nТекст:\n{clean_body}"},
    ]
    try:
        content, _ = _chat_completion(messages=messages, temperature=0.2, max_tokens=180)
        return content[:255]
    except LLMIntegrationError:
        return (
            f"Статья «{clean_title}» объясняет основные идеи и предлагает практические шаги "
            "для применения в коммуникации."
        )[:255]
