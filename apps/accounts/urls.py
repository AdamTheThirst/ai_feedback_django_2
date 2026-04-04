"""Маршруты приложения accounts."""

from django.urls import path

from apps.accounts.views import (
    LoginView,
    RegisterView,
    SafePasswordResetCompleteView,
    SafePasswordResetConfirmView,
    SafePasswordResetDoneView,
    SafePasswordResetView,
    logout_view,
    profile_view,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("password-reset/", SafePasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", SafePasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", SafePasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/complete/", SafePasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
