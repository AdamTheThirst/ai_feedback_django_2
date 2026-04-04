# build_log

## Шаг 0 — Инициализация bootstrap-слоя проекта

Дата: 2026-04-04

### Что сделано
- Создан Django-каркас проекта с конфигурацией `config/` и окружениями `base/local/production`.
- Добавлены базовые приложения согласно архитектурной декомпозиции (`core`, `accounts`, `content`, `dialogs`, `analysis`, `platform_config`, `adminpanel`, `exports`, `auditlog`, `integrations`).
- Настроены базовые пути шаблонов, статики и медиа.
- Подключены Bootstrap 5 (CDN) и локальные `static/css/app.css`, `static/js/app.js`.
- Добавлен базовый шаблон `templates/layouts/base.html` и техническая страница `templates/pages/home.html`.
- Подготовлены `.env`-переменные для AI и email через `.env.example`.
- Добавлены `requirements.txt` и `.gitignore` для базовой разработки.

### Как это связано между собой
- `manage.py` запускает Django с настройками `config.settings.local`.
- `config/settings/base.py` задаёт общий каркас (apps, middleware, templates, db, static/media).
- `config/settings/local.py` и `config/settings/production.py` уточняют окружение через переменные среды.
- `config/urls.py` подключает `/admin/` и временную домашнюю страницу для smoke-проверки каркаса.
- Базовый шаблон и статические ресурсы создают фундамент UI для следующих итераций.

### Что не сделано в этом шаге
- Бизнес-логика доменных модулей и модели данных.
- Миграции, роли и права, чатовый runtime, аналитика и PDF.
- Реализация личного кабинета/энциклопедии и персонального таймера.
