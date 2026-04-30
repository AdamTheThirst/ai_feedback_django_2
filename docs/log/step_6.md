# step_6

## Операции, выполненные на шаге
1. Добавлено поле `effective_duration_seconds` в `DialogSession` и миграция `0003_dialogsession_effective_duration_seconds`.
2. Реализован lifecycle-сервис завершения диалога (`finish_dialog`, `maybe_finish_dialog_by_timeout`).
3. Добавлены JSON-endpoint-ы завершения: `dialogs:finish` и `dialogs:page_leave`.
4. Обновлён `chat.js`: обратный отсчёт, ручное завершение, автозавершение по таймеру.
5. Реализован `sendBeacon` + keepalive fallback при покидании страницы.
6. Добавлены тесты `apps/dialogs/tests/test_finish_api.py`.

## Какие функции/сущности появились и зачем
- `DialogFinishApiView` — серверная точка завершения вручную и по таймеру.
- `DialogPageLeaveApiView` — endpoint для завершения при закрытии вкладки.
- `finish_dialog` — единый идемпотентный сервис финализации статуса.
- `get_dialog_seconds_remaining` — серверный расчёт оставшегося времени.

## Связность между элементами
- `ScenarioStartView` фиксирует длительность таймера в `DialogSession`.
- `DialogChatView` отдаёт `seconds_remaining` клиенту.
- `chat.js` обновляет таймер и вызывает `dialogs:finish`/`dialogs:page_leave`.
- `has_active_dialog` запускает серверный fallback-добиватель зависших сессий.

## Краткий консольный отчёт
Итерация 7 выполнена: серверный/клиентский таймер, ручное и таймаут-завершение, `sendBeacon` + fallback добивание реализованы.
