# Generated manually for iteration 3 auth schema.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models

import apps.accounts.models


class Migration(migrations.Migration):
    """Создаёт кастомную модель пользователя с ролями и профилем."""

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный ID")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="Email")),
                ("nickname", models.CharField(max_length=64, verbose_name="Никнейм")),
                (
                    "role",
                    models.CharField(
                        choices=[("user", "Пользователь"), ("admin", "Администратор"), ("superadmin", "Супер-администратор")],
                        default="user",
                        max_length=16,
                        verbose_name="Роль",
                    ),
                ),
                ("is_primary_superadmin", models.BooleanField(default=False, verbose_name="Главный супер-администратор")),
                ("avatar_letter", models.CharField(default="U", max_length=1, verbose_name="Буква аватара")),
                ("avatar_bg_hex", models.CharField(default="#E7F0FF", max_length=7, verbose_name="Цвет аватара")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("is_staff", models.BooleanField(default=False, verbose_name="Доступ в админку")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата регистрации")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_users",
                        to="accounts.user",
                        verbose_name="Кем создан",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
                "indexes": [models.Index(fields=["role", "is_active"], name="idx_user_role_active")],
            },
            managers=[("objects", apps.accounts.models.UserManager())],
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary_superadmin", True)),
                fields=("is_primary_superadmin",),
                name="uniq_single_primary_superadmin",
            ),
        ),
    ]
