"""Сервисные функции проверки и запуска пользовательской диалоговой сессии."""

from django.contrib.auth import get_user_model

from apps.core.enums import DialogStatus
from apps.dialogs.models import DialogSession


def has_active_dialog(user: get_user_model()) -> bool:
    """Проверяет наличие активной диалоговой сессии у пользователя.

    Контекст использования:
    - применяется на главной странице перед запуском нового сценария;
    - поддерживает продуктовый инвариант «один активный диалог на пользователя».

    Параметры:
    - `user`: авторизованный пользователь, для которого выполняется проверка.

    Возвращает:
    - `True`, если хотя бы одна сессия со статусом `active` существует, иначе `False`.

    Исключения и особые случаи:
    - для неавторизованного пользователя функция возвращает `False`.

    Побочные эффекты:
    - отсутствуют.
    """

    if not user or not user.is_authenticated:
        return False
    return DialogSession.objects.filter(user=user, status=DialogStatus.ACTIVE).exists()
