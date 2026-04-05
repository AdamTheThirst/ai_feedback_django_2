"""Регистрация контентных моделей в Django Admin."""

from django.contrib import admin, messages

from apps.content.models import (
    AnalysisPrompt,
    EncyclopediaArticle,
    Game,
    Scenario,
    ScenarioMediaAsset,
    ScenarioPrompt,
    SystemPrompt,
)
from apps.content.services.encyclopedia import build_article_summary


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
    """Настраивает отображение сценариев в административном интерфейсе."""

    list_display = ("title", "game", "sort_order", "is_published", "is_archived", "created_by")
    list_filter = ("game", "is_published", "is_archived")
    search_fields = ("title", "slug", "game__title")

    def get_form(self, request, obj=None, change=False, **kwargs):
        """Добавляет пояснения к полям сценария в админ-форме.

        Контекст использования:
        - используется при создании/редактировании `Scenario` в Django Admin;
        - снижает путаницу между «Кратким описанием» и «Условиями сценария».

        Параметры:
        - `request`: текущий HTTP-запрос;
        - `obj`: редактируемый объект или `None`;
        - `change`: флаг режима редактирования;
        - `**kwargs`: дополнительные параметры `ModelAdmin.get_form`.

        Возвращает:
        - класс формы администратора с обновлёнными `help_text`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - изменяет текст подсказок в форме админки.
        """

        form = super().get_form(request, obj=obj, change=change, **kwargs)
        if "short_description" in form.base_fields:
            form.base_fields["short_description"].help_text = (
                "Краткое описание показывается в админке и карточках контента. "
                "Этот текст не вставляется в чат персонажа."
            )
        if "conditions_text" in form.base_fields:
            form.base_fields["conditions_text"].help_text = (
                "Условия сценария видит пользователь вверху экрана чата. "
                "Это рабочий контекст упражнения для диалога."
            )
        return form


@admin.register(ScenarioPrompt)
class ScenarioPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение игровых промтов в административном интерфейсе."""

    list_display = ("title", "scenario", "is_active", "is_archived", "created_by")
    list_filter = ("is_active", "is_archived")
    search_fields = ("title", "scenario__title")


@admin.register(AnalysisPrompt)
class AnalysisPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение аналитических промтов в административном интерфейсе."""

    list_display = ("title", "game", "alias", "sort_order", "is_active", "is_archived")
    list_filter = ("game", "is_active", "is_archived")
    search_fields = ("title", "alias", "game__title")


@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    """Настраивает отображение системных промтов в административном интерфейсе."""

    list_display = ("title", "key", "is_active", "is_archived", "created_by")
    list_filter = ("is_active", "is_archived")
    search_fields = ("title", "key")


@admin.register(ScenarioMediaAsset)
class ScenarioMediaAssetAdmin(admin.ModelAdmin):
    """Настраивает отображение медиа-ресурсов сценариев в административном интерфейсе."""

    list_display = ("title", "mime_type", "file_size_bytes", "is_archived", "uploaded_by")
    list_filter = ("is_archived",)
    search_fields = ("title", "original_filename", "checksum_sha256")


@admin.register(EncyclopediaArticle)
class EncyclopediaArticleAdmin(admin.ModelAdmin):
    """Управляет статьями энциклопедии и генерацией их summary через LLM.

    Контекст использования:
    - предоставляет CRUD для админов/суперадминов;
    - поддерживает массовую и точечную генерацию краткого описания статьи.

    Параметры:
    - используется стандартный набор атрибутов `ModelAdmin` и action `regenerate_summary_action`.

    Возвращает:
    - административный интерфейс модели `EncyclopediaArticle`.

    Исключения и особые случаи:
    - поле summary необязательно и может быть пустым.

    Побочные эффекты:
    - при генерации summary вызывает LLM-адаптер и сохраняет обновлённые данные статей.
    """

    list_display = ("title", "slug", "is_published", "created_by", "updated_by", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "summary")
    readonly_fields = ("slug", "created_at", "updated_at", "created_by", "updated_by")
    actions = ["regenerate_summary_action"]
    fieldsets = (
        (
            "Основные данные",
            {
                "fields": ("title", "slug", "body", "summary", "is_published"),
                "description": "Текст статьи ограничен 5000 символами. Краткое описание опционально; при необходимости можно сгенерировать через action.",
            },
        ),
        ("Аудит", {"fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change) -> None:
        """Сохраняет статью и заполняет служебные поля автора/редактора.

        Контекст использования:
        - вызывается Django Admin при создании и редактировании статьи.

        Параметры:
        - `request`: текущий HTTP-запрос админки;
        - `obj`: сохраняемая статья;
        - `form`: форма admin-интерфейса;
        - `change`: флаг режима редактирования существующей записи.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - записывает в БД `created_by`, `updated_by` и, при необходимости, `summary`.
        """

        if not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Перегенерировать summary через LLM")
    def regenerate_summary_action(self, request, queryset) -> None:
        """Массово перегенерирует summary для выбранных статей через LLM-адаптер.

        Контекст использования:
        - action в списке статей админки.

        Параметры:
        - `request`: текущий HTTP-запрос;
        - `queryset`: выбранный набор статей.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - обновляет поле `summary` и `updated_by` у выбранных статей.
        """

        updated_count = 0
        for article in queryset:
            article.summary = build_article_summary(title=article.title, body=article.body)
            article.updated_by = request.user
            article.save(update_fields=["summary", "updated_by", "updated_at"])
            updated_count += 1

        self.message_user(request, f"Перегенерировано summary: {updated_count} шт.", level=messages.SUCCESS)
