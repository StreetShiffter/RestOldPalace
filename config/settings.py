import os
from datetime import timedelta


from dotenv import load_dotenv

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(override=True)  # ИСПОЛЬЗОВАТЬ ДАННЫЕ ИЗ ПЕРЕМЕННОГО ОКРУЖЕНИЯ ИЗ ФАЙЛА .ENV


# SECURITY WARNING: django app secret!
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = True if os.getenv("DEBUG") == "True" else False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "restic",
    # "rest_framework",
    # "rest_framework_simplejwt",
    "users",
    "django_filters",
    'django_celery_beat',
    "drf_spectacular",
    "django_cleanup.apps.CleanupConfig",
    # "corsheaders",
]

# REST_FRAMEWORK = {
#     "DEFAULT_FILTER_BACKENDS": [
#         "django_filters.rest_framework.DjangoFilterBackend",
#         "rest_framework.filters.SearchFilter",
#         "rest_framework.filters.OrderingFilter",
#     ],
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         "rest_framework_simplejwt.authentication.JWTAuthentication",
#     ],
#     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
# }

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
# }

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "corsheaders.middleware.CorsMiddleware",
]

# CORS_ALLOWED_ORIGINS = [
#     '<http://localhost:8000>',  # Замените на адрес вашего фронтенд-сервера
# ]
#
# CSRF_TRUSTED_ORIGINS = [
#     "https://read-and-write.example.com", #  Замените на адрес вашего фронтенд-сервера
#     # и добавьте адрес бэкенд-сервера
# ]
#
# CORS_ALLOW_ALL_ORIGINS = True # только если DEBUG=True

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "restic.context_processors.unread_feedback",
                "restic.context_processors.new_payment",
                "restic.context_processors.user_notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv(
            "DB_HOST", "localhost"
        ),  # "db" (имя сервиса docker-compose из .env)
        "PORT": os.getenv("DB_PORT"),
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ru"

TIME_ZONE = "Asia/Novosibirsk"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # исходники статики

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",  # ← это ищет static/ в приложениях
]

# Путь в файловой системе, куда collectstatic будет копировать все файлы (как в VOLUMES)
STATIC_ROOT = BASE_DIR / "staticfiles"  # сюда collectstatic будет копировать всё

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"  # Указываем кастомную модель для уинтификации
#
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")  # Настройки почты
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = True if os.getenv("EMAIL_USE_TLS") == "True" else False
EMAIL_USE_SSL = True if os.getenv("EMAIL_USE_SSL") == "True" else False
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
#

# Настройки для тестирования SQLITE, включая CI/CD
# if "test" in sys.argv:
#     ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
#
#     # Дополнительные настройки для тестов
#     PASSWORD_HASHERS = [
#         "django.contrib.auth.hashers.MD5PasswordHasher",  # Быстрее для тестов
#     ]
#
#     # 🗃️ База данных - для тестов стоковая
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": BASE_DIR / "db.sqlite3",
#         }
#     }
#
#     LANGUAGE_CODE = "ru-ru"
#     TIME_ZONE = "UTC"
#     USE_I18N = True
#     USE_TZ = True
#
#     # 📦 Статика
#     STATIC_URL = "/static/"
#     STATICFILES_DIRS = []
#
#     # 📧 Email
#     EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
#
#     # ПРОИЗВОЛЬНЫЙ КЛЮЧ ДЛЯ ТЕСТОВ
#     SECRET_KEY = "ci-test-secret-key-unsafe-but-ok"
#     DEBUG = True
#     ROOT_URLCONF = "config.urls"
#
#     # 🔑 Указываем, что кастомная модель User — основная
#     AUTH_USER_MODEL = "users.User"
#
#     # 🖼️ TEMPLATES — обязательно для админки
#     TEMPLATES = [
#         {
#             "BACKEND": "django.template.backends.django.DjangoTemplates",
#             "DIRS": [],
#             "APP_DIRS": True,
#             "OPTIONS": {
#                 "context_processors": [
#                     "django.template.context_processors.debug",
#                     "django.template.context_processors.request",
#                     "django.contrib.auth.context_processors.auth",
#                     "django.contrib.messages.context_processors.messages",
#                 ],
#             },
#         },
#     ]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "restic": {  # ← имя вашего приложения
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
#
LOGIN_REDIRECT_URL = (
    "users:profile"  # Редирект после логирования(имя приложения и имя в url)
)
LOGOUT_REDIRECT_URL = (
    "restic:index"  # Редирект после выхода(имя приложения и имя в url )
)
LOGIN_URL = "users:register"  # Редирект на страницу регистрации, если вьюшка защищена миксином LoginRequiredMixin
#
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL"),
    }
}


# Настройки Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Используем eventlet на Windows
CELERY_WORKER_POOL = "eventlet"
CELERY_WORKER_POOL_RESTARTS = True

# Опционально: сериализация
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
#
# # Настройки Celery Beat (планировщик)
CELERY_BEAT_SCHEDULE = {
    "cancel-expired-bookings": {
        "task": "restic.tasks.cancel_expired_bookings",
        "schedule": 300.0,  # каждые 5 минут
    },
}
TELEGRAM_URL = "https://api.telegram.org/bot"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
