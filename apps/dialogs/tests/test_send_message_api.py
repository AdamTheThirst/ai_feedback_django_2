"""Тесты JSON-endpoint отправки сообщений в чатовом диалоге."""

import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.content.models import Game, Scenario, ScenarioPrompt
from apps.core.enums import DialogMessageRole
from apps.dialogs.models import DialogMessage, DialogSession
from apps.integrations.services.llm_chat import LLMGameReply


class DialogSendMessageApiTests(TestCase):
    """Проверяет отправку сообщений, idempotency и защиту от дублей.

    Контекст использования:
    - покрывает сценарии JSON-endpoint-а `dialogs:send_message`.

    Параметры:
    - отсутствуют.

    Возвращает:
    - результаты assert-проверок.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - создаёт тестовые записи в изолированной тестовой БД.
    """

    def setUp(self) -> None:
        """Создаёт пользователя и активный диалог с первой репликой ассистента.

        Контекст использования:
        - вызывается перед каждым тестовым методом.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - заполняет тестовую БД пользователем, сценарием, промтом и активной сессией.
        """

        self.user = User.objects.create_user(email="chat@example.com", password="pass12345", nickname="ChatUser")
        self.game = Game.objects.create(slug="chat-game", title="Chat Game", is_published=True)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="chat-scenario",
            title="Chat Scenario",
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

    @patch("apps.dialogs.services.chat.generate_game_reply")
    def test_send_message_returns_user_and_assistant_messages(self, generate_game_reply_mock) -> None:
        """Проверяет успешный JSON-ответ с парой новых сообщений.

        Контекст использования:
        - подтверждает базовый happy-path отправки сообщения.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - добавляет сообщения пользователя и ассистента в диалог.
        """

        generate_game_reply_mock.return_value = LLMGameReply(
            text="Тестовый ответ ассистента через LLM.",
            status_text="LLM подключен: test-model",
        )

        response = self.client.post(
            reverse("dialogs:send_message", kwargs={"public_id": self.dialog.public_id}),
            data={"text": "Привет", "client_message_id": str(uuid.uuid4())},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["user_message"]["role"], "user")
        self.assertEqual(payload["assistant_message"]["role"], "assistant")
        self.assertIn("LLM подключен", payload["llm_status_text"])

    @patch("apps.dialogs.services.chat.generate_game_reply")
    def test_send_message_is_idempotent_by_client_message_id(self, generate_game_reply_mock) -> None:
        """Проверяет защиту от дубля при повторной отправке одинакового client_message_id.

        Контекст использования:
        - подтверждает idempotency-контракт API для повторно доставленных запросов.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - не создаёт повторных пользовательских сообщений при одинаковом client_message_id.
        """

        generate_game_reply_mock.return_value = LLMGameReply(
            text="Тестовый ответ ассистента через LLM.",
            status_text="LLM подключен: test-model",
        )

        client_id = str(uuid.uuid4())
        url = reverse("dialogs:send_message", kwargs={"public_id": self.dialog.public_id})

        first = self.client.post(url, data={"text": "Сообщение", "client_message_id": client_id})
        second = self.client.post(url, data={"text": "Сообщение", "client_message_id": client_id})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(DialogMessage.objects.filter(dialog=self.dialog, role=DialogMessageRole.USER).count(), 1)
