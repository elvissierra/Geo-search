import os.path
import socket
from enum import Enum
from pathlib import Path

import boto3
import environ

from utils import SecretManager


class PossibleEnvironments(Enum):
    CI_UNIT_TESTS = "ci_unit_tests"
    LOCAL_UNIT_TESTS = "local_unit_tests"
    LOCAL_DO_NOT_VALIDATE_TOKEN = "local_do_not_validate_token"
    LOCAL_VALIDATE_TOKEN = "local_validate_token"
    LOCAL_DOCKER = "local_docker"
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


class Environment:
    __base_dir = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(__base_dir, ".env"))
    env = environ.Env(
        # set casting, default value
        DEBUG=(bool, True),
        AWS_LOAD_BALANCER_URL=(str, ""),
        SHOW_TOPICS_MANAGEMENT_API=(bool, True),
    )
    current_environment = PossibleEnvironments(
        env("CURRENT_ENVIRONMENT", default=PossibleEnvironments.LOCAL_UNIT_TESTS.value)
    )

    def __init__(self):
        self.aws_region_name = "us-east-1"
        self.aws_service_name = "es"
        self.project_name = "geo-search-api"
        self.root_urlconf = "geo_search_api.urls"
        self.wsgi_application = "geo_search_api.wsgi.application"
        self.secret_key = "django-insecure-mrq7$!7yt3rrc=e6#*4m)h1c84cov%83tm35j5xt^_ro9(&j2i"
        self.cors_allow_all_origins = True
        self.cors_allow_credentials = True
        self.cors_allow_headers = [
            "x-case",
        ]

        self.aws_opensearch_host = ""

        self.debug = self.current_environment.value != PossibleEnvironments.PROD.value

        self.allowed_hosts = [
            "localhost",
            "0.0.0.0",
            "127.0.0.1",
            self.env("AWS_LOAD_BALANCER_URL"),
        ]

        self.installed_apps = [
            "corsheaders",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "environ",
            "rest_framework",
            "drf_spectacular",
            "geo_search_api",
            "geo_search_api.apps.likes",
            "geo_search_api.apps.comments",
            "geo_search_api.apps.notes",
            "geo_search_api.apps.topics",
            "geo_search_api.apps.ideas",
            "geo_search_api.apps.contributors",
            "geo_search_api.apps.opensearch",
        ]

        self.middleware = [
            "django.middleware.gzip.GZipMiddleware",
            "corsheaders.middleware.CorsMiddleware",
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.auth.middleware.RemoteUserMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "middlewares.cloudwatch_logging_middleware.CloudwatchLoggingMiddleware",
        ]
        self.templates = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
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
        self.auth_password_validators = [
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

        self.language_code = "en-us"
        self.time_zone = "UTC"
        self.use_i18n = True
        self.use_l10n = True
        self.use_tz = True
        self.static_url = "/api/static/"

        self.rest_framework = {
            "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
            "DEFAULT_PARSER_CLASSES": (
                "djangorestframework_camel_case.parser.CamelCaseJSONParser",
            ),
            "DEFAULT_RENDERER_CLASSES": (
                "geo_search_api.api.utils.ConfigurableCamelCaseJSONRenderer",
            ),
        }
        self.logging = {}
        self.databases = {}
        self.auth0_domain = ""
        self.auth0_issuer = ""
        self.auth0_api_audience = ""
        self.auth0_algorithms = ["RS256"]

        self.spectacular_settings = {
            "TITLE": self.project_name,
            "DESCRIPTION": f"Swagger documentation for {self.project_name}.",
            "VERSION": "1.0.0",
            "APPEND_COMPONENTS": {
                "securitySchemes": {
                    "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "Authorization"},
                }
            },
            "SECURITY": [
                {
                    "ApiKeyAuth": [],
                },
                {
                    "Cookie": [],
                },
            ],
        }
        self.show_topics_management_api = self.env("SHOW_TOPICS_MANAGEMENT_API")

        self.likes_object_types = {
            "Note": "geo_search_api.apps.notes.models.Note",
            "Comment": "geo_search_api.apps.comments.models.Comment",
            "Idea": "geo_search_api.apps.ideas.models.Idea",
        }

        self.comments_object_types = {
            "Note": "geo_search_api.apps.notes.models.Note",
            "Idea": "geo_search_api.apps.ideas.models.Idea",
        }

        self.opensearch_max_searching_size = self.env("MAX_SEARCHING_SIZE", default=10000)
        self.opensearch_max_terms_aggregation_size = self.env(
            "MAX_TERMS_AGGREGATION_SIZE", default=20000
        )
        self.opensearch_max_terms_aggregation_clusters = self.env(
            "MAX_TERMS_AGGREGATION_CLUSTERS", default=501
        )
        self.opensearch_max_buckets_aggregation_size = self.env(
            "MAX_TERMS_AGGREGATION_CLUSTERS", default=30000
        )

    @staticmethod
    def create_env():
        """
        Fabric method for environments
        """
        if Environment.current_environment == PossibleEnvironments.LOCAL_UNIT_TESTS:
            return LocalUnitTestsEnvironment()
        if Environment.current_environment == PossibleEnvironments.CI_UNIT_TESTS:
            return CIUnitTestsEnvironment()
        if Environment.current_environment == PossibleEnvironments.LOCAL_DO_NOT_VALIDATE_TOKEN:
            return LocalDoNotValidateTokenEnvironment()
        if Environment.current_environment == PossibleEnvironments.LOCAL_VALIDATE_TOKEN:
            return LocalValidateTokenEnvironment()
        if Environment.current_environment == PossibleEnvironments.LOCAL_DOCKER:
            return LocalDockerEnvironment()
        if Environment.current_environment == PossibleEnvironments.DEV:
            return DevEnvironment()
        if Environment.current_environment == PossibleEnvironments.STAGE:
            return StageEnvironment()
        if Environment.current_environment == PossibleEnvironments.PROD:
            return ProdEnvironment()
        raise Exception("Invalid environment")


class CIEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self.databases = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": self.env("DB_HOST", default="postgres"),
                "PORT": self.env("DB_PORT", default="5432"),
                "NAME": self.env("DB_NAME", default=self.project_name),
                "USER": self.env("DB_USERNAME", default="local_postgresql_user"),
                "PASSWORD": self.env("DB_PASSWORD", default="local_strong_postgresql_password"),
                "OPTIONS": {"sslmode": "disable"},
            }
        }
        self.rest_framework["DEFAULT_AUTHENTICATION_CLASSES"] = [
            "geo_search_api.api.authentication.Auth0TokenAuthentication",
        ]


class Local(Environment):
    def __init__(self):
        super().__init__()


class Docker(Environment):
    def __init__(self):
        super().__init__()
        self.databases = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": self.env("DB_HOST"),
                "PORT": self.env("DB_PORT"),
                "NAME": self.env("DB_NAME"),
                "USER": self.env("DB_USERNAME"),
                "PASSWORD": self.env("DB_PASSWORD"),
                "OPTIONS": {"sslmode": "disable"},
            }
        }
        self.aws_opensearch_host = self.env("AWS_OPENSEARCH_HOST")


class OnCluster(Environment):
    def __init__(self):
        super().__init__()
        SecretManager.aws_region = self.aws_region_name
        self._set_db_data()
        self.allowed_hosts.append(socket.gethostbyname(socket.gethostname()))
        self.rest_framework["DEFAULT_AUTHENTICATION_CLASSES"] = [
            "geo_search_api.api.authentication.Auth0TokenAuthentication",
        ]

    def _set_db_data(self):
        secrets_manager = SecretManager()
        secrets_manager.add_secret(
            "DB_USERNAME",
            SecretManager.DataAboutSecret(self.env("DB_USERNAME")),
        )
        secrets_manager.add_secret(
            "DB_PASSWORD",
            SecretManager.DataAboutSecret(self.env("DB_PASSWORD")),
        )
        self.databases = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": self.env("DB_HOST"),
                "PORT": self.env("DB_PORT"),
                "NAME": self.env("DB_NAME"),
                "USER": secrets_manager.get_secret("DB_USERNAME")["Username"],
                "PASSWORD": secrets_manager.get_secret("DB_PASSWORD")["Password"],
            }
        }


class CIUnitTestsEnvironment(CIEnvironment):
    def __init__(self):
        super().__init__()
        self.show_topics_management_api = True


class LocalUnitTestsEnvironment(Local):
    def __init__(self):
        super().__init__()
        self.rest_framework["DEFAULT_AUTHENTICATION_CLASSES"] = [
            "geo_search_api.api.authentication.Auth0TokenAuthentication",
        ]


class LocalDoNotValidateTokenEnvironment(Local):
    def __init__(self):
        super().__init__()


class LocalValidateTokenEnvironment(Local):
    def __init__(self):
        super().__init__()
        self.rest_framework["DEFAULT_AUTHENTICATION_CLASSES"] = [
            "geo_search_api.api.authentication.Auth0TokenAuthentication",
        ]

        self.auth0_domain = self.env("AUTH0_DOMAIN")
        self.auth0_issuer = self.env("AUTH0_ISSUER")
        self.auth0_api_audience = self.env("AUTH0_API_AUDIENCE")


class LocalDockerEnvironment(Docker):
    def __init__(self):
        super().__init__()
        self.rest_framework["DEFAULT_AUTHENTICATION_CLASSES"] = [
            "geo_search_api.api.authentication.Auth0TokenAuthentication",
        ]
        self.auth0_domain = self.env("AUTH0_DOMAIN")
        self.auth0_issuer = self.env("AUTH0_ISSUER")
        self.auth0_api_audience = self.env("AUTH0_API_AUDIENCE")
        self.show_topics_management_api = True


class OnClusterApplication(OnCluster):
    def __init__(self):
        super().__init__()
        self._set_secret_key()
        self._set_aws_opensearch_host()
        self._set_logging()
        self.auth0_domain = self.env("AUTH0_DOMAIN")
        self.auth0_issuer = self.env("AUTH0_ISSUER")
        self.auth0_api_audience = self.env("AUTH0_API_AUDIENCE")

    def _set_secret_key(self):
        secrets_manager = SecretManager()
        secrets_manager.add_secret(
            "DJANGO_SECRET_KEY",
            SecretManager.DataAboutSecret(self.env("DJANGO_SECRET_KEY")),
        )
        self.secret_key = secrets_manager.get_secret("DJANGO_SECRET_KEY")

    def _set_aws_opensearch_host(self):
        secrets_manager = SecretManager()
        secrets_manager.add_secret(
            "AWS_OPENSEARCH_HOST",
            SecretManager.DataAboutSecret(self.env("AWS_OPENSEARCH_HOST")),
        )
        self.aws_opensearch_host = secrets_manager.get_secret("AWS_OPENSEARCH_HOST")

    def _set_logging(self):
        logger_boto3_client = boto3.client("logs", region_name=self.aws_region_name)
        self.logging = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "watchtower": {
                    "level": self.env("LOG_LEVEL", default="ERROR"),
                    "class": "watchtower.CloudWatchLogHandler",
                    "boto3_client": logger_boto3_client,
                    "log_group": self.env("CLOUDWATCH_LOG_GROUP"),
                    "stream_name": self.env("CLOUDWATCH_STREAM_NAME"),
                },
            },
            "loggers": {
                "watchtower": {
                    "level": self.env("LOG_LEVEL", default="ERROR"),
                    "handlers": ["watchtower"],
                    "propagate": False,
                }
            },
        }


class DevEnvironment(OnClusterApplication):
    def __init__(self):
        super().__init__()


class StageEnvironment(OnClusterApplication):
    def __init__(self):
        super().__init__()


class ProdEnvironment(OnClusterApplication):
    def __init__(self):
        super().__init__()
