"""Тесты PDF-экспорта результатов: формат ответа, длинный транскрипт, повторный экспорт и доступ."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus, DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession


class DialogExportPdfViewTests(TestCase):
    """Проверяет endpoint экспорта PDF и ограничение доступа владельцем.

    Контекст использования:
    - покрывает `dialogs:export_pdf` в итерации 10.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовый диалог с анализом и длинным транскриптом.
    """

    def setUp(self) -> None:
        """Создаёт пользователей и завершённый диалог с результатами анализа.

        Контекст использования:
        - вызывается перед каждым тестом набора.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - записывает в БД сущности для сценариев экспорта.
        """

        self.owner = User.objects.create_user(email="pdf-owner@example.com", password="pass12345", nickname="Owner")
        self.other = User.objects.create_user(email="pdf-other@example.com", password="pass12345", nickname="Other")
        self.game = Game.objects.create(slug="pdf-game", title="PDF Game", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="pdf-scenario",
            title="PDF Scenario",
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
        long_text = "Очень длинный текст " * 300
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=2, role=DialogMessageRole.USER, text=long_text)

        analysis_prompt = AnalysisPrompt.objects.create(
            game=self.game,
            alias="pdf-crit",
            title="Критерий PDF",
            header_text="Заголовок",
            comment_text="Комментарий",
            prompt_text="prompt",
            sort_order=10,
            min_rating=0,
            max_rating=5,
            is_active=True,
        )
        analysis_run = AnalysisRun.objects.create(dialog=self.dialog, status=AnalysisRunStatus.COMPLETED)
        AnalysisResult.objects.create(
            analysis_run=analysis_run,
            analysis_prompt=analysis_prompt,
            sort_order_snapshot=10,
            alias_snapshot="pdf-crit",
            title_snapshot="Критерий PDF",
            header_snapshot_text="Заголовок",
            comment_snapshot_text="Комментарий",
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

    def test_owner_can_export_pdf_and_repeat_export(self) -> None:
        """Проверяет успешный экспорт PDF и повторный вызов endpoint-а.

        Контекст использования:
        - подтверждает идемпотентность бизнес-результата экспорта.

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
        url = reverse("dialogs:export_pdf", kwargs={"public_id": self.dialog.public_id})

        first = self.client.get(url)
        second = self.client.get(url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=", first["Content-Disposition"])
        self.assertTrue(first.content.startswith(b"%PDF"))
        self.assertTrue(second.content.startswith(b"%PDF"))
        self.assertGreater(len(first.content), 2000)

    def test_other_user_cannot_export_foreign_pdf(self) -> None:
        """Проверяет запрет экспорта чужого результата.

        Контекст использования:
        - обязательный security-кейс для endpoint-а экспорта.

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
        response = self.client.get(reverse("dialogs:export_pdf", kwargs={"public_id": self.dialog.public_id}))

        self.assertEqual(response.status_code, 404)
