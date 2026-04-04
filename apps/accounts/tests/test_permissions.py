"""Тесты сервисных правил ролевого доступа."""

from django.test import TestCase

from apps.accounts.models import User, UserRole
from apps.accounts.services.permissions import can_assign_superadmin, can_create_admin, is_admin, is_primary_superadmin, is_superadmin


class RolePermissionServiceTests(TestCase):
    """Проверяет базовые ограничения ролей в permission-сервисе.

    Контекст использования:
    - защищает от регрессий в правилах прав доступа для ролей V1.

    Параметры:
    - тестовый класс не принимает параметров.

    Возвращает:
    - результаты assert-проверок при выполнении тестов.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые записи пользователей во временной тестовой БД.
    """

    def setUp(self) -> None:
        """Подготавливает пользователей разных ролей для сценариев проверки.

        Контекст использования:
        - вызывается перед каждым тестовым методом этого класса.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - не ожидаются при корректной миграции тестовой БД.

        Побочные эффекты:
        - создаёт четыре записи пользователей в тестовой БД.
        """

        self.user = User.objects.create_user(email="user@example.com", password="pass12345", nickname="User")
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass12345",
            nickname="Admin",
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.superadmin = User.objects.create_user(
            email="super@example.com",
            password="pass12345",
            nickname="Super",
            role=UserRole.SUPERADMIN,
            is_staff=True,
        )
        self.primary_superadmin = User.objects.create_user(
            email="root@example.com",
            password="pass12345",
            nickname="Root",
            role=UserRole.SUPERADMIN,
            is_staff=True,
            is_primary_superadmin=True,
        )

    def test_admin_flags(self) -> None:
        """Проверяет классификацию обычной и административных ролей.

        Контекст использования:
        - подтверждает работу функции `is_admin`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.assertFalse(is_admin(self.user))
        self.assertTrue(is_admin(self.admin))
        self.assertTrue(is_admin(self.superadmin))

    def test_superadmin_flags(self) -> None:
        """Проверяет различие назначенного и главного супер-админа.

        Контекст использования:
        - валидирует функции `is_superadmin` и `is_primary_superadmin`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.assertTrue(is_superadmin(self.superadmin))
        self.assertFalse(is_primary_superadmin(self.superadmin))
        self.assertTrue(is_primary_superadmin(self.primary_superadmin))

    def test_root_only_actions(self) -> None:
        """Проверяет, что критичные ролевые операции доступны только root-superadmin.

        Контекст использования:
        - валидирует правила `can_create_admin` и `can_assign_superadmin`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.assertFalse(can_create_admin(self.superadmin))
        self.assertFalse(can_assign_superadmin(self.admin))
        self.assertTrue(can_create_admin(self.primary_superadmin))
        self.assertTrue(can_assign_superadmin(self.primary_superadmin))
