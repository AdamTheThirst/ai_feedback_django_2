"""Тесты HTML-экрана результатов и защиты доступа к чужому диалогу."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus, DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession


class DialogResultsViewTests(TestCase):
    """Проверяет отображение `N из M`, карточек и защиту доступа.

    Контекст использования:
    - покрывает endpoint `dialogs:results` в итерации 9.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые данные в БД.
    """

    def setUp(self) -> None:
        """Подготавливает пользователей, завершённый диалог и анализ.

        Контекст использования:
        - выполняется перед каждым тестом класса.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт связанные записи диалога, анализа и результатов.
        """

        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345", nickname="Owner")
        self.other = User.objects.create_user(email="other@example.com", password="pass12345", nickname="Other")
        self.game = Game.objects.create(slug="results-game", title="Results Game", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="results-scenario",
            title="Results Scenario",
            conditions_text="cond",
            opening_message_text="open",
            is_published=True,
        )
        self.prompt = ScenarioPrompt.objects.create(scenario=self.scenario, title="main", prompt_text="p", is_active=True)

        self.dialog = DialogSession.objects.create(
            user=self.owner,
            game=self.game,
            scenario=self.scenario,
            scenario_prompt_used=self.prompt,
            status=DialogStatus.FINISHED,
            ended_reason=DialogEndedReason.MANUAL_FEEDBACK,
            user_message_count=1,
            assistant_message_count=1,
            conditions_snapshot_text="cond",
            opening_message_snapshot_text="open",
        )
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=1, role=DialogMessageRole.ASSISTANT, text="open")
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=2, role=DialogMessageRole.USER, text="hi")

        self.a_prompt = AnalysisPrompt.objects.create(
            game=self.game,
            alias="crit-1",
            title="Критерий 1",
            header_text="Заголовок",
            comment_text="",
            prompt_text="prompt",
            sort_order=10,
            min_rating=0,
            max_rating=5,
            is_active=True,
        )
        self.analysis_run = AnalysisRun.objects.create(dialog=self.dialog, status=AnalysisRunStatus.COMPLETED)
        AnalysisResult.objects.create(
            analysis_run=self.analysis_run,
            analysis_prompt=self.a_prompt,
            sort_order_snapshot=10,
            alias_snapshot="crit-1",
            title_snapshot="Критерий 1",
            header_snapshot_text="Заголовок",
            comment_snapshot_text="",
            rating=4,
            rating_min=0,
            rating_max=5,
            analysis_text="Текст анализа",
            raw_llm_response_text='{"rating":4,"text":"Текст анализа"}',
            parsed_json_snapshot={"rating": 4, "text": "Текст анализа"},
            validation_status=AnalysisValidationStatus.VALID,
            validation_error_message="",
            llm_attempt_count=1,
        )

    def test_owner_can_open_results_and_see_score(self) -> None:
        """Проверяет отображение суммы и карточек на странице владельца.

        Контекст использования:
        - подтверждает основной пользовательский сценарий просмотра результатов.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.client.login(username=self.owner.email, password="pass12345")
        response = self.client.get(reverse("dialogs:results", kwargs={"public_id": self.dialog.public_id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Критерий 1")
        self.assertContains(response, "Текст анализа")
        self.assertNotContains(response, "Сырой ответ LLM")
        self.assertNotContains(response, "Статус валидации")
        self.assertNotContains(response, "из 5")


    def test_staff_user_also_does_not_see_technical_llm_fields(self) -> None:
        """Проверяет, что технические поля LLM скрыты даже для staff-пользователя.

        Контекст использования:
        - фиксирует требование показывать только распарсенные данные аналитики всем ролям.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.owner.is_staff = True
        self.owner.save(update_fields=["is_staff"])

        self.client.login(username=self.owner.email, password="pass12345")
        response = self.client.get(reverse("dialogs:results", kwargs={"public_id": self.dialog.public_id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Текст анализа")
        self.assertNotContains(response, "Сырой ответ LLM")
        self.assertNotContains(response, "Статус валидации")
        self.assertNotContains(response, "Взаимодействие с LLM")

    def test_other_user_cannot_open_foreign_results(self) -> None:
        """Проверяет защиту от доступа к чужим результатам.

        Контекст использования:
        - реализует обязательный security-кейс для экрана результата.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.client.login(username=self.other.email, password="pass12345")
        response = self.client.get(reverse("dialogs:results", kwargs={"public_id": self.dialog.public_id}))

        self.assertEqual(response.status_code, 404)
