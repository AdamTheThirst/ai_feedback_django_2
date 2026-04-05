"""Локальные настройки разработки для запуска проекта на машине разработчика."""

import os

from .base import *  # noqa: F403


DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", SECRET_KEY)  # noqa: F405
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("AI_BASE_URL", LLM_BASE_URL))  # noqa: F405
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("AI_API_KEY", LLM_API_KEY))  # noqa: F405
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", os.getenv("LLM_MODEL_NAME", os.getenv("AI_MODEL", AI_MODEL_NAME)))  # noqa: F405
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", os.getenv("AI_TIMEOUT_SECONDS", str(LLM_TIMEOUT_SECONDS))))  # noqa: F405

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", EMAIL_BACKEND)  # noqa: F405
EMAIL_HOST = os.getenv("EMAIL_HOST", EMAIL_HOST)  # noqa: F405
EMAIL_PORT = int(os.getenv("EMAIL_PORT", str(EMAIL_PORT)))  # noqa: F405
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", EMAIL_HOST_USER)  # noqa: F405
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", EMAIL_HOST_PASSWORD)  # noqa: F405
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", DEFAULT_FROM_EMAIL)  # noqa: F405
