# step_3

## Операции, выполненные на шаге
1. Добавлен `OwnedModel` в `apps/core/models.py`.
2. Реализованы модели content-домена и регистрация в Django Admin.
3. Добавлена миграция `apps/content/migrations/0001_initial.py`.
4. Реализована management-команда `seed_demo_content`.
5. Добавлены тесты ограничений `apps/content/tests/test_content_models.py`.

## Какие функции/сущности появились и зачем
- `Game/Scenario` — иерархия пользовательского контента игр.
- `ScenarioPrompt` — версия игрового промта сценария.
- `AnalysisPrompt` — критерии анализа на уровне игры.
- `SystemPrompt` — служебный глобальный промт.
- `ScenarioMediaAsset` — переиспользуемый и архивируемый медиа-ресурс.
- `seed_demo_content` — прозрачное seed-наполнение demo-контента V1.

## Связность между элементами
- `Scenario` связан с `Game` и опционально с `ScenarioMediaAsset`.
- `ScenarioPrompt` связан с `Scenario`, `AnalysisPrompt` — с `Game`.
- Все мастер-данные имеют `created_by` через `OwnedModel` и флаги архивирования.

## Краткий консольный отчёт
Итерация 4 выполнена: реализован content domain, миграция и seed-наполнение демо-контента.
