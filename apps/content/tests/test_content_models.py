"""Тесты ключевых ограничений контент-домена."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt


class ContentDomainTests(TestCase):
    """Проверяет базовые ограничения моделей контента и промтов.

    Контекст использования:
    - защищает от регрессий ограничений уникальности и валидации шкал.

    Параметры:
    - класс не принимает внешних параметров.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые записи в временной БД.
    """

    def setUp(self) -> None:
        """Готовит пользователя-владельца и базовую игру для тестов.

        Контекст использования:
        - выполняется перед каждым тестовым методом.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт пользователя и игру в тестовой БД.
        """

        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345", nickname="Owner")
        self.game = Game.objects.create(slug="test-game", title="Test Game", created_by=self.owner)

    def test_single_active_prompt_per_scenario(self) -> None:
        """Проверяет ограничение одной активной версии игрового промта на сценарий.

        Контекст использования:
        - валидирует уникальный частичный constraint модели `ScenarioPrompt`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - ожидается `IntegrityError` при попытке добавить второй активный промт.

        Побочные эффекты:
        - отсутствуют.
        """

        scenario = Scenario.objects.create(
            game=self.game,
            slug="scenario-1",
            title="Scenario 1",
            conditions_text="Conditions",
            opening_message_text="Opening",
            created_by=self.owner,
        )
        ScenarioPrompt.objects.create(scenario=scenario, title="v1", prompt_text="prompt", is_active=True, created_by=self.owner)
        with self.assertRaises(IntegrityError):
            ScenarioPrompt.objects.create(scenario=scenario, title="v2", prompt_text="prompt2", is_active=True, created_by=self.owner)

    def test_analysis_prompt_rating_validation(self) -> None:
        """Проверяет валидацию диапазона оценивания аналитического критерия.

        Контекст использования:
        - подтверждает, что `min_rating` не может превышать `max_rating`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - ожидается `ValidationError` при некорректных границах.

        Побочные эффекты:
        - отсутствуют.
        """

        prompt = AnalysisPrompt(
            game=self.game,
            alias="criterion",
            title="Criterion",
            header_text="Header",
            prompt_text="Prompt",
            min_rating=5,
            max_rating=1,
            created_by=self.owner,
        )
        with self.assertRaises(ValidationError):
            prompt.full_clean()
