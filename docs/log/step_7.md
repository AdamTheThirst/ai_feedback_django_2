# step_7

## Операции, выполненные на шаге
1. Добавлена модель `AnalysisResult` и миграция `0002_analysisresult`.
2. Добавлена модель `AuditLogEntry` и миграция `auditlog/0001_initial`.
3. Реализован сервис `run_analysis_for_dialog` с транскриптом и запуском по каждому `AnalysisPrompt`.
4. Реализована JSON-валидация и fallback-обработка невалидных ответов.
5. Встроен запуск аналитики в `finish_dialog` после завершения сессии.
6. Добавлены тесты `apps/analysis/tests/test_engine.py`.

## Какие функции/сущности появились и зачем
- `AnalysisResult` — хранение результата каждого критерия с snapshot-полями.
- `AuditLogEntry` — технический журнал событий/ошибок анализа.
- `parse_analysis_response` — строгая проверка структуры JSON (`rating`, `text`).
- `run_analysis_for_dialog` — оркестрация полного аналитического цикла.

## Связность между элементами
- `finish_dialog` завершает сессию и запускает `run_analysis_for_dialog`.
- `run_analysis_for_dialog` собирает транскрипт из `DialogMessage`.
- Для каждого `AnalysisPrompt` сохраняется `AnalysisResult`.
- Ошибки и невалидные JSON фиксируются в `AuditLogEntry`.

## Краткий консольный отчёт
Итерация 8 выполнена: аналитический движок, JSON-валидация, сохранение `AnalysisRun/AnalysisResult` и audit log реализованы.
