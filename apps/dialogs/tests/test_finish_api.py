"""Тесты JSON-endpoint-ов завершения сессии и таймерного поведения."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.auditlog.models import AuditLogEntry
from apps.content.models import Game, Scenario, ScenarioPrompt
from apps.core.enums import DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession


class DialogFinishApiTests(TestCase):
    """Проверяет ручное завершение, таймаут и сигнал покидания страницы.

    Контекст использования:
    - покрывает endpoint-ы `dialogs:finish` и `dialogs:page_leave`.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые записи в изолированной базе.
    """

    def setUp(self) -> None:
        """Создаёт пользователя и активную сессию для сценариев завершения.

        Контекст использования:
        - выполняется перед каждым тестом набора.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - заполняет тестовые сущности пользователя, контента и диалога.
        """

        self.user = User.objects.create_user(email="finish@example.com", password="pass12345", nickname="FinishUser")
        self.game = Game.objects.create(slug="finish-game", title="Finish Game", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="finish-scenario",
            title="Finish Scenario",
            conditions_text="conditions",
            opening_message_text="opening",
            is_published=True,
        )
        self.prompt = ScenarioPrompt.objects.create(scenario=self.scenario, title="active", prompt_text="prompt", is_active=True)
        self.dialog = DialogSession.objects.create(
            user=self.user,
            game=self.game,
            scenario=self.scenario,
            scenario_prompt_used=self.prompt,
            conditions_snapshot_text=self.scenario.conditions_text,
            opening_message_snapshot_text=self.scenario.opening_message_text,
            effective_duration_seconds=600,
        )
        DialogMessage.objects.create(
            dialog=self.dialog,
            sequence_no=1,
            role=DialogMessageRole.ASSISTANT,
            text=self.scenario.opening_message_text,
        )
        self.dialog.assistant_message_count = 1
        self.dialog.save(update_fields=["assistant_message_count", "updated_at"])
        self.client.login(username=self.user.email, password="pass12345")

    def test_manual_finish_moves_dialog_to_finished(self) -> None:
        """Проверяет ручное завершение активного диалога.

        Контекст использования:
        - подтверждает базовый сценарий кнопки «Дай обратную связь».

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - переводит сессию в финальный статус.
        """

        DialogMessage.objects.create(dialog=self.dialog, sequence_no=2, role=DialogMessageRole.USER, text="Реплика")
        self.dialog.user_message_count = 1
        self.dialog.save(update_fields=["user_message_count", "updated_at"])

        response = self.client.post(
            reverse("dialogs:finish", kwargs={"public_id": self.dialog.public_id}),
            data={"reason": DialogEndedReason.MANUAL_FEEDBACK},
        )

        self.assertEqual(response.status_code, 200)
        self.dialog.refresh_from_db()
        self.assertEqual(self.dialog.status, DialogStatus.FINISHED)
        self.assertEqual(self.dialog.ended_reason, DialogEndedReason.MANUAL_FEEDBACK)

    def test_timeout_finish_without_user_messages_skips_analysis(self) -> None:
        """Проверяет завершение без пользовательских реплик как `analysis_skipped`.

        Контекст использования:
        - подтверждает продуктовое правило «нет реплик — анализ не запускается».

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - переводит статус в `analysis_skipped`.
        """

        response = self.client.post(
            reverse("dialogs:finish", kwargs={"public_id": self.dialog.public_id}),
            data={"reason": DialogEndedReason.TIMEOUT},
        )

        self.assertEqual(response.status_code, 200)
        self.dialog.refresh_from_db()
        self.assertEqual(self.dialog.status, DialogStatus.ANALYSIS_SKIPPED)
        self.assertEqual(self.dialog.ended_reason, DialogEndedReason.NO_USER_MESSAGES)

    def test_page_leave_marks_dialog_as_aborted(self) -> None:
        """Проверяет завершение при покидании страницы через отдельный endpoint.

        Контекст использования:
        - покрывает интеграцию клиентского `sendBeacon` с серверной фиксацией причины.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - переводит активный диалог в `aborted`.
        """

        DialogMessage.objects.create(dialog=self.dialog, sequence_no=2, role=DialogMessageRole.USER, text="Реплика")
        self.dialog.user_message_count = 1
        self.dialog.save(update_fields=["user_message_count", "updated_at"])

        response = self.client.post(reverse("dialogs:page_leave", kwargs={"public_id": self.dialog.public_id}))

        self.assertEqual(response.status_code, 200)
        self.dialog.refresh_from_db()
        self.assertEqual(self.dialog.status, DialogStatus.ABORTED)
        self.assertEqual(self.dialog.ended_reason, DialogEndedReason.PAGE_LEAVE)

    def test_send_message_after_timeout_returns_error(self) -> None:
        """Проверяет блокировку отправки сообщений после истечения времени.

        Контекст использования:
        - гарантирует серверную защиту, даже если клиентский таймер не сработал.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - переводит сессию в финальный статус и не создаёт новые реплики.
        """

        self.dialog.started_at = timezone.now() - timedelta(minutes=15)
        self.dialog.effective_duration_seconds = 60
        self.dialog.save(update_fields=["started_at", "effective_duration_seconds", "updated_at"])

        response = self.client.post(
            reverse("dialogs:send_message", kwargs={"public_id": self.dialog.public_id}),
            data={"text": "Привет"},
        )

        self.assertEqual(response.status_code, 400)
        self.dialog.refresh_from_db()
        self.assertEqual(self.dialog.status, DialogStatus.ANALYSIS_SKIPPED)
        self.assertEqual(self.dialog.ended_reason, DialogEndedReason.NO_USER_MESSAGES)

    def test_unhandled_finish_error_is_logged_and_returns_500(self) -> None:
        """Проверяет логирование и JSON-ответ 500 при непредвиденной ошибке finish API.

        Контекст использования:
        - подтверждает диагностируемость кейсов, когда клиент видит сетевую/серверную ошибку.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт запись `AuditLogEntry` с event_type `dialogs.finish.unhandled_error`.
        """

        with patch("apps.dialogs.views.finish_dialog", side_effect=RuntimeError("boom")):
            response = self.client.post(
                reverse("dialogs:finish", kwargs={"public_id": self.dialog.public_id}),
                data={"reason": DialogEndedReason.MANUAL_FEEDBACK},
            )

        self.assertEqual(response.status_code, 500)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                event_type="dialogs.finish.unhandled_error",
                dialog=self.dialog,
            ).exists()
        )
