"""Административная регистрация модели пользователя."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Настраивает отображение кастомного пользователя в Django Admin.

    Контекст использования:
    - используется администраторами для просмотра и редактирования учётных записей.

    Параметры:
    - конфигурация задаётся атрибутами класса `ModelAdmin`.

    Возвращает:
    - стандартный интерфейс управления моделью `User` в Django Admin.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - позволяет редактировать роли и служебные флаги пользователя через админку.
    """

    ordering = ("email",)
    list_display = ("email", "nickname", "role", "is_primary_superadmin", "is_staff", "is_active")
    search_fields = ("email", "nickname")
    readonly_fields = ("public_id", "created_at", "updated_at", "date_joined", "last_login", "avatar_letter", "avatar_bg_hex")
    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        (
            "Профиль и роли",
            {
                "fields": (
                    "public_id",
                    "nickname",
                    "role",
                    "is_primary_superadmin",
                    "created_by",
                    "avatar_letter",
                    "avatar_bg_hex",
                )
            },
        ),
        (
            "Права",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Временные поля",
            {"fields": ("date_joined", "last_login", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nickname", "password1", "password2", "role", "is_staff", "is_active"),
            },
        ),
    )
