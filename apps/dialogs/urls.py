"""Маршруты приложения dialogs."""

from django.urls import path

from apps.dialogs.views import DialogChatView, DialogPlaceholderRedirectView, DialogSendMessageApiView

app_name = "dialogs"

urlpatterns = [
    path("<uuid:public_id>/", DialogChatView.as_view(), name="chat"),
    path("<uuid:public_id>/send/", DialogSendMessageApiView.as_view(), name="send_message"),
    path("<uuid:public_id>/placeholder/", DialogPlaceholderRedirectView.as_view(), name="placeholder"),
]
