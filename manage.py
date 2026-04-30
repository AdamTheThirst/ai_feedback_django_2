#!/usr/bin/env python
"""Точка входа для административных команд Django-проекта."""

import os
import sys

from django.core.management import execute_from_command_line


def main() -> None:
    """Запускает выполнение команд Django в выбранном окружении.

    Контекст использования:
    - применяется локально разработчиками и CI для запуска `runserver`, `migrate`, `test` и других команд;
    - по умолчанию использует настройки `config.settings.local`.

    Параметры:
    - не принимает именованных параметров напрямую; аргументы читаются из `sys.argv`.

    Возвращает:
    - ничего не возвращает; завершает процесс кодом возврата команды Django.

    Исключения:
    - возможны исключения Django при некорректной конфигурации окружения.

    Побочные эффекты:
    - инициализирует переменную окружения `DJANGO_SETTINGS_MODULE` при её отсутствии;
    - запускает обработку CLI-команды и может менять состояние БД/файлов в зависимости от команды.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
