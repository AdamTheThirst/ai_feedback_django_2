# step_5

## Операции, выполненные на шаге
1. Расширен lifecycle `DialogSession` и добавлена модель `DialogMessage`.
2. Реализован старт диалога со стартовым сообщением ассистента.
3. Реализован JSON-endpoint отправки сообщений.
4. Добавлены защита от двойной отправки и pending-конкуренции.
5. Реализован чатовый UI с индикатором «думаю...» и отправкой без перезагрузки.
6. Добавлены миграция `0002_dialog_chat_runtime` и тесты `apps/dialogs/tests/test_send_message_api.py`.

## Какие функции/сущности появились и зачем
- `DialogMessage` — постоянная история реплик в чате.
- `send_user_message` — единая оркестрация бизнес-логики отправки сообщения.
- `DialogSendMessageApiView` — JSON-контракт для динамического чата.
- `generate_game_reply` — временный адаптер ответа персонажа до подключения LLM.

## Связность между элементами
- `ScenarioStartView` создаёт `DialogSession` + opening message.
- `DialogChatView` отображает историю `DialogMessage`.
- `chat.js` -> `dialogs:send_message` -> `send_user_message` -> сохранение user/assistant сообщений.

## Краткий консольный отчёт
Итерация 6 выполнена: lifecycle сессии и базовый динамический чат реализованы с серверной защитой от дублей/конкуренции.
