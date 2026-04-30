# Что поменять для product mode (production)

Ниже таблица с практическими изменениями для прод-режима.

> Да, `DEBUG` тоже включён в таблицу (как ты просил).
> Формат: **файл → строка → текущий параметр → на что поменять**.

| Файл | Строка | Текущий параметр | На что поменять (prod) |
|---|---:|---|---|
| `config/settings/base.py` | 44 | `DEBUG = False` (база) | Оставить `False` в проде. Не включать `True` на сервере. |
| `config/settings/production.py` | 8 | `DEBUG = False` | Оставить `False`. |
| `config/settings/base.py` | 45 | `ALLOWED_HOSTS = []` | В проде использовать реальные хосты через env (`DJANGO_ALLOWED_HOSTS=example.com,www.example.com,IP`). |
| `config/settings/production.py` | 9 | `ALLOWED_HOSTS` читается из `DJANGO_ALLOWED_HOSTS` | В `.env` указать домен/поддомен/IP без пробелов. |
| `config/settings/base.py` | 43 | `SECRET_KEY = "dev-only-secret-key-change-me"` | В проде задавать только через env (`DJANGO_SECRET_KEY`) и длинный случайный ключ. |
| `config/settings/production.py` | 11-13 | `SECRET_KEY` из env, иначе ошибка | Оставить как есть, но обязательно заполнить `DJANGO_SECRET_KEY` в `.env`. |
| `config/settings/base.py` | 106 | `STATIC_URL = "static/"` | Поменять на `STATIC_URL = "/static/"`, чтобы URL статики был корректным в любых роутингах (в т.ч. `/admin/`). |
| `config/settings/base.py` | 108 | `STATIC_ROOT = BASE_DIR / "staticfiles"` | Оставить. После каждого деплоя выполнять `collectstatic`. |
| `config/settings/base.py` | 111 | `MEDIA_URL = "media/"` | Рекомендуется `MEDIA_URL = "/media/"` для единообразия и корректных абсолютных URL. |
| `config/settings/base.py` | 112 | `MEDIA_ROOT = BASE_DIR / "media"` | Оставить. В nginx добавить `location /media/`. |
| `config/settings/base.py` | 124 | `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` | Для прода поменять в `.env` на SMTP backend и заполнить `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`. |
| `config/settings/production.py` | 21 | `EMAIL_BACKEND` из env (по умолчанию SMTP) | В `.env` явно задать SMTP-параметры. |
| `config/settings/production.py` | 15-18 | LLM параметры из env | В `.env` проверить `LLM_BASE_URL`, `LLM_API_KEY`, `AI_MODEL_NAME`, `LLM_TIMEOUT_SECONDS`. |
| `config/settings/production.py` | (добавить) | `SECURE_SSL_REDIRECT` отсутствует | Добавить `SECURE_SSL_REDIRECT = True` (если используешь HTTPS). |
| `config/settings/production.py` | (добавить) | `SESSION_COOKIE_SECURE` отсутствует | Добавить `SESSION_COOKIE_SECURE = True`. |
| `config/settings/production.py` | (добавить) | `CSRF_COOKIE_SECURE` отсутствует | Добавить `CSRF_COOKIE_SECURE = True`. |
| `config/settings/production.py` | (добавить) | `CSRF_TRUSTED_ORIGINS` отсутствует | Добавить список доверенных HTTPS-origin, например `https://app.example.com`. |
| `config/settings/production.py` | (добавить) | `SECURE_PROXY_SSL_HEADER` отсутствует | Добавить `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` при работе за nginx reverse proxy. |
| `config/settings/production.py` | (добавить) | HSTS отсутствует | Добавить `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` (только после стабильного HTTPS). |
| `.env` | (файл) | может быть пустой/тестовый | Заполнить прод-значениями: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, LLM, SMTP. |
| `nginx site config` | (файл сервера) | может не быть `location /static/` | Добавить `location /static/ { alias /opt/ai_feedback_django_2/staticfiles/; }` и `location /media/ { alias /opt/ai_feedback_django_2/media/; }`. |
| `systemd service` | (файл сервера) | может не быть `EnvironmentFile` | Добавить `EnvironmentFile=/opt/ai_feedback_django_2/.env`, чтобы prod-настройки подтягивались автоматически. |

---

## Минимальный набор команд после изменений

```bash
cd /opt/ai_feedback_django_2
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
systemctl restart ai_feedback_django_2
systemctl restart nginx
```

---

## Важно про DEBUG

- В проде должно быть только `DEBUG=False`.
- `DEBUG=True` в интернете = риск утечки служебной информации и настроек.
