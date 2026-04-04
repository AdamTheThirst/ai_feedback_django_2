"""Контентные модели игр, сценариев, промтов и медиа-ресурсов."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import ArchivableModel, OwnedModel, PublicIdModel, TimestampedModel


class Game(PublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Описывает игру как верхний контейнер сценариев и аналитических критериев.

    Контекст использования:
    - отображается на главной странице пользователя;
    - используется для группировки сценариев и аналитических промтов.

    Параметры:
    - `slug`, `title`, `short_description`, `sort_order`, `is_published`.

    Возвращает:
    - запись игры для пользовательского и административного контуров.

    Исключения и особые случаи:
    - `slug` должен быть уникальным глобально.

    Побочные эффекты:
    - архивирование скрывает игру из пользовательского списка.
    """

    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug")
    title = models.CharField(max_length=255, verbose_name="Название")
    short_description = models.TextField(blank=True, verbose_name="Краткое описание")
    sort_order = models.PositiveIntegerField(default=100, verbose_name="Порядок")
    is_published = models.BooleanField(default=True, verbose_name="Опубликована")

    class Meta:
        """Мета-настройки таблицы игр."""

        verbose_name = "Игра"
        verbose_name_plural = "Игры"
        ordering = ["sort_order", "title"]
        indexes = [
            models.Index(fields=["is_published", "is_archived", "sort_order"], name="idx_game_public_order"),
        ]

    def __str__(self) -> str:
        """Возвращает краткое имя игры для админки и логов.

        Контекст использования:
        - отображается в списках Django Admin и отладочной диагностике.

        Параметры:
        - отсутствуют.

        Возвращает:
        - значение поля `title`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return self.title


class ScenarioMediaAsset(PublicIdModel, ArchivableModel, TimestampedModel):
    """Хранит медиа-ресурс сценария с возможностью переиспользования и версионирования.

    Контекст использования:
    - позволяет привязывать одно изображение к нескольким сценариям;
    - сохраняет историю замен через ссылку `previous_version`.

    Параметры:
    - `title`, `file`, метаданные файла и `uploaded_by`.

    Возвращает:
    - запись медиа-ресурса для связки со сценариями.

    Исключения и особые случаи:
    - `file` обязателен;
    - старая версия может отсутствовать.

    Побочные эффекты:
    - отсутствуют.
    """

    title = models.CharField(max_length=255, verbose_name="Название файла")
    file = models.FileField(upload_to="scenario_media/", verbose_name="Файл")
    original_filename = models.CharField(max_length=255, blank=True, verbose_name="Исходное имя")
    mime_type = models.CharField(max_length=100, blank=True, verbose_name="MIME-тип")
    file_size_bytes = models.BigIntegerField(null=True, blank=True, verbose_name="Размер, байт")
    checksum_sha256 = models.CharField(max_length=64, blank=True, verbose_name="SHA256")
    previous_version = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="next_versions",
        verbose_name="Предыдущая версия",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_media_assets",
        verbose_name="Загрузил",
    )

    class Meta:
        """Мета-настройки таблицы медиа-ресурсов."""

        verbose_name = "Медиа-ресурс сценария"
        verbose_name_plural = "Медиа-ресурсы сценариев"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Возвращает компактное имя медиа-ресурса.

        Контекст использования:
        - нужно для визуального выбора файла в админке.

        Параметры:
        - отсутствуют.

        Возвращает:
        - название ресурса.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return self.title


class Scenario(PublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Описывает конкретный сценарий внутри выбранной игры.

    Контекст использования:
    - отображается кнопкой на главной странице;
    - хранит пользовательские `conditions` и стартовое сообщение персонажа.

    Параметры:
    - `game`, `slug`, `title`, `conditions_text`, `opening_message_text`, `media_asset`, `sort_order`, `is_published`.

    Возвращает:
    - запись сценария, доступную для запуска диалога.

    Исключения и особые случаи:
    - уникальность `slug` обеспечивается в пределах одной игры.

    Побочные эффекты:
    - архивирование скрывает сценарий из пользовательского запуска.
    """

    game = models.ForeignKey("content.Game", on_delete=models.PROTECT, related_name="scenarios", verbose_name="Игра")
    slug = models.SlugField(max_length=120, verbose_name="Slug")
    title = models.CharField(max_length=255, verbose_name="Название")
    short_description = models.TextField(blank=True, verbose_name="Краткое описание")
    conditions_text = models.TextField(verbose_name="Условия сценария")
    opening_message_text = models.TextField(verbose_name="Стартовое сообщение персонажа")
    media_asset = models.ForeignKey(
        "content.ScenarioMediaAsset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scenarios",
        verbose_name="Медиа-ресурс",
    )
    sort_order = models.PositiveIntegerField(default=100, verbose_name="Порядок")
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")

    class Meta:
        """Мета-настройки таблицы сценариев."""

        verbose_name = "Сценарий"
        verbose_name_plural = "Сценарии"
        ordering = ["game", "sort_order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["game", "slug"], name="uniq_scenario_slug_in_game"),
            models.UniqueConstraint(fields=["game", "sort_order"], name="uniq_scenario_sort_in_game"),
        ]
        indexes = [
            models.Index(fields=["game", "is_published", "is_archived"], name="idx_scenario_game_public"),
        ]

    def __str__(self) -> str:
        """Возвращает строковое представление сценария с названием игры.

        Контекст использования:
        - помогает различать одноимённые сценарии в админке.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку `<game.title> / <title>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.game.title} / {self.title}"


class ScenarioPrompt(PublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Хранит версию игрового промта, привязанного к сценарию.

    Контекст использования:
    - задаёт ролевое поведение ИИ для конкретного сценария;
    - поддерживает архивирование и смену активной версии.

    Параметры:
    - `scenario`, `title`, `prompt_text`, `is_active`.

    Возвращает:
    - запись промта для выбора при старте диалога.

    Исключения и особые случаи:
    - одновременно активным может быть только один промт на сценарий.

    Побочные эффекты:
    - архивный промт исключается из новых запусков.
    """

    scenario = models.ForeignKey("content.Scenario", on_delete=models.PROTECT, related_name="scenario_prompts", verbose_name="Сценарий")
    title = models.CharField(max_length=255, verbose_name="Название версии")
    prompt_text = models.TextField(verbose_name="Текст промта")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        """Мета-настройки таблицы игровых промтов."""

        verbose_name = "Игровой промт"
        verbose_name_plural = "Игровые промты"
        constraints = [
            models.UniqueConstraint(
                fields=["scenario"],
                condition=models.Q(is_active=True),
                name="uniq_active_prompt_per_scenario",
            )
        ]

    def __str__(self) -> str:
        """Возвращает имя версии игрового промта.

        Контекст использования:
        - используется в административных списках.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку `<scenario.title> / <title>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.scenario.title} / {self.title}"


class AnalysisPrompt(PublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Описывает один аналитический критерий в рамках игры.

    Контекст использования:
    - применяется анализатором после завершения диалога;
    - определяет порядок карточек и границы шкалы баллов.

    Параметры:
    - `game`, `alias`, `title`, `header_text`, `comment_text`, `prompt_text`, `sort_order`, `min_rating`, `max_rating`, `is_active`.

    Возвращает:
    - запись аналитического критерия.

    Исключения и особые случаи:
    - `min_rating` не должен быть больше `max_rating`.

    Побочные эффекты:
    - отсутствуют.
    """

    game = models.ForeignKey("content.Game", on_delete=models.PROTECT, related_name="analysis_prompts", verbose_name="Игра")
    alias = models.SlugField(max_length=120, verbose_name="Alias")
    title = models.CharField(max_length=255, verbose_name="Название")
    header_text = models.CharField(max_length=255, verbose_name="Заголовок карточки")
    comment_text = models.TextField(blank=True, verbose_name="Комментарий")
    prompt_text = models.TextField(verbose_name="Текст аналитического промта")
    sort_order = models.PositiveIntegerField(default=100, verbose_name="Порядок")
    min_rating = models.SmallIntegerField(default=0, verbose_name="Минимальный балл")
    max_rating = models.SmallIntegerField(default=5, verbose_name="Максимальный балл")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        """Мета-настройки таблицы аналитических промтов."""

        verbose_name = "Аналитический промт"
        verbose_name_plural = "Аналитические промты"
        ordering = ["game", "sort_order"]
        constraints = [
            models.UniqueConstraint(fields=["game", "alias"], name="uniq_analysis_alias_in_game"),
            models.UniqueConstraint(fields=["game", "sort_order"], name="uniq_analysis_sort_in_game"),
        ]

    def clean(self) -> None:
        """Проверяет корректность диапазона шкалы оценивания.

        Контекст использования:
        - вызывается перед сохранением формы/модели в административном контуре.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - `ValidationError`, если `min_rating > max_rating`.

        Побочные эффекты:
        - отсутствуют.
        """

        super().clean()
        if self.min_rating > self.max_rating:
            raise ValidationError("Минимальный балл не может быть больше максимального.")

    def __str__(self) -> str:
        """Возвращает краткое имя аналитического критерия.

        Контекст использования:
        - отображается в списках и селекторах админки.

        Параметры:
        - отсутствуют.

        Возвращает:
        - строку `<game.title> / <title>`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return f"{self.game.title} / {self.title}"


class SystemPrompt(PublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Хранит глобальный системный промт для служебных задач платформы.

    Контекст использования:
    - используется для внутренних AI-процессов (например, генерации метаданных аналитики);
    - управляется только административными ролями верхнего уровня.

    Параметры:
    - `key`, `title`, `prompt_text`, `is_active`.

    Возвращает:
    - запись системного промта.

    Исключения и особые случаи:
    - `key` уникален в пределах таблицы.

    Побочные эффекты:
    - влияет на поведение системных AI-сервисов.
    """

    key = models.SlugField(max_length=120, unique=True, verbose_name="Ключ")
    title = models.CharField(max_length=255, verbose_name="Название")
    prompt_text = models.TextField(verbose_name="Текст системного промта")
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        """Мета-настройки таблицы системных промтов."""

        verbose_name = "Системный промт"
        verbose_name_plural = "Системные промты"

    def __str__(self) -> str:
        """Возвращает название системного промта.

        Контекст использования:
        - отображается в административных списках.

        Параметры:
        - отсутствуют.

        Возвращает:
        - значение поля `title`.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        return self.title
