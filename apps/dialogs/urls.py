"""Маршруты приложения dialogs."""

from django.urls import path

from apps.dialogs.views import DialogPlaceholderView

app_name = "dialogs"

urlpatterns = [
    path("<uuid:public_id>/", DialogPlaceholderView.as_view(), name="placeholder"),
]
