"""
Django settings for e_metric_api project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
import ssl
from datetime import timedelta
from pathlib import Path
from socket import gethostbyname
from urllib.parse import urlparse

import environ

from kombu import Queue, Exchange

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(env("DEBUG", default="0")))

ALLOWED_HOSTS = []

# CORS SETUP
CORS_ALLOW_CREDENTIALS = True  # to accept cookies via ajax request
CORS_ORIGIN_WHITELIST = []
BASE_DOMAIN = env("BASE_URL", default="http://127.0.0.1:8000/")
ALLOWED_HOSTS.extend(
    filter(
        None,
        os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1").split(","),
    )
)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = []
CORS_ALLOWED_ORIGIN_REGEXES = []

LOCAL_HOST_PORT = []
LOCAL_HOST_PORT.extend(
    filter(None, os.environ.get("LOCAL_HOST_PORT", "").split(","))
)

for i in ALLOWED_HOSTS:
    if i == "localhost":
        for port in LOCAL_HOST_PORT:
            CORS_ALLOWED_ORIGINS.append(f"http://{i}:{port}")
            CORS_ALLOWED_ORIGINS.append(f"http://127.0.0.1:{port}")
    else:
        CORS_ALLOWED_ORIGINS.append(f"https://{i}")


# Application definition

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

SHARED_APPS = [
    "django_tenants",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "cloudinary_storage",
    "cloudinary",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt.token_blacklist",
    "django_user_agents",
    "django_celery_results",
    "django_celery_beat",
    "django_tenants_celery_beat",
    "silk",
    "import_export",
    "django_cleanup.apps.CleanupConfig",
    # custom models
    "client.apps.ClientConfig",
    "core.apps.CoreConfig",
    "account.apps.AccountConfig",
    "mailing.apps.MailingConfig",
    "tracking.apps.TrackingConfig",


    # "organization.apps.OrganizationConfig",
    # "employee_profile.apps.EmployeeProfileConfig",
    # "employee.apps.EmployeeConfig",
    # "designation.apps.DesignationConfig",
    # "career_path.apps.CareerPathConfig",
    # "strategy_deck.apps.StrategyDeckConfig",
    # "tasks.apps.TasksConfig",
    # "emetric_calendar.apps.EmetricCalendarConfig",
    # "employee_file.apps.EmployeeFileConfig",
    
]
# b006
TENANT_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "corsheaders",
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt.token_blacklist",
    "django_user_agents",
    "django_celery_results",
    "silk",
    # custom Apps
    "account.apps.AccountConfig",
    "core.apps.CoreConfig",
    "mailing.apps.MailingConfig",
    "tracking.apps.TrackingConfig",
    "organization.apps.OrganizationConfig",
    "employee_profile.apps.EmployeeProfileConfig",
    "employee",
    "designation.apps.DesignationConfig",
    "career_path.apps.CareerPathConfig",
    "strategy_deck.apps.StrategyDeckConfig",
    "tasks.apps.TasksConfig",
    # reason why i did not use apps.Config 
    # https://github.com/django-tenants/django-tenants/issues/577 the line that said default_app_config = 'app_name.apps.AppConfig'
    "emetric_calendar",
    "employee_file",
    "leaveManagement",
    'payroll',
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]
ROOT_URLCONF = "e_metric_api.urls_tenants"
PUBLIC_SCHEMA_URLCONF = "e_metric_api.urls_public"
TENANT_MODEL = "client.Client"
TENANT_DOMAIN_MODEL = "client.Domain"
TENANT_SUBFOLDER_PREFIX = "client"
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_MAIL_SENDER", default="emetricsuite@gmail.com"
)
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

DEFAULT_ACTIVATION_DAYS = 7

MANAGERS = (
    ("Admin", "emmaldini12@gmail.com"),
    ("Developer", "emmaldini12@gmail.com"),
)

ADMINS = MANAGERS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "core.utils.CustomTenantSubFolderMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]
MIDDLEWARE.insert(2, "silk.middleware.SilkyMiddleware") if DEBUG else None


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "e_metric_api.wsgi.application"

AUTH_USER_MODEL = "account.User"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASE_URL = env("DATABASE_URL", default=None)

if not DATABASE_URL:
    DATABASES = {
        "default": {
            "ENGINE": "django_tenants.postgresql_backend",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASS"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    db_info = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django_tenants.postgresql_backend",
            "NAME": db_info.path[1:],
            "USER": db_info.username,
            "PASSWORD": db_info.password,
            "HOST": db_info.hostname,
            "PORT": db_info.port,
            "OPTIONS": {"sslmode": "require"},
            "CONN_MAX_AGE": 60,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Auth Token eg [Bearer (JWT Token)]": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    }
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "EXCEPTION_HANDLER": "core.utils.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
}

# JWT config
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=8),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = Path(BASE_DIR).joinpath("staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "static", "media")

STATICFILES_DIRS = (Path(BASE_DIR).joinpath("static"),)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# sending blue
SENDINBLUE_API_KEY = env("SENDINBLUE_API_KEY")

# Redis
# setup -> https://digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04
REDIS_PORT = int(env("REDIS_PORT", default=6379))
REDIS_DB = 0
# REDIS_HOST = env('REDIS_PORT_6379_TCP_ADDR', default='127.0.0.1')
REDIS_HOST = env("REDIS_HOST", default="127.0.0.1")
REDIS_MAX_CONNECTIONS = 5

USE_REDIS_SSL = os.getenv("REDIS_TLS_URL", default=False)
REDIS_URL_SSL = None
REDIS_URL_SSL_WITH_DB = None
HEROKU_REDIS_SSL_HOST = None
REDIS_URL_SSL_WITH_DB_AND_QUERY = None

if USE_REDIS_SSL is not False:
    REDIS_TLS = True
    REDIS_VERIFY_SSL = False
    REDIS_URL_SSL = env("REDIS_TLS_URL")
    REDIS_URL_SSL_WITH_DB = f"{os.getenv('REDIS_TLS_URL')}/{REDIS_DB}"
    REDIS_URL_SSL_WITH_DB_AND_QUERY = (
        f"{os.getenv('REDIS_TLS_URL')}/{REDIS_DB}?ssl_cert_reqs=CERT_NONE"
    )

    ssl_context = ssl.SSLContext()
    ssl_context.check_hostname = False

    HEROKU_REDIS_SSL_HOST = {
        "address": REDIS_URL_SSL_WITH_DB,  # The 'rediss' schema denotes a SSL connection.
        "ssl": ssl_context,
    }

# CACHE
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env(
            "REDIS_URL",
            default="redis://%s:%d/%d"
            % (REDIS_HOST, int(REDIS_PORT), REDIS_DB),
        ),  # env('REDIS_URL'),,
        "TIMEOUT": 60 * 60 * 2,
        "KEY_FUNCTION": "django_tenants.cache.make_key",
        "REVERSE_KEY_FUNCTION": "django_tenants.cache.reverse_key",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # "CONNECTION_POOL_KWARGS": {
            #     "ssl_cert_reqs": None
            # },
        },
    }
}

CELERY_TASK_TENANT_CACHE_SECONDS = 60 * 60 * 24

USER_AGENTS_CACHE = "default"

BROKER_POOL_LIMIT = 1
BROKER_CONNECTION_TIMEOUT = 10

# Celery Configuration Options
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
# configure queues, currently we have only one
CELERY_DEFAULT_QUEUE = "default"
CELERY_QUEUES = (Queue("default", Exchange("default"), routing_key="default"),)
CELERY_ALWAYS_EAGER = False
CELERY_ACKS_LATE = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_DISABLE_RATE_LIMITS = False

CELERY_IGNORE_RESULT = True
CELERY_SEND_TASK_ERROR_EMAILS = False
CELERY_TASK_RESULT_EXPIRES = 600

# Set redis as celery result backend
CELERY_RESULT_BACKEND = (
    env(
        "REDIS_URL",
        default="redis://%s:%d/%d" % (REDIS_HOST, int(REDIS_PORT), REDIS_DB),
    )
    if USE_REDIS_SSL is False
    else REDIS_URL_SSL_WITH_DB_AND_QUERY
)
CELERY_REDIS_MAX_CONNECTIONS = 1

# Don't use pickle as serializer, json is much safer
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = CELERY_RESULT_BACKEND
PERIODIC_TASK_TENANT_LINK_MODEL = "client.PeriodicTaskTenantLink"
# ADMINS
ADMIN_EMAIL = env("ADMIN_EMAIL", default="admin@mail.com")
ADMIN_FIRST_NAME = env("ADMIN_FIRST_NAME", default="demo_first_name")
ADMIN_LAST_NAME = env("ADMIN_LAST_NAME", default="demo_last_name")
ADMIN_PHONE_NUMBER = env("ADMIN_PHONE_NUMBER", default="+2348065652234")
ADMIN_PASS = env("ADMIN_PASS", default="secure_pass")


# cloudinary settings

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"


# Silk profiling setting
SILKY_PYTHON_PROFILER = os.getenv("ENABLE_PROFILING", "False") == "True"
SILKY_PYTHON_PROFILER_BINARY = SILKY_PYTHON_PROFILER
SILKY_PYTHON_PROFILER_RESULT_PATH = "/profiled/"
SILKY_META = SILKY_PYTHON_PROFILER
SILKY_INTERCEPT_FUNC = lambda r: DEBUG