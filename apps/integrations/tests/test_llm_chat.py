"""Тесты адаптера LLM для проверки параметров аналитических вызовов."""

from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import User
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.dialogs.models import DialogSession
from apps.integrations.services.llm_chat import generate_analysis_reply


class LlmChatAnalysisTests(TestCase):
    """Проверяет передачу max_tokens из аналитического промта в LLM-вызов."""

    def setUp(self) -> None:
        """Создаёт минимальный набор данных для вызова `generate_analysis_reply`.

        Контекст использования:
        - выполняется перед каждым тестом класса.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт тестовые записи пользователя, игры, сценария, промтов и диалога.
        """

        user = User.objects.create_user(email="llmtest@example.com", password="pass12345", nickname="LLM")
        game = Game.objects.create(slug="llm-game", title="LLM Game", is_published=True)
        scenario = Scenario.objects.create(
            game=game,
            slug="llm-scenario",
            title="LLM Scenario",
            conditions_text="cond",
            opening_message_text="open",
            is_published=True,
        )
        scenario_prompt = ScenarioPrompt.objects.create(scenario=scenario, title="sp", prompt_text="prompt", is_active=True)
        self.dialog = DialogSession.objects.create(
            user=user,
            game=game,
            scenario=scenario,
            scenario_prompt_used=scenario_prompt,
            conditions_snapshot_text="cond",
            opening_message_snapshot_text="open",
        )
        self.analysis_prompt = AnalysisPrompt.objects.create(
            game=game,
            alias="a1",
            title="Критерий",
            header_text="header",
            comment_text="",
            prompt_text="анализируй",
            sort_order=1,
            min_rating=0,
            max_rating=5,
            max_tokens=1234,
            is_active=True,
        )

    def test_generate_analysis_reply_uses_prompt_max_tokens(self) -> None:
        """Проверяет, что лимит токенов берётся из `AnalysisPrompt.max_tokens`.

        Контекст использования:
        - защищает контракт персональной настройки длины ответа для каждого аналитического промта.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - отсутствуют.
        """

        with patch("apps.integrations.services.llm_chat._chat_completion", return_value=("ok", "status")) as mocked_call:
            generate_analysis_reply(dialog=self.dialog, analysis_prompt=self.analysis_prompt, transcript="text")

        mocked_call.assert_called_once()
        self.assertEqual(mocked_call.call_args.kwargs.get("max_tokens"), 1234)
