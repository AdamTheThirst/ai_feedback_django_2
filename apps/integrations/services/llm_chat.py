"""Временные адаптеры генерации игровых и аналитических реплик для V1."""

import json

from apps.content.models import AnalysisPrompt
from apps.dialogs.models import DialogSession


def generate_game_reply(dialog: DialogSession, user_text: str) -> str:
    """Формирует ответ персонажа на основе пользовательской реплики.

    Контекст использования:
    - вызывается JSON-endpoint отправки сообщений в диалоге;
    - служит временной реализацией до подключения внешнего LLM-клиента.

    Параметры:
    - `dialog`: активная сессия диалога;
    - `user_text`: последняя реплика пользователя.

    Возвращает:
    - текст ответа ассистента для сохранения в `DialogMessage`.

    Исключения и особые случаи:
    - если пользовательская реплика пустая, возвращается уточняющий ответ.

    Побочные эффекты:
    - отсутствуют.
    """

    trimmed = (user_text or "").strip()
    if not trimmed:
        return "Пожалуйста, сформулируйте вашу мысль, и мы продолжим диалог."

    return (
        f"Я услышал вас: «{trimmed}». "
        "Уточните, пожалуйста, какой конкретный результат вы ожидаете после этой обратной связи?"
    )


def generate_analysis_reply(dialog: DialogSession, analysis_prompt: AnalysisPrompt, transcript: str) -> str:
    """Возвращает временный JSON-ответ для аналитического критерия.

    Контекст использования:
    - вызывается сервисом `AnalysisService` для каждого активного `AnalysisPrompt`;
    - в текущей итерации заменяет реальный вызов внешней LLM.

    Параметры:
    - `dialog`: анализируемая сессия;
    - `analysis_prompt`: критерий оценки;
    - `transcript`: полный транскрипт диалога.

    Возвращает:
    - строку JSON c полями `rating` и `text`.

    Исключения и особые случаи:
    - если транскрипт пустой, возвращается минимальная оценка.

    Побочные эффекты:
    - отсутствуют.
    """

    transcript_length = len((transcript or "").strip())
    if transcript_length == 0:
        rating_value = analysis_prompt.min_rating
        text_value = "Диалог не содержит реплик для полноценного анализа."
    else:
        rating_value = min(analysis_prompt.max_rating, max(analysis_prompt.min_rating, analysis_prompt.min_rating + 1))
        text_value = (
            f"Критерий «{analysis_prompt.title}»: пользователь поддерживал диалог и демонстрировал рабочую коммуникацию. "
            "Рекомендуется уточнять ожидания и завершать сообщение конкретным действием."
        )

    return json.dumps({"rating": rating_value, "text": text_value}, ensure_ascii=False)



def generate_encyclopedia_summary(title: str, body: str) -> str:
    """Генерирует краткое описание статьи энциклопедии в деловом стиле.

    Контекст использования:
    - вызывается административными сервисами энциклопедии для автозаполнения поля `summary`.

    Параметры:
    - `title`: заголовок статьи;
    - `body`: полный текст статьи.

    Возвращает:
    - краткий текст summary на русском языке длиной до 255 символов.

    Исключения и особые случаи:
    - если входные данные пустые, возвращается безопасный технический fallback.

    Побочные эффекты:
    - отсутствуют.
    """

    clean_title = (title or "").strip() or "Материал"
    clean_body = " ".join((body or "").split())
    if not clean_body:
        return f"Статья «{clean_title}» описывает ключевые понятия и даёт краткие практические ориентиры по теме материала."

    summary = f"Статья «{clean_title}» объясняет основные идеи и практические шаги по теме, выделяя важные акценты и ожидаемые результаты применения рекомендаций."
    return summary[:255]
