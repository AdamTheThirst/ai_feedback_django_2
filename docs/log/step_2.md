# step_2

## Операции, выполненные на шаге
1. Добавлена кастомная модель пользователя `accounts.User` и миграция `0001_initial`.
2. Добавлены сервисы авторизации (throttling) и проверок прав по ролям.
3. Реализованы формы и views для регистрации, входа, выхода, reset password и минимального профиля.
4. Добавлены маршруты `accounts/` и обновлён корневой роутинг.
5. Настроены `AUTH_USER_MODEL`, auth-redirects и cache backend.
6. Добавлены шаблоны auth-страниц и тесты permission-правил.

## Какие функции/сущности появились и зачем
- `User` + `UserManager` — ядро учётных записей и ролей.
- `EmailAuthenticationForm`/`RegistrationForm` — безопасный пользовательский auth-ввод.
- `LoginView`/`RegisterView`/`logout_view` — базовый auth flow V1.
- `SafePasswordReset*` — восстановление пароля через email по стандартному Django-flow.
- `permissions.py` — централизованные правила разграничения роли/доступа.

## Связность между элементами
- формы `accounts/forms.py` обслуживаются view-слоем `accounts/views.py`.
- throttling логина отделён в `accounts/services/auth.py`.
- ролевые проверки отделены в `accounts/services/permissions.py`.
- все маршруты объединены под префиксом `/accounts/`.

## Краткий консольный отчёт
Итерация 3 выполнена: добавлены User/роли, auth flow и сервисные проверки прав доступа.
