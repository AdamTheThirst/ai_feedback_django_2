"""Корневой роутер проекта с базовыми маршрутами первой итерации."""

from django.contrib import admin
from django.urls import include, path
from apps.core.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("", HomeView.as_view(), name="home"),
]
