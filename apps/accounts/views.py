"""Views приложения accounts для регистрации, входа, выхода и профиля."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from apps.accounts.forms import EmailAuthenticationForm, NicknameUpdateForm, PersonalTimerForm, RegistrationForm, SafePasswordResetForm
from apps.accounts.services.auth import is_login_throttled, register_failed_login_attempt, reset_login_attempts
from apps.accounts.services.cabinet import build_cabinet_dashboard


class RegisterView(View):
    """Отображает и обрабатывает регистрацию нового пользователя.

    Контекст использования:
    - публичная точка входа в создание учётной записи V1.

    Параметры:
    - использует `GET` для показа формы и `POST` для создания пользователя.

    Возвращает:
    - HTML-страницу регистрации или redirect на страницу входа.

    Исключения и особые случаи:
    - при невалидной форме возвращает страницу с ошибками.

    Побочные эффекты:
    - при успешной регистрации создаёт нового пользователя в БД.
    """

    template_name = "auth/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Возвращает экран регистрации с пустой формой.

        Контекст использования:
        - вызывается при первичном открытии страницы регистрации.

        Параметры:
        - `request`: входящий HTTP-запрос.

        Возвращает:
        - HTML-ответ с формой `RegistrationForm`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        form = RegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Проверяет форму регистрации и создаёт пользователя при успехе.

        Контекст использования:
        - обрабатывает отправку формы регистрации пользователем.

        Параметры:
        - `request`: HTTP-запрос с POST-данными формы.

        Возвращает:
        - redirect на страницу входа при успехе;
        - HTML-страницу с ошибками при невалидных данных.

        Исключения и особые случаи:
        - ошибки валидации обрабатываются на уровне формы без выброса исключения наружу.

        Побочные эффекты:
        - создаёт новую запись пользователя в БД при валидной форме.
        """

        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация успешна. Войдите в систему.")
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": form})


class LoginView(View):
    """Выполняет вход по email и паролю с базовым throttling.

    Контекст использования:
    - публичная страница входа в систему;
    - обеспечивает ограничение частоты неудачных попыток.

    Параметры:
    - `GET` возвращает форму;
    - `POST` обрабатывает аутентификацию.

    Возвращает:
    - HTML-форму входа или redirect на главную страницу после успеха.

    Исключения и особые случаи:
    - при превышении лимита попыток показывает предупреждение и блокирует вход.

    Побочные эффекты:
    - создаёт пользовательскую сессию;
    - обновляет счётчики throttling в кэше.
    """

    template_name = "auth/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Показывает форму авторизации по email и паролю.

        Контекст использования:
        - используется при открытии страницы входа без отправки формы.

        Параметры:
        - `request`: входящий HTTP-запрос.

        Возвращает:
        - HTML-ответ с пустой формой `EmailAuthenticationForm`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        form = EmailAuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Проверяет throttling и выполняет логин при корректных данных.

        Контекст использования:
        - обрабатывает POST-запрос страницы входа.

        Параметры:
        - `request`: HTTP-запрос с email и паролем.

        Возвращает:
        - redirect на `home` при успешном входе;
        - HTML-форму с ошибками/сообщением при неуспехе.

        Исключения и особые случаи:
        - при превышении лимита попыток логин блокируется временно;
        - при невалидной форме увеличивается счётчик неудачных попыток.

        Побочные эффекты:
        - создаёт сессию авторизации;
        - изменяет счётчик throttling в кэше.
        """

        email = (request.POST.get("email") or "").strip().lower()
        if is_login_throttled(email):
            messages.error(request, "Слишком много попыток входа. Попробуйте позже.")
            return render(request, self.template_name, {"form": EmailAuthenticationForm(request.POST)})

        form = EmailAuthenticationForm(request.POST)
        if not form.is_valid():
            register_failed_login_attempt(email)
            messages.error(request, "Не удалось войти. Проверьте email и пароль.")
            return render(request, self.template_name, {"form": form})

        user = form.cleaned_data["user"]
        login(request, user)
        reset_login_attempts(email)
        return redirect("home")


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """Завершает авторизованную сессию пользователя.

    Контекст использования:
    - вызывается по нажатию глобальной кнопки «Выйти».

    Параметры:
    - `request`: текущий HTTP-запрос авторизованного пользователя.

    Возвращает:
    - redirect на страницу входа.

    Исключения и особые случаи:
    - для неавторизованных пользователей маршрут закрыт декоратором `login_required`.

    Побочные эффекты:
    - удаляет данные пользовательской сессии.
    """

    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Показывает минимальный профиль и позволяет изменить никнейм.

    Контекст использования:
    - технический экран V1 для выполнения FR-PROFILE без полноценного личного кабинета.

    Параметры:
    - `request`: HTTP-запрос авторизованного пользователя;
    - `GET`: отображает форму никнейма;
    - `POST`: обновляет никнейм пользователя.

    Возвращает:
    - HTML-страницу профиля с формой.

    Исключения и особые случаи:
    - при невалидной форме остаётся на странице с ошибками.

    Побочные эффекты:
    - при успешном сохранении меняет `nickname` текущего пользователя.
    """

    if request.method == "POST":
        form = NicknameUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Никнейм обновлён.")
            return redirect("accounts:profile")
    else:
        form = NicknameUpdateForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


class SafePasswordResetView(PasswordResetView):
    """Экран запроса восстановления пароля с нейтральным сообщением о результате."""

    form_class = SafePasswordResetForm
    template_name = "auth/password_reset_form.html"
    email_template_name = "auth/password_reset_email.txt"
    subject_template_name = "auth/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class SafePasswordResetDoneView(PasswordResetDoneView):
    """Экран подтверждения отправки инструкций по восстановлению пароля."""

    template_name = "auth/password_reset_done.html"


class SafePasswordResetConfirmView(PasswordResetConfirmView):
    """Экран ввода нового пароля по валидной reset-ссылке."""

    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class SafePasswordResetCompleteView(PasswordResetCompleteView):
    """Экран успешного завершения восстановления пароля."""

    template_name = "auth/password_reset_complete.html"


@login_required
def cabinet_view(request: HttpRequest) -> HttpResponse:
    """Отображает личный кабинет пользователя с профилем, метриками, историей и настройками.

    Контекст использования:
    - основной экран `/cabinet/` для авторизованного пользователя;
    - объединяет профиль, персональный таймер, индикаторы и историю игр.

    Параметры:
    - `request`: HTTP-запрос пользователя;
    - `POST` поддерживает действия `update_nickname` и `update_timer`.

    Возвращает:
    - HTML-страницу `pages/cabinet_entry.html`.

    Исключения и особые случаи:
    - обрабатывает только текущего пользователя и не предоставляет доступ к чужим данным.

    Побочные эффекты:
    - может обновить nickname и/или персональный таймер в профиле пользователя.
    """

    action = request.POST.get("action") if request.method == "POST" else ""

    if request.method == "POST" and action == "update_nickname":
        nickname_form = NicknameUpdateForm(request.POST, instance=request.user)
        timer_form = PersonalTimerForm(instance=request.user)
        if nickname_form.is_valid():
            nickname_form.save()
            messages.success(request, "Никнейм обновлён.")
            return redirect("cabinet_entry")
    elif request.method == "POST" and action == "update_timer":
        timer_form = PersonalTimerForm(request.POST, instance=request.user)
        nickname_form = NicknameUpdateForm(instance=request.user)
        if timer_form.is_valid():
            timer_form.save()
            messages.success(request, "Персональный таймер сохранён.")
            return redirect("cabinet_entry")
    else:
        nickname_form = NicknameUpdateForm(instance=request.user)
        timer_form = PersonalTimerForm(instance=request.user)

    dashboard = build_cabinet_dashboard(request.user)

    from django.core.paginator import Paginator

    history_paginator = Paginator(dashboard["history_scores"], 10)
    history_page = history_paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "pages/cabinet_entry.html",
        {
            "nickname_form": nickname_form,
            "timer_form": timer_form,
            "history_page": history_page,
            **dashboard,
        },
    )
