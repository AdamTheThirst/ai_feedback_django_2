"""Формы аутентификации и регистрации пользователей."""

from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError

from apps.accounts.models import User


class RegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя по никнейму, email и паролю.

    Контекст использования:
    - применяется на публичной странице регистрации;
    - создаёт обычного пользователя роли `user`.

    Параметры:
    - принимает поля `nickname`, `email`, `password1`, `password2`.

    Возвращает:
    - валидированные данные и созданного пользователя через `save`.

    Исключения и особые случаи:
    - выдаёт ошибки, если email уже занят или пароли не совпадают.

    Побочные эффекты:
    - при успешном `save` создаёт запись пользователя в БД.
    """

    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    class Meta:
        """Привязывает форму к модели пользователя."""

        model = User
        fields = ["nickname", "email"]

    def clean_email(self) -> str:
        """Проверяет уникальность email перед созданием учётной записи.

        Контекст использования:
        - вызывается в процессе валидации формы регистрации.

        Параметры:
        - не принимает аргументов, использует значение поля `email`.

        Возвращает:
        - нормализованный email.

        Исключения и особые случаи:
        - `ValidationError`, если email уже используется.

        Побочные эффекты:
        - отсутствуют.
        """

        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean(self) -> dict[str, object]:
        """Проверяет совпадение пароля и подтверждения.

        Контекст использования:
        - выполняется после валидации отдельных полей формы.

        Параметры:
        - отсутствуют.

        Возвращает:
        - словарь очищенных данных.

        Исключения и особые случаи:
        - добавляет ошибку к полю `password2`, если пароли различаются.

        Побочные эффекты:
        - отсутствуют.
        """

        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """Создаёт пользователя и задаёт хэш пароля.

        Контекст использования:
        - вызывается view регистрации после успешной валидации.

        Параметры:
        - `commit`: флаг немедленного сохранения в БД.

        Возвращает:
        - объект созданного пользователя.

        Исключения и особые случаи:
        - при `commit=False` возвращает несохранённый объект.

        Побочные эффекты:
        - создаёт пользователя в БД при `commit=True`.
        """

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    """Форма входа в систему по email и паролю.

    Контекст использования:
    - используется на странице логина вместо username-формы Django.

    Параметры:
    - принимает `email` и `password`.

    Возвращает:
    - в `cleaned_data` возвращает проверенного пользователя в ключе `user`.

    Исключения и особые случаи:
    - `ValidationError`, если данные входа некорректны.

    Побочные эффекты:
    - отсутствуют.
    """

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self) -> dict[str, object]:
        """Аутентифицирует пользователя по введённым данным.

        Контекст использования:
        - выполняется в процессе отправки формы входа.

        Параметры:
        - отсутствуют.

        Возвращает:
        - словарь очищенных данных с ключом `user`.

        Исключения и особые случаи:
        - `ValidationError` при неверной паре email/пароль.

        Побочные эффекты:
        - отсутствуют.
        """

        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError("Неверный email или пароль.")
            if not user.is_active:
                raise ValidationError("Учётная запись деактивирована.")
            cleaned_data["user"] = user
        return cleaned_data


class NicknameUpdateForm(forms.ModelForm):
    """Форма минимального изменения никнейма авторизованного пользователя.

    Контекст использования:
    - применяется на странице профиля в рамках V1.

    Параметры:
    - принимает поле `nickname`.

    Возвращает:
    - обновлённого пользователя через `save`.

    Исключения и особые случаи:
    - не допускает пустой никнейм.

    Побочные эффекты:
    - при сохранении обновляет профиль пользователя.
    """

    class Meta:
        """Привязывает форму к полю никнейма модели пользователя."""

        model = User
        fields = ["nickname"]


class SafePasswordResetForm(PasswordResetForm):
    """Форма reset password с нейтральным пользовательским откликом.

    Контекст использования:
    - используется вместо стандартной формы для соблюдения требования
      не раскрывать существование email сверх необходимого.

    Параметры:
    - принимает email пользователя.

    Возвращает:
    - штатный результат отправки письма через backend Django.

    Исключения и особые случаи:
    - не сообщает пользователю, существует ли email в системе.

    Побочные эффекты:
    - может отправить письмо для существующей активной учётной записи.
    """

    def get_users(self, email: str):
        """Возвращает активных пользователей по email без изменения контракта безопасности.

        Контекст использования:
        - переопределяется для явного контроля источника пользователей reset-flow.

        Параметры:
        - `email`: адрес, введённый в форме восстановления.

        Возвращает:
        - генератор активных пользователей с совпадающим email.

        Исключения и особые случаи:
        - при отсутствии пользователей возвращает пустой генератор.

        Побочные эффекты:
        - отсутствуют.
        """

        return User._default_manager.filter(email__iexact=email, is_active=True)


class PersonalTimerForm(forms.ModelForm):
    """Форма настройки персональной длительности игровых сессий пользователя.

    Контекст использования:
    - используется в личном кабинете для изменения таймера будущих сессий.

    Параметры:
    - работает с полем `preferred_dialog_duration_minutes` модели `User`.

    Возвращает:
    - валидированное значение таймера в диапазоне 5..20 минут.

    Исключения и особые случаи:
    - не допускает значения вне диапазона и нечисловые данные.

    Побочные эффекты:
    - при `save` обновляет поле настройки пользователя.
    """

    class Meta:
        """Определяет связь формы с моделью пользователя."""

        model = User
        fields = ["preferred_dialog_duration_minutes"]

    def clean_preferred_dialog_duration_minutes(self) -> int:
        """Проверяет диапазон значения таймера 5..20 минут.

        Контекст использования:
        - серверная валидация перед сохранением персональной настройки.

        Параметры:
        - отсутствуют, значение берётся из очищенных данных формы.

        Возвращает:
        - целое число минут в диапазоне 5..20.

        Исключения и особые случаи:
        - `ValidationError`, если значение выходит за допустимые границы.

        Побочные эффекты:
        - отсутствуют.
        """

        minutes = int(self.cleaned_data["preferred_dialog_duration_minutes"])
        if minutes < 5 or minutes > 20:
            raise forms.ValidationError("Таймер должен быть в диапазоне от 5 до 20 минут.")
        return minutes
