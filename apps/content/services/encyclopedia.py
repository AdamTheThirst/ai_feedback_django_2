"""Сервисы раздела энциклопедии: summary-генерация и сортировка статей."""

import re

from apps.content.models import EncyclopediaArticle
from apps.integrations.services.llm_chat import generate_encyclopedia_summary


def build_article_summary(title: str, body: str) -> str:
    """Генерирует краткое описание статьи энциклопедии через LLM-адаптер.

    Контекст использования:
    - вызывается из административного интерфейса при создании/редактировании статьи.

    Параметры:
    - `title`: заголовок статьи;
    - `body`: основной текст статьи.

    Возвращает:
    - строку summary длиной от 50 до 255 символов.

    Исключения и особые случаи:
    - если LLM вернул слишком короткий текст, применяется технический fallback.

    Побочные эффекты:
    - отсутствуют.
    """

    summary = (generate_encyclopedia_summary(title=title, body=body) or "").strip()
    if len(summary) < 50:
        summary = f"Статья раскрывает тему «{title}» и кратко объясняет ключевые правила и практические рекомендации для применения в работе."
    return summary[:255]


def encyclopedia_title_sort_key(article: EncyclopediaArticle) -> tuple[int, str]:
    """Возвращает ключ сортировки заголовков по правилу: цифры → кириллица → латиница.

    Контекст использования:
    - применяется пользовательским списком статей перед пагинацией.

    Параметры:
    - `article`: экземпляр статьи энциклопедии.

    Возвращает:
    - кортеж `(bucket, normalized_title)` для детерминированной сортировки.

    Исключения и особые случаи:
    - пустой заголовок попадает в латинский bucket как безопасный fallback.

    Побочные эффекты:
    - отсутствуют.
    """

    title = (article.title or "").strip()
    first = title[:1]
    if first.isdigit():
        bucket = 0
    elif re.match(r"[А-Яа-яЁё]", first):
        bucket = 1
    else:
        bucket = 2
    return bucket, title.casefold()
