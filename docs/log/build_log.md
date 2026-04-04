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

## Шаг 2 — Accounts, роли и auth flow

Дата: 2026-04-04

### Что сделано
- Реализована кастомная модель `accounts.User` с логином по email, ролями (`user/admin/superadmin`), признаком главного супер-админа и служебными полями профиля.
- Добавлен менеджер `UserManager` и функции генерации никнейма/цвета аватара.
- Реализованы формы:
  - регистрация,
  - вход по email,
  - обновление никнейма,
  - безопасный reset password.
- Реализованы views и маршруты auth-flow:
  - `register`, `login`, `logout`, `profile`,
  - `password_reset` + `done/confirm/complete`.
- Добавлен базовый throttling попыток логина через cache-сервис.
- Добавлен сервис ролевых permission-проверок (`is_admin`, `is_superadmin`, `is_primary_superadmin`, `can_create_admin`, `can_assign_superadmin`).
- Обновлены настройки проекта для кастомного пользователя (`AUTH_USER_MODEL`) и auth-redirects.
- Добавлена первая миграция `apps/accounts/migrations/0001_initial.py`.
- Добавлены smoke-тесты permission-сервиса ролей.

### Как это связано между собой
- `accounts.User` является источником истины для аутентификации и ролевого доступа.
- `LoginView` использует `EmailAuthenticationForm` и throttling-сервис из `accounts/services/auth.py`.
- Правила ролей из `accounts/services/permissions.py` готовы для интеграции в админские/контентные сервисы.
- `profile_view` даёт минимальный путь изменения никнейма без полноценного ЛК.

### Что не сделано в этом шаге
- Полноценный backoffice для управления ролями.
- Логирование событий превышения login-rate-limit в отдельную таблицу audit log.
- Seed-учётки и команды инициализации.

## Шаг 3 — Content domain

Дата: 2026-04-04

### Что сделано
- Реализованы модели контент-домена:
  - `Game`,
  - `Scenario`,
  - `ScenarioMediaAsset`,
  - `ScenarioPrompt`,
  - `AnalysisPrompt`,
  - `SystemPrompt`.
- Добавлены правила владения через абстракцию `OwnedModel` в `core`.
- Для контентных сущностей применены правила архивирования (`is_archived`, `archived_at`) и метки времени.
- Введены ограничения целостности:
  - уникальность slug/порядков,
  - один активный `ScenarioPrompt` на сценарий,
  - уникальность `AnalysisPrompt.alias` в рамках игры,
  - валидация диапазона `min_rating/max_rating`.
- Добавлена миграция `apps/content/migrations/0001_initial.py`.
- Добавлена management-команда `seed_demo_content` для заполнения demo-контента V1.
- Добавлены тесты ограничений контент-моделей.

### Как это связано между собой
- `Game` является корневой сущностью контента.
- `Scenario` принадлежит `Game`, может ссылаться на `ScenarioMediaAsset`.
- `ScenarioPrompt` принадлежит `Scenario` и хранит активную игровую версию промта.
- `AnalysisPrompt` принадлежит `Game` и задаёт критерии анализа для всех сценариев этой игры.
- `SystemPrompt` хранит глобальный служебный промт (`analysis_metadata_generator`).
- Команда `seed_demo_content` формирует 1 игру и 3 сценария demo-набора, включая промты и системный промт.

### Что не сделано в этом шаге
- Полная интеграция новых моделей content в runtime-диалог (`DialogSession` пока не ссылается на `game/scenario/scenario_prompt_used`).
- Backoffice-интерфейс продукта (реализовано только через Django Admin).
- Заполнение и валидация реальных медиа-файлов в dev seed-потоке.
