"""Модели приложения accounts: пользователь, роли и служебные атрибуты профиля."""

from __future__ import annotations

import hashlib
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel


class UserRole(models.TextChoices):
    """Перечисляет поддерживаемые роли пользователя в системе.

    Контекст использования:
    - применяется в поле `User.role` для серверного контроля доступа;
    - используется в permission/service-слое для разграничения прав.

    Параметры:
    - значения перечисления задаются централизованно и не передаются извне.

    Возвращает:
    - строковые коды ролей: `user`, `admin`, `superadmin`.

    Исключения и особые случаи:
    - невалидные роли блокируются ограничением `choices`.

    Побочные эффекты:
    - отсутствуют.
    """

    USER = "user", "Пользователь"
    ADMIN = "admin", "Администратор"
    SUPERADMIN = "superadmin", "Супер-администратор"


class UserManager(BaseUserManager):
    """Менеджер кастомной модели пользователя с логином по email.

    Контекст использования:
    - используется Django ORM для создания обычных пользователей и суперпользователей;
    - централизует нормализацию email и установку обязательных служебных флагов.

    Параметры:
    - методы принимают `email`, `password` и дополнительные поля пользователя.

    Возвращает:
    - экземпляр модели `User` после сохранения в БД.

    Исключения и особые случаи:
    - выбрасывает `ValueError`, если email не передан;
    - выбрасывает `ValidationError`, если нарушены ограничения ролей.

    Побочные эффекты:
    - сохраняет пользователя в базе данных;
    - устанавливает хэш пароля через штатный механизм Django.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: object) -> "User":
        """Создаёт и сохраняет пользователя с заданным email.

        Контекст использования:
        - внутренний вспомогательный метод для `create_user` и `create_superuser`.

        Параметры:
        - `email`: email пользователя, используемый как логин;
        - `password`: пароль в открытом виде до хэширования;
        - `extra_fields`: дополнительные поля модели пользователя.

        Возвращает:
        - созданный и сохранённый экземпляр `User`.

        Исключения и особые случаи:
        - `ValueError`, если email отсутствует.

        Побочные эффекты:
        - изменяет БД и записывает хэш пароля.
        """

        if not email:
            raise ValueError("Email обязателен для создания пользователя.")
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "User":
        """Создаёт обычного пользователя с ролью `user`.

        Контекст использования:
        - вызывается формой регистрации и сидерами dev-данных.

        Параметры:
        - `email`: email для входа;
        - `password`: пароль пользователя;
        - `extra_fields`: дополнительные поля, включая `nickname`.

        Возвращает:
        - сохранённый пользователь с ролью `user`.

        Исключения и особые случаи:
        - если не передан `nickname`, метод задаёт значение по умолчанию из локальной части email.

        Побочные эффекты:
        - создаёт запись пользователя в БД.
        """

        extra_fields.setdefault("role", UserRole.USER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_primary_superadmin", False)
        extra_fields.setdefault("nickname", normalized_nickname_from_email(email))
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields: object) -> "User":
        """Создаёт главного супер-администратора для Django Admin.

        Контекст использования:
        - применяется штатной командой `createsuperuser` и dev bootstrap-процедурами.

        Параметры:
        - `email`: email администратора;
        - `password`: пароль суперпользователя;
        - `extra_fields`: дополнительные поля, включая `nickname`.

        Возвращает:
        - сохранённый пользователь роли `superadmin` с правами superuser.

        Исключения и особые случаи:
        - `ValueError`, если критичные флаги прав не выставлены.

        Побочные эффекты:
        - создаёт запись суперпользователя в БД.
        """

        extra_fields.setdefault("role", UserRole.SUPERADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_primary_superadmin", True)
        extra_fields.setdefault("nickname", normalized_nickname_from_email(email))

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь обязан иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь обязан иметь is_superuser=True.")
        if extra_fields.get("role") != UserRole.SUPERADMIN:
            raise ValueError("Суперпользователь обязан иметь роль superadmin.")

        return self._create_user(email, password, **extra_fields)


def normalized_nickname_from_email(email: str) -> str:
    """Возвращает безопасный никнейм по умолчанию на основе email.

    Контекст использования:
    - используется при создании пользователя, если никнейм не передан явно.

    Параметры:
    - `email`: исходный email пользователя.

    Возвращает:
    - локальную часть email либо резервное значение `user`.

    Исключения и особые случаи:
    - если локальная часть пустая, возвращается значение `user`.

    Побочные эффекты:
    - отсутствуют.
    """

    local_part = (email or "").split("@", maxsplit=1)[0].strip()
    return local_part or "user"


def build_avatar_color(email: str) -> str:
    """Генерирует детерминированный светлый цвет аватара по email.

    Контекст использования:
    - используется для поля `avatar_bg_hex` пользовательского профиля;
    - поддерживает стабильный визуальный фон буквы-аватара в UI.

    Параметры:
    - `email`: email пользователя как стабильный вход для хэширования.

    Возвращает:
    - HEX-цвет из ограниченной палитры светлых оттенков.

    Исключения и особые случаи:
    - если email пустой, берётся детерминированный fallback на основе пустой строки.

    Побочные эффекты:
    - отсутствуют.
    """

    palette = [
        "#FFE8D6",
        "#E7F0FF",
        "#E9F7EF",
        "#FFF4CC",
        "#F3E8FF",
        "#DFF5F2",
        "#FDE2E4",
        "#E8F1D4",
    ]
    hash_int = int(hashlib.sha256((email or "").encode("utf-8")).hexdigest(), 16)
    return palette[hash_int % len(palette)]


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """Кастомная модель пользователя с логином по email и ролевым доступом.

    Контекст использования:
    - является основной учётной записью платформы;
    - используется для аутентификации, авторизации и аудита административных действий.

    Параметры:
    - хранит email, nickname, роль, флаги доступа и служебные поля профиля.

    Возвращает:
    - экземпляр пользователя, совместимый с auth-системой Django.

    Исключения и особые случаи:
    - обеспечивает валидацию сочетаний `role` и `is_primary_superadmin`;
    - для административных ролей требует `is_staff=True`.

    Побочные эффекты:
    - участвует во всех внешних ключах системы как владелец действий и контента.
    """

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="Публичный ID")
    email = models.EmailField(unique=True, verbose_name="Email")
    nickname = models.CharField(max_length=64, verbose_name="Никнейм")
    role = models.CharField(max_length=16, choices=UserRole.choices, default=UserRole.USER, verbose_name="Роль")
    is_primary_superadmin = models.BooleanField(default=False, verbose_name="Главный супер-администратор")
    avatar_letter = models.CharField(max_length=1, default="U", verbose_name="Буква аватара")
    avatar_bg_hex = models.CharField(max_length=7, default="#E7F0FF", verbose_name="Цвет аватара")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Доступ в админку")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")
    preferred_dialog_duration_minutes = models.PositiveSmallIntegerField(default=10, verbose_name="Персональный таймер, мин")
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
        verbose_name="Кем создан",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = ["nickname"]

    class Meta:
        """Мета-настройки таблицы пользователей."""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.UniqueConstraint(
                fields=["is_primary_superadmin"],
                condition=models.Q(is_primary_superadmin=True),
                name="uniq_single_primary_superadmin",
            )
        ]
        indexes = [
            models.Index(fields=["role", "is_active"], name="idx_user_role_active"),
        ]

    def clean(self) -> None:
        """Проверяет согласованность ролей и служебных флагов.

        Контекст использования:
        - вызывается перед сохранением пользователя через формы и менеджер;
        - обеспечивает ключевые продуктовые ограничения ролей.

        Параметры:
        - метод не принимает аргументов.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - `ValidationError`, если главный супер-админ не имеет роли `superadmin`;
        - `ValidationError`, если административная роль не имеет `is_staff=True`.

        Побочные эффекты:
        - отсутствуют.
        """

        super().clean()
        if self.is_primary_superadmin and self.role != UserRole.SUPERADMIN:
            raise ValidationError("Главный супер-администратор обязан иметь роль superadmin.")
        if self.role in {UserRole.ADMIN, UserRole.SUPERADMIN} and not self.is_staff:
            raise ValidationError("Административные роли обязаны иметь is_staff=True.")
        if not 5 <= int(self.preferred_dialog_duration_minutes or 0) <= 20:
            raise ValidationError("Персональный таймер должен быть в диапазоне от 5 до 20 минут.")

    def save(self, *args: object, **kwargs: object) -> None:
        """Сохраняет пользователя и обновляет вычисляемые поля аватара.

        Контекст использования:
        - централизует обновление `avatar_letter` и `avatar_bg_hex` на основе текущих данных.

        Параметры:
        - `*args`, `**kwargs`: стандартные аргументы `Model.save`.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - возможны исключения валидации, если поля пользователя противоречат ограничениям.

        Побочные эффекты:
        - записывает данные в БД;
        - модифицирует поля аватара перед сохранением.
        """

        normalized_nickname = (self.nickname or "").strip()
        self.nickname = normalized_nickname or normalized_nickname_from_email(self.email)
        self.avatar_letter = (self.nickname[0] if self.nickname else "U").upper()
        self.avatar_bg_hex = build_avatar_color(self.email)
        if self.role in {UserRole.ADMIN, UserRole.SUPERADMIN}:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает строковое представление пользователя.

        Контекст использования:
        - используется в админке, логах и отладочных сообщениях.

        Параметры:
        - не принимает аргументов.

        Возвращает:
        - строку вида `<email> (<role>)`.

        Исключения и особые случаи:
        - не ожидаются.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.email} ({self.role})"
