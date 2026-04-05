"""Тесты личного кабинета: профиль, история, индикаторы и персональный таймер."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.core.enums import AnalysisRunStatus, AnalysisValidationStatus, DialogEndedReason, DialogMessageRole, DialogStatus
from apps.dialogs.models import DialogMessage, DialogSession


class CabinetViewTests(TestCase):
    """Проверяет базовые сценарии личного кабинета пользователя."""

    def setUp(self) -> None:
        """Подготавливает пользователя и завершённую сессию с анализом для истории/метрик."""

        self.user = User.objects.create_user(email="cab@example.com", password="pass12345", nickname="Cab")
        self.client.login(username=self.user.email, password="pass12345")

        game = Game.objects.create(slug="cab-game", title="Cab Game", is_published=True)
        scenario = Scenario.objects.create(
            game=game,
            slug="cab-scen",
            title="Cab Scenario",
            conditions_text="c",
            opening_message_text="o",
            is_published=True,
        )
        prompt = ScenarioPrompt.objects.create(scenario=scenario, title="sp", prompt_text="pt", is_active=True)
        dialog = DialogSession.objects.create(
            user=self.user,
            game=game,
            scenario=scenario,
            scenario_prompt_used=prompt,
            status=DialogStatus.FINISHED,
            ended_reason=DialogEndedReason.MANUAL_FEEDBACK,
            user_message_count=1,
            assistant_message_count=1,
            conditions_snapshot_text="c",
            opening_message_snapshot_text="o",
        )
        DialogMessage.objects.create(dialog=dialog, sequence_no=1, role=DialogMessageRole.ASSISTANT, text="o")
        DialogMessage.objects.create(dialog=dialog, sequence_no=2, role=DialogMessageRole.USER, text="u")

        a_prompt = AnalysisPrompt.objects.create(
            game=game,
            alias="crit",
            title="Критерий",
            header_text="h",
            comment_text="",
            prompt_text="p",
            sort_order=10,
            min_rating=0,
            max_rating=5,
            is_active=True,
        )
        run = AnalysisRun.objects.create(dialog=dialog, status=AnalysisRunStatus.COMPLETED)
        AnalysisResult.objects.create(
            analysis_run=run,
            analysis_prompt=a_prompt,
            sort_order_snapshot=10,
            alias_snapshot="crit",
            title_snapshot="Критерий",
            header_snapshot_text="h",
            comment_snapshot_text="",
            rating=4,
            rating_min=0,
            rating_max=5,
            analysis_text="ok",
            raw_llm_response_text='{"rating":4,"text":"ok"}',
            parsed_json_snapshot={"rating": 4, "text": "ok"},
            validation_status=AnalysisValidationStatus.VALID,
            validation_error_message="",
            llm_attempt_count=1,
        )

    def test_cabinet_page_is_available_and_shows_history(self) -> None:
        """Проверяет отображение личного кабинета и ссылки на результат в истории."""

        response = self.client.get(reverse("cabinet_entry"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Личный кабинет")
        self.assertContains(response, "Результат")

    def test_cabinet_updates_nickname(self) -> None:
        """Проверяет обновление nickname через форму профиля в кабинете."""

        response = self.client.post(reverse("cabinet_entry"), {"action": "update_nickname", "nickname": "NewNick"})
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "NewNick")

    def test_cabinet_updates_personal_timer(self) -> None:
        """Проверяет сохранение персональной настройки таймера 5..20 минут."""

        response = self.client.post(
            reverse("cabinet_entry"),
            {
                "action": "update_timer",
                "preferred_dialog_duration_minutes": 15,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_dialog_duration_minutes, 15)
