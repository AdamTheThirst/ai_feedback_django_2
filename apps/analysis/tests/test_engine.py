"""Тесты движка аналитики: транскрипт, JSON-валидация, сохранение результатов и audit log."""

from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import User
from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.analysis.services.engine import run_analysis_for_dialog
from apps.auditlog.models import AuditLogEntry
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus, DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession


class AnalysisEngineTests(TestCase):
    """Проверяет запуск аналитики по всем критериям и обработку невалидного JSON.

    Контекст использования:
    - покрывает сервис `run_analysis_for_dialog` как ядро итерации 8.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые сущности в изолированной БД.
    """

    def setUp(self) -> None:
        """Подготавливает завершённый диалог и два аналитических критерия.

        Контекст использования:
        - выполняется перед каждым тестом.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт пользователя, контент и сообщения диалога.
        """

        self.user = User.objects.create_user(email="ana@example.com", password="pass12345", nickname="Ana")
        self.game = Game.objects.create(slug="g1", title="Game", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="s1",
            title="Scenario",
            conditions_text="Условия",
            opening_message_text="Старт",
            is_published=True,
        )
        self.prompt = ScenarioPrompt.objects.create(scenario=self.scenario, title="p", prompt_text="pt", is_active=True)
        self.dialog = DialogSession.objects.create(
            user=self.user,
            game=self.game,
            scenario=self.scenario,
            scenario_prompt_used=self.prompt,
            status=DialogStatus.FINISHED,
            ended_reason=DialogEndedReason.MANUAL_FEEDBACK,
            user_message_count=1,
            assistant_message_count=2,
            conditions_snapshot_text="Условия",
            opening_message_snapshot_text="Старт",
        )
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=1, role=DialogMessageRole.ASSISTANT, text="Старт")
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=2, role=DialogMessageRole.USER, text="Реплика 1")
        DialogMessage.objects.create(dialog=self.dialog, sequence_no=3, role=DialogMessageRole.ASSISTANT, text="Ответ 1")

        self.a_prompt_1 = AnalysisPrompt.objects.create(
            game=self.game,
            alias="focus",
            title="Фокус",
            header_text="Фокус на цели",
            comment_text="Комментарий",
            prompt_text="Промт 1",
            sort_order=10,
            min_rating=0,
            max_rating=5,
            is_active=True,
        )
        self.a_prompt_2 = AnalysisPrompt.objects.create(
            game=self.game,
            alias="clarity",
            title="Ясность",
            header_text="Ясность",
            comment_text="",
            prompt_text="Промт 2",
            sort_order=20,
            min_rating=1,
            max_rating=5,
            is_active=True,
        )

    def test_engine_creates_run_and_result_for_each_prompt(self) -> None:
        """Проверяет создание `AnalysisRun` и набора `AnalysisResult` по всем промтам.

        Контекст использования:
        - подтверждает основной контракт аналитического движка.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт записи анализа и audit log старта.
        """

        analysis_run = run_analysis_for_dialog(self.dialog)

        self.assertIsNotNone(analysis_run)
        assert analysis_run is not None
        self.assertEqual(analysis_run.status, AnalysisRunStatus.COMPLETED)
        self.assertEqual(AnalysisResult.objects.filter(analysis_run=analysis_run).count(), 2)
        self.assertTrue(AuditLogEntry.objects.filter(event_type="analysis.started", analysis_run=analysis_run).exists())

    def test_invalid_json_is_saved_as_fallback_and_logged(self) -> None:
        """Проверяет fallback-сохранение и audit log при невалидном JSON-ответе.

        Контекст использования:
        - подтверждает устойчивость анализа к невалидному ответу LLM.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт warning запись audit log и fallback-результат.
        """

        with patch("apps.analysis.services.engine.generate_analysis_reply", return_value="{bad-json"):
            analysis_run = run_analysis_for_dialog(self.dialog)

        self.assertIsNotNone(analysis_run)
        assert analysis_run is not None
        first_result = AnalysisResult.objects.filter(analysis_run=analysis_run).order_by("sort_order_snapshot").first()
        self.assertIsNotNone(first_result)
        assert first_result is not None
        self.assertEqual(first_result.validation_status, AnalysisValidationStatus.FALLBACK_SAVED)
        self.assertTrue(first_result.validation_error_message)
        self.assertTrue(AuditLogEntry.objects.filter(event_type="analysis.invalid_text", analysis_run=analysis_run).exists())

    def test_no_user_messages_skips_run_creation(self) -> None:
        """Проверяет, что без пользовательских реплик `AnalysisRun` не создаётся.

        Контекст использования:
        - подтверждает бизнес-правило пропуска аналитики при пустом пользовательском вкладе.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        self.dialog.user_message_count = 0
        self.dialog.save(update_fields=["user_message_count", "updated_at"])

        result = run_analysis_for_dialog(self.dialog)

        self.assertIsNone(result)
        self.assertEqual(AnalysisRun.objects.filter(dialog=self.dialog).count(), 0)

    def test_plain_text_response_is_saved_without_json_parsing(self) -> None:
        """Проверяет успешное сохранение обычного текстового ответа аналитики.

        Контекст использования:
        - подтверждает новый формат аналитики, где модель возвращает не JSON, а текст.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт корректный `AnalysisResult` без fallback-статуса.
        """

        plain_text = "Сфокусируйтесь на конкретных примерах поведения и их эффекте."
        with patch("apps.analysis.services.engine.generate_analysis_reply", return_value=plain_text):
            analysis_run = run_analysis_for_dialog(self.dialog)

        self.assertIsNotNone(analysis_run)
        assert analysis_run is not None
        first_result = AnalysisResult.objects.filter(analysis_run=analysis_run).order_by("sort_order_snapshot").first()
        self.assertIsNotNone(first_result)
        assert first_result is not None
        self.assertEqual(first_result.validation_status, AnalysisValidationStatus.VALID)
        self.assertEqual(first_result.analysis_text, plain_text)

    def test_empty_text_response_is_saved_as_fallback(self) -> None:
        """Проверяет fallback-сохранение при пустом текстовом ответе аналитики.

        Контекст использования:
        - подтверждает устойчивость движка к пустому ответу модели.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт warning запись audit log и fallback-результат.
        """

        with patch("apps.analysis.services.engine.generate_analysis_reply", return_value="   "):
            analysis_run = run_analysis_for_dialog(self.dialog)

        self.assertIsNotNone(analysis_run)
        assert analysis_run is not None
        first_result = AnalysisResult.objects.filter(analysis_run=analysis_run).order_by("sort_order_snapshot").first()
        self.assertIsNotNone(first_result)
        assert first_result is not None
        self.assertEqual(first_result.validation_status, AnalysisValidationStatus.FALLBACK_SAVED)
        self.assertTrue(first_result.validation_error_message)
        self.assertTrue(AuditLogEntry.objects.filter(event_type="analysis.invalid_text", analysis_run=analysis_run).exists())
