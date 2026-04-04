"""Регистрация контентных моделей в Django Admin."""

from django.contrib import admin

from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioMediaAsset, ScenarioPrompt, SystemPrompt


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Настраивает отображение игр в административном интерфейсе.

    Контекст использования:
    - применяется в Django Admin для управления играми контент-домена.

    Параметры:
    - конфигурация задаётся атрибутами `list_display`, `list_filter`, `search_fields`.

    Возвращает:
    - стандартный административный CRUD-интерфейс для модели `Game`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "slug", "sort_order", "is_published", "is_archived", "created_by")
    list_filter = ("is_published", "is_archived")
    search_fields = ("title", "slug")


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    """Настраивает отображение сценариев в административном интерфейсе.

    Контекст использования:
    - применяется в Django Admin для управления сценариями конкретных игр.

    Параметры:
    - фильтрация и поиск задаются через стандартные атрибуты `ModelAdmin`.

    Возвращает:
    - CRUD-интерфейс модели `Scenario`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "game", "sort_order", "is_published", "is_archived", "created_by")
    list_filter = ("game", "is_published", "is_archived")
    search_fields = ("title", "slug", "game__title")


@admin.register(ScenarioPrompt)
class ScenarioPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение игровых промтов в административном интерфейсе.

    Контекст использования:
    - применяется для управления активными и архивными версиями сценарных промтов.

    Параметры:
    - список и фильтры задаются атрибутами класса.

    Возвращает:
    - CRUD-интерфейс модели `ScenarioPrompt`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "scenario", "is_active", "is_archived", "created_by")
    list_filter = ("is_active", "is_archived")
    search_fields = ("title", "scenario__title")


@admin.register(AnalysisPrompt)
class AnalysisPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение аналитических промтов в административном интерфейсе.

    Контекст использования:
    - применяется для управления критериями анализа в рамках игры.

    Параметры:
    - сортировка, поиск и фильтрация определяются атрибутами класса.

    Возвращает:
    - CRUD-интерфейс модели `AnalysisPrompt`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "game", "alias", "sort_order", "is_active", "is_archived")
    list_filter = ("game", "is_active", "is_archived")
    search_fields = ("title", "alias", "game__title")


@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение системных промтов в административном интерфейсе.

    Контекст использования:
    - используется супер-администраторами для редактирования служебных промтов.

    Параметры:
    - настраивается атрибутами `ModelAdmin`.

    Возвращает:
    - CRUD-интерфейс модели `SystemPrompt`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "key", "is_active", "is_archived", "created_by")
    list_filter = ("is_active", "is_archived")
    search_fields = ("title", "key")


@admin.register(ScenarioMediaAsset)
class ScenarioMediaAssetAdmin(admin.ModelAdmin):
    """Настраивает отображение медиа-ресурсов сценариев в административном интерфейсе.

    Контекст использования:
    - обеспечивает управление файлами сценариев и их архивным состоянием.

    Параметры:
    - задаётся набор колонок и фильтров для навигации по медиа-ресурсам.

    Возвращает:
    - CRUD-интерфейс модели `ScenarioMediaAsset`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - отсутствуют.
    """

    list_display = ("title", "mime_type", "file_size_bytes", "is_archived", "uploaded_by")
    list_filter = ("is_archived",)
    search_fields = ("title", "original_filename", "checksum_sha256")
