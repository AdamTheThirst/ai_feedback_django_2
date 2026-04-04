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

## Шаг 1 — База данных и core-модели

Дата: 2026-04-04

### Что сделано
- Добавлены базовые абстракции моделей в `apps/core/models.py`:
  - `TimestampedModel` (created_at/updated_at),
  - `ArchivableModel` (is_archived/archived_at),
  - `PublicIdModel` (public_id UUID).
- Добавлены ключевые enum-статусы в `apps/core/enums.py`:
  - `DialogStatus`,
  - `DialogEndedReason`,
  - `AnalysisRunStatus`.
- Введены базовые таблицы жизненного цикла:
  - `dialogs.DialogSession`,
  - `analysis.AnalysisRun`.
- Добавлены первые миграции:
  - `apps/dialogs/migrations/0001_initial.py`,
  - `apps/analysis/migrations/0001_initial.py`.

### Как это связано между собой
- `DialogSession` использует enum-статусы и фиксирует базовый жизненный цикл пользовательского диалога.
- `AnalysisRun` связан с `DialogSession` через `OneToOne` и хранит технический статус выполнения аналитики.
- Абстракции `TimestampedModel` и `PublicIdModel` обеспечивают единый формат технических полей для доменных моделей.
- Ограничение `uniq_active_dialog_per_user` поддерживает инвариант «один активный диалог на пользователя» на уровне БД.

### Что не сделано в этом шаге
- Полный состав полей `DialogSession`/`AnalysisRun` из спецификации (часть полей будет добавлена в следующих итерациях вместе с моделями контента и настроек).
- Модели `DialogMessage` и `AnalysisResult`.
- Доменные модели контента, платформенных настроек и ролей.
