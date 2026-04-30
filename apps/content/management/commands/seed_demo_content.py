"""Команда заполнения демо-контента игр, сценариев и промтов для V1."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, UserRole
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt, SystemPrompt


class Command(BaseCommand):
    """Создаёт или обновляет демо-набор контента для локальной разработки.

    Контекст использования:
    - запускается разработчиком в dev-среде после миграций;
    - гарантирует наличие базовой игры и сценариев из продуктовой спецификации.

    Параметры:
    - команда не принимает пользовательских аргументов в текущей версии.

    Возвращает:
    - текстовый отчёт в stdout о созданных/обновлённых сущностях.

    Исключения и особые случаи:
    - при отсутствии пользователя-суперадмина создаётся технический владелец контента.

    Побочные эффекты:
    - записывает/обновляет данные в таблицах content и accounts.
    """

    help = "Заполняет БД демо-игрой, сценариями и промтами для V1"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Выполняет транзакционное создание seed-контента.

        Контекст использования:
        - вызывается инфраструктурой Django при запуске management-команды.

        Параметры:
        - `*args`: позиционные аргументы CLI (не используются);
        - `**options`: именованные опции команды (не используются).

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - потенциальные ошибки БД откатывают изменения всей транзакции.

        Побочные эффекты:
        - создаёт/обновляет игру, сценарии, игровые и аналитические промты, системный промт.
        """

        owner = self._get_or_create_owner()

        game, _ = Game.objects.update_or_create(
            slug="ya-vyskazyvanie",
            defaults={
                "title": "Я-высказывание",
                "short_description": "Тренировка экологичной обратной связи в рабочих ситуациях.",
                "sort_order": 10,
                "is_published": True,
                "is_archived": False,
                "archived_at": None,
                "created_by": owner,
            },
        )

        scenarios = [
            {
                "slug": "podchinennyy-marina",
                "title": "Подчинённый Марина",
                "sort_order": 10,
                "conditions_text": "Вы руководитель. Обсудите с Мариной срыв дедлайна без перехода на личность.",
                "opening_message_text": "Здравствуйте. Я Марина, готова обсудить задачу.",
                "prompt_title": "Промт: Подчинённый Марина",
            },
            {
                "slug": "kollega-aleksey",
                "title": "Коллега Алексей",
                "sort_order": 20,
                "conditions_text": "Вы коллеги. Нужно дать обратную связь по совместной презентации.",
                "opening_message_text": "Привет! Я Алексей, давай обсудим презентацию.",
                "prompt_title": "Промт: Коллега Алексей",
            },
            {
                "slug": "rukovoditel-aleksey",
                "title": "Руководитель Алексей",
                "sort_order": 30,
                "conditions_text": "Вы сотрудник. Обсудите с руководителем повышенную нагрузку и ожидания.",
                "opening_message_text": "Добрый день, я Алексей. Слушаю вашу обратную связь.",
                "prompt_title": "Промт: Руководитель Алексей",
            },
        ]

        for scenario_data in scenarios:
            scenario, _ = Scenario.objects.update_or_create(
                game=game,
                slug=scenario_data["slug"],
                defaults={
                    "title": scenario_data["title"],
                    "short_description": "Демо-сценарий для V1",
                    "conditions_text": scenario_data["conditions_text"],
                    "opening_message_text": scenario_data["opening_message_text"],
                    "sort_order": scenario_data["sort_order"],
                    "is_published": True,
                    "is_archived": False,
                    "archived_at": None,
                    "created_by": owner,
                },
            )

            ScenarioPrompt.objects.update_or_create(
                scenario=scenario,
                is_active=True,
                defaults={
                    "title": scenario_data["prompt_title"],
                    "prompt_text": (
                        "Ты персонаж Алексей в ролевом диалоге тренажёра обратной связи. "
                        "Отвечай на русском, естественно, кратко и в рамках заданной ситуации."
                    ),
                    "is_archived": False,
                    "archived_at": None,
                    "created_by": owner,
                },
            )

        analysis_prompts = [
            {
                "alias": "focus-on-behavior",
                "title": "Фокус на поведении",
                "header_text": "Фокус на поведении, а не на личности",
                "comment_text": "Оценка того, насколько обратная связь описывает действия, а не личные качества.",
                "sort_order": 10,
            },
            {
                "alias": "clarity-and-specificity",
                "title": "Ясность и конкретика",
                "header_text": "Ясность формулировок",
                "comment_text": "Оценка конкретности запроса и понятности следующего шага.",
                "sort_order": 20,
            },
        ]

        for prompt_data in analysis_prompts:
            AnalysisPrompt.objects.update_or_create(
                game=game,
                alias=prompt_data["alias"],
                defaults={
                    "title": prompt_data["title"],
                    "header_text": prompt_data["header_text"],
                    "comment_text": prompt_data["comment_text"],
                    "prompt_text": (
                        "Проанализируй диалог и верни оценку критерия по шкале 0..5 "
                        "с кратким обоснованием на русском языке."
                    ),
                    "sort_order": prompt_data["sort_order"],
                    "min_rating": 0,
                    "max_rating": 5,
                    "is_active": True,
                    "is_archived": False,
                    "archived_at": None,
                    "created_by": owner,
                },
            )

        SystemPrompt.objects.update_or_create(
            key="analysis_metadata_generator",
            defaults={
                "title": "Генерация метаданных аналитики",
                "prompt_text": "Сгенерируй alias, header_text и comment_text для аналитического критерия.",
                "is_active": True,
                "is_archived": False,
                "archived_at": None,
                "created_by": owner,
            },
        )

        self.stdout.write(self.style.SUCCESS("Демо-контент V1 успешно подготовлен."))

    def _get_or_create_owner(self) -> User:
        """Возвращает владельца демо-контента, создавая его при необходимости.

        Контекст использования:
        - используется seed-командой для заполнения поля `created_by`.

        Параметры:
        - отсутствуют.

        Возвращает:
        - пользователя роли `superadmin`, выступающего техническим владельцем seed-данных.

        Исключения и особые случаи:
        - если подходящий пользователь отсутствует, создаётся новый.

        Побочные эффекты:
        - может создать нового пользователя в БД.
        """

        existing = User.objects.filter(role=UserRole.SUPERADMIN, is_active=True).first()
        if existing:
            return existing
        return User.objects.create_superuser(
            email="superadmin@example.com",
            password="123456",
            nickname="superadmin",
        )
