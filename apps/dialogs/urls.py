"""Маршруты приложения dialogs."""

from django.urls import path

from apps.analysis.views import DialogResultsView
from apps.dialogs.views import (
    DialogChatView,
    DialogFinishApiView,
    DialogPageLeaveApiView,
    DialogPlaceholderRedirectView,
    DialogSendMessageApiView,
)

app_name = "dialogs"

urlpatterns = [
    path("<uuid:public_id>/", DialogChatView.as_view(), name="chat"),
    path("<uuid:public_id>/send/", DialogSendMessageApiView.as_view(), name="send_message"),
    path("<uuid:public_id>/finish/", DialogFinishApiView.as_view(), name="finish"),
    path("<uuid:public_id>/page-leave/", DialogPageLeaveApiView.as_view(), name="page_leave"),
    path("<uuid:public_id>/results/", DialogResultsView.as_view(), name="results"),
    path("<uuid:public_id>/placeholder/", DialogPlaceholderRedirectView.as_view(), name="placeholder"),
]
