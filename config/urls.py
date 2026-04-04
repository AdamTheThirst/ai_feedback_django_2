"""Корневой роутер проекта с пользовательскими и системными маршрутами."""

from django.contrib import admin
from django.urls import include, path

from apps.content.views_encyclopedia import EncyclopediaDetailView, EncyclopediaListView
from apps.core.views import CabinetEntryView, HomeView, ScenarioStartView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("dialogs/", include("apps.dialogs.urls", namespace="dialogs")),
    path("", HomeView.as_view(), name="home"),
    path("start/<slug:game_slug>/<slug:scenario_slug>/", ScenarioStartView.as_view(), name="scenario_start"),
    path("encyclopedia/", EncyclopediaListView.as_view(), name="encyclopedia_entry"),
    path("encyclopedia/<slug:slug>/", EncyclopediaDetailView.as_view(), name="encyclopedia_detail"),
    path("cabinet/", CabinetEntryView.as_view(), name="cabinet_entry"),
]
