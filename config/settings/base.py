"""Базовые настройки Django-проекта для всех окружений."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def load_dotenv_file(dotenv_path: Path) -> None:
    """Загружает переменные окружения из `.env` в `os.environ`.

    Контекст использования:
    - позволяет локальному запуску читать настройки LLM и email прямо из `.env`;
    - выполняется один раз при импорте базового модуля настроек.

    Параметры:
    - `dotenv_path`: путь к файлу `.env`.

    Возвращает:
    - ничего не возвращает.

    Исключения и особые случаи:
    - если файл отсутствует, функция завершается без ошибок;
    - строки без `=` пропускаются.

    Побочные эффекты:
    - добавляет переменные в окружение только если ключ ещё не определён.
    """

    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_dotenv_file(BASE_DIR / ".env")

SECRET_KEY = "dev-only-secret-key-change-me"
DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.accounts",
    "apps.content",
    "apps.dialogs",
    "apps.analysis",
    "apps.platform_config",
    "apps.adminpanel",
    "apps.exports",
    "apps.auditlog",
    "apps.integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# AI-настройки (OpenAI-compatible endpoint)
LLM_BASE_URL = ""
LLM_API_KEY = ""
AI_MODEL_NAME = ""
LLM_TIMEOUT_SECONDS = 60

# Email-настройки для восстановления пароля.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = ""
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "noreply@example.com"


AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "accounts:login"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ai-feedback-cache",
    }
}

# Настройки таймера и завершения диалога V1.
DIALOG_DEFAULT_DURATION_SECONDS = 10 * 60
DIALOG_CLIENT_ABORT_GRACE_SECONDS = 20
