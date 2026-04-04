"""Тесты энциклопедии: модель статьи, публикация, список с пагинацией и детальная страница."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.content.models import EncyclopediaArticle


class EncyclopediaArticleModelTests(TestCase):
    """Проверяет генерацию slug и базовые ограничения модели статьи."""

    def test_slug_is_generated_and_unique(self) -> None:
        """Проверяет автоматическую генерацию уникального slug при коллизии заголовков."""

        a1 = EncyclopediaArticle.objects.create(title="Тестовая статья", body="Текст", summary="x" * 60)
        a2 = EncyclopediaArticle.objects.create(title="Тестовая статья", body="Текст", summary="y" * 60)

        self.assertTrue(a1.slug)
        self.assertTrue(a2.slug)
        self.assertNotEqual(a1.slug, a2.slug)


class EncyclopediaViewsTests(TestCase):
    """Проверяет публичный список и детальную страницу энциклопедии для авторизованных пользователей."""

    def setUp(self) -> None:
        """Создаёт пользователя и набор статей для тестирования списка/детальной страницы."""

        self.user = User.objects.create_user(email="enc@example.com", password="pass12345", nickname="Enc")

        EncyclopediaArticle.objects.create(
            title="2. Вторая",
            body="Текст",
            summary="Содержательное краткое описание статьи для проверки списка и карточки пользователя.",
            is_published=True,
        )
        EncyclopediaArticle.objects.create(
            title="Альфа",
            body="Текст",
            summary="Краткое описание статьи в деловом стиле для тестирования отображения в списке.",
            is_published=True,
        )
        EncyclopediaArticle.objects.create(
            title="Beta",
            body="Текст",
            summary="Краткое описание статьи с латиницей для проверки порядка сортировки списка.",
            is_published=True,
        )
        EncyclopediaArticle.objects.create(
            title="Черновик",
            body="Текст",
            summary="Черновое описание, которое не должно попадать в пользовательский список статей.",
            is_published=False,
        )

        for idx in range(12):
            EncyclopediaArticle.objects.create(
                title=f"Доп. статья {idx}",
                body="Текст",
                summary="Дополнительная статья для формирования второй страницы пагинации в списке энциклопедии.",
                is_published=True,
            )

    def test_list_requires_auth(self) -> None:
        """Проверяет, что список энциклопедии доступен только авторизованным пользователям."""

        response = self.client.get(reverse("encyclopedia_entry"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_only_published_with_pagination(self) -> None:
        """Проверяет публикационный фильтр и пагинацию по 10 статей."""

        self.client.login(username=self.user.email, password="pass12345")
        response = self.client.get(reverse("encyclopedia_entry"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Черновик")
        self.assertContains(response, "Стр. 1")

        response_page_2 = self.client.get(reverse("encyclopedia_entry"), {"page": 2})
        self.assertEqual(response_page_2.status_code, 200)
        self.assertContains(response_page_2, "Стр. 2")

    def test_detail_shows_only_published_article(self) -> None:
        """Проверяет доступность детальной страницы только для опубликованной статьи."""

        self.client.login(username=self.user.email, password="pass12345")
        published = EncyclopediaArticle.objects.filter(is_published=True).first()
        draft = EncyclopediaArticle.objects.get(title="Черновик")

        ok_response = self.client.get(reverse("encyclopedia_detail", kwargs={"slug": published.slug}))
        draft_response = self.client.get(reverse("encyclopedia_detail", kwargs={"slug": draft.slug}))

        self.assertEqual(ok_response.status_code, 200)
        self.assertEqual(draft_response.status_code, 404)
