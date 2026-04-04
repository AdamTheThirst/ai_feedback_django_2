# Минимальный примерный код для подключения к AI

```python
# Настройка клиента для vLLM
client = OpenAI(
    base_url="https://...",  # URL вашего vLLM сервера
    api_key="" 
)


try:
    chat_response = client.chat.completions.create(
        model="Qwen/Qwen3-32B",
        messages=[
            {"role": "system", "content": "Вы - роль"},
            {"role": "user", "content": "Сообщение пользователя"}
        ],
        max_tokens=400,
        temperature=0.7,
        top_p=0.8
    )
    
    print("\nОтвет (chat completion):")
    print(chat_response.choices[0].message.content)
    
except Exception as chat_error:
    print(f"Ошибка при chat completion запросе: {chat_error}")
```

# Universal guide: how to connect Django to AI (OpenAI-compatible API)

Этот файл можно положить в **любой Django-проект** как универсальную инструкцию для разработчика (и для Codex), чтобы быстро и предсказуемо подключить AI.

---

## 1) Что нужно подготовить заранее

Минимум:

- Django-проект (любой структуры)
- OpenAI-compatible endpoint (OpenAI, vLLM, LiteLLM gateway, proxy и т.д.)
- API ключ
- выбранная модель

Важно:

- Для большинства OpenAI-compatible серверов нужен путь вида `/v1` в базовом URL.
- Наиболее частая ошибка конфигурации — неправильный endpoint (например, без `/v1`).

---

## 2) Рекомендуемый контракт переменных окружения

Используйте `.env` и держите все чувствительные данные там.

```env
AI_BASE_URL=https://your-endpoint.example.com/v1
AI_API_KEY=your_api_key
AI_MODEL=model_name
AI_TIMEOUT_SECONDS=60
```

Рекомендации:

- Не храните ключи в коде.
- Для разных сред делайте разные `.env` (dev/stage/prod).
- Если у вас внутренний gateway, всё равно соблюдайте тот же контракт переменных.

---

## 3) Подключение `.env` в Django settings

Пример универсального подхода:

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

AI_BASE_URL = os.getenv("AI_BASE_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "")
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
```

Проверьте, что библиотека для `.env` установлена (`python-dotenv`).

---

## 4) Универсальный сервисный слой (рекомендуемая архитектура)

Создайте отдельный модуль/сервис, например:

- `apps/common/ai_service.py`
- или `core/services/ai.py`
- или любой аналогичный слой

Задачи сервиса:

1. Проверить обязательные настройки (`AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`).
2. Собрать `messages` для LLM.
3. Выполнить запрос к AI.
4. Вернуть чистый текст ответа.
5. Бросать осмысленные исключения (не прятать их полностью в сервисе).

Базовый пример:

```python
from django.conf import settings
from openai import OpenAI


def ask_ai(messages: list[dict], temperature: float = 0.7, max_tokens: int = 400) -> str:
    if not settings.AI_BASE_URL:
        raise ValueError("AI_BASE_URL is not configured")
    if not settings.AI_API_KEY:
        raise ValueError("AI_API_KEY is not configured")
    if not settings.AI_MODEL:
        raise ValueError("AI_MODEL is not configured")

    client = OpenAI(base_url=settings.AI_BASE_URL.rstrip("/"), api_key=settings.AI_API_KEY)

    response = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content or ""
```

---

## 5) Как формировать `messages` правильно

Рекомендуемый порядок:

1. `system` (мастер-промпт)
2. история диалога (если есть)
3. текущее сообщение пользователя

Пример:

```python
messages = [
    {"role": "system", "content": settings.AI_MASTER_PROMPT},
    *history_messages,
    {"role": "user", "content": user_text},
]
```

Где `history_messages` обычно ограничивается по объёму (например, последние 10–30 пар), чтобы не раздувать токены.

---

## 6) Хранение истории диалога (универсальные варианты)

Можно использовать:

- SQLite/PostgreSQL/MySQL (через обычную Django-модель)

Минимум полей для БД:

- `id`
- `created_at`
- `role` (`user` / `assistant`)
- `content`

Практика:

- При отправке сообщения: сначала сохраните user-реплику.
- После ответа модели: сохраните assistant-реплику.
- Для контекста выбирайте последние N пар.

---

## 7) Обработка ошибок и типовые причины проблем

### Частые причины

1. Неверный `AI_BASE_URL` (особенно отсутствует `/v1`)
2. Неверный API ключ
3. Неверное имя модели
4. Endpoint не поддерживает `chat.completions`
5. Таймаут/сетевые ограничения

### Что делать

- Логировать HTTP-статус и краткое тело ошибки (без утечки ключа).
- Возвращать пользователю безопасное сообщение вида «Временная ошибка AI-сервиса».
- Для `405 Method Not Allowed` первым делом проверить endpoint и метод.

---

## 8) Рекомендации по безопасности

- Никогда не отдавайте API ключ во фронтенд.
- Запрос к AI выполняйте только на backend.
- Скрывайте stack trace от конечного пользователя.
- Фильтруйте/маскируйте чувствительные данные в логах.
- Для production добавьте rate limiting и аудит запросов.

---

## 9) Рекомендации для Codex/агентов (чтобы быстрее интегрировать в любой проект)

Если этот файл читает агент:

1. Найди `settings.py` и добавь чтение env-переменных `AI_*`.
2. Найди/создай сервисный слой для запроса к AI (не смешивай с view).
3. Проверь, где хранится история сообщений, и добавь выборку последних N пар в контекст.
4. Убедись, что endpoint чата вызывает сервис и корректно обрабатывает исключения.
5. Добавь `.env.example` с `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`, `AI_MASTER_PROMPT`.
6. Не хардкодь URL/ключ/модель в коде.

---

## 10) Мини-чеклист перед запуском

- [ ] `AI_BASE_URL` корректен (обычно с `/v1`)
- [ ] `AI_API_KEY` валиден
- [ ] `AI_MODEL` существует на сервере
- [ ] backend может достучаться до endpoint по сети
- [ ] в логах видно входящий запрос и ответ AI без секретов
- [ ] фронт не содержит ключей

---

## 11) Мини-чеклист для production

- [ ] `DEBUG=False`
- [ ] секреты только в защищённом хранилище/переменных окружения
- [ ] централизованное логирование
- [ ] ограничение частоты запросов
- [ ] мониторинг ошибок AI (4xx/5xx/timeout)
- [ ] fallback/деградация при недоступности модели

---

## 12) Быстрая диагностика 405

Если видите:

`405 Method Not Allowed`

проверьте по порядку:

1. Базовый URL (часто нужна версия `/v1`)
2. Что вызывается именно `POST` endpoint chat completions
3. Что ваш proxy/gateway не блокирует `POST`
4. Что backend и endpoint используют совместимый OpenAI API формат
