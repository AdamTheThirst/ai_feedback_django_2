# step_4

## Операции, выполненные на шаге
1. Реализован `HomeView` со списком игр и сценариев.
2. Реализован `ScenarioStartView` и серверная проверка активного диалога.
3. Добавлены маршруты `scenario_start`, `encyclopedia_entry`, `cabinet_entry`, `dialogs/*`.
4. Добавлены шаблоны: `home`, `encyclopedia_entry`, `cabinet_entry`, `dialogs/placeholder`.
5. Добавлен сервис `apps/dialogs/services/session.py`.
6. Добавлены тесты `apps/core/tests/test_home_flow.py`.

## Какие функции/сущности появились и зачем
- `has_active_dialog` — централизованная проверка инварианта единственного активного диалога.
- `ScenarioStartView` — безопасный запуск сценария с серверной валидацией.
- `DialogPlaceholderView` — временный экран для проверки сквозной маршрутизации до реализации чата.

## Связность между элементами
- `HomeView` -> `scenario_start` (POST) -> `DialogSession` -> `dialogs:placeholder`.
- Нижние кнопки home ведут на `encyclopedia_entry` и `cabinet_entry`.
- Проверка активного диалога используется и в UI, и в серверной логике запуска.

## Краткий консольный отчёт
Итерация 5 выполнена: главная страница и маршрутизация пользовательского входа реализованы, включая блокировку повторного запуска сценария.
