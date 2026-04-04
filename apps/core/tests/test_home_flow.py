"""Тесты главной страницы и запуска сценария с ограничением активного диалога."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.content.models import Game, Scenario
from apps.core.enums import DialogStatus
from apps.dialogs.models import DialogSession


class HomeFlowTests(TestCase):
    """Проверяет пользовательский flow главной страницы и запуск сценария.

    Контекст использования:
    - валидирует ключевые требования итерации 5:
      список игр/сценариев, нижние точки входа и запрет второго активного диалога.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые записи пользователей, игр и диалогов.
    """

    def setUp(self) -> None:
        """Подготавливает пользователя и один опубликованный сценарий.

        Контекст использования:
        - выполняется перед каждым тестом.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт базовые записи в тестовой БД.
        """

        self.user = User.objects.create_user(email="player@example.com", password="pass12345", nickname="Player")
        self.game = Game.objects.create(slug="game-1", title="Game 1", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="scenario-1",
            title="Scenario 1",
            conditions_text="conditions",
            opening_message_text="opening",
            is_published=True,
        )

    def test_home_displays_game_and_scenario_buttons(self) -> None:
        """Проверяет отображение списка игр, сценариев и нижней навигации.

        Контекст использования:
        - подтверждает корректный рендер главной страницы после входа.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.client.login(username=self.user.email, password="pass12345")
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Game 1")
        self.assertContains(response, "Scenario 1")
        self.assertContains(response, "Энциклопедия")
        self.assertContains(response, "Личный кабинет")
        self.assertContains(response, "Выйти")

    def test_start_scenario_is_blocked_when_active_dialog_exists(self) -> None:
        """Проверяет, что при активном диалоге второй запуск сценария блокируется.

        Контекст использования:
        - валидирует продуктовый инвариант «один активный диалог на пользователя».

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт первую активную диалоговую сессию.
        """

        self.client.login(username=self.user.email, password="pass12345")
        DialogSession.objects.create(user=self.user, status=DialogStatus.ACTIVE)

        response = self.client.post(
            reverse("scenario_start", kwargs={"game_slug": self.game.slug, "scenario_slug": self.scenario.slug}),
            follow=True,
        )

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "У вас уже есть активный диалог")
        self.assertEqual(DialogSession.objects.filter(user=self.user, status=DialogStatus.ACTIVE).count(), 1)

    def test_start_scenario_creates_dialog_and_redirects(self) -> None:
        """Проверяет создание сессии при первом запуске сценария.

        Контекст использования:
        - подтверждает корректный POST-flow кнопки сценария.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт новую запись `DialogSession`.
        """

        self.client.login(username=self.user.email, password="pass12345")

        response = self.client.post(
            reverse("scenario_start", kwargs={"game_slug": self.game.slug, "scenario_slug": self.scenario.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(DialogSession.objects.filter(user=self.user).count(), 1)
