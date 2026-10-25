"""ProductionTracker の設定。値は環境変数から読む(秘密情報を Git に入れない)。"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not (DEBUG or env_bool("DJANGO_ALLOW_INSECURE_KEY", False)):
        raise RuntimeError("DJANGO_SECRET_KEY が未設定です(開発時は DJANGO_DEBUG=1 を指定)。")
    SECRET_KEY = "insecure-dev-key-do-not-use-in-production"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],web,testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "tracker",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- DB: POSTGRES_HOST があれば PostgreSQL、なければ SQLite(開発・テスト用) ---
if os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "productiontracker"),
            "USER": os.environ.get("POSTGRES_USER", "productiontracker"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- Cookie / CSRF(画面からの API はセッション認証 + CSRF) ---
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_COOKIE_SAMESITE = "Lax"
# Cloudflare Tunnel など TLS を終端するプロキシの背後で https を認識させる
if env_bool("DJANGO_BEHIND_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- DRF ---
# 認証の差し替え口(設計書 Phase 6): 認証クラスは環境変数で入れ替えられる。
# 外部ID基盤(Firebase Auth 等)を足すときは、ここにクラスのパスを追加する。docs/auth.md 参照。
API_AUTHENTICATION_CLASSES = env_list(
    "API_AUTHENTICATION_CLASSES",
    "tracker.auth.SessionAuthentication401,rest_framework.authentication.TokenAuthentication",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": API_AUTHENTICATION_CLASSES,
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "tracker.pagination.StandardPagination",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "tracker.errors.exception_handler",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}

# --- アプリ固有の設定 ---
# 「完了」にするとき、紐づく版が1つ以上あることを条件にする(設計書 3.3。外せる)
REQUIRE_VERSION_FOR_COMPLETION = env_bool("REQUIRE_VERSION_FOR_COMPLETION", True)
# 版が「却下」されたとき、レビュー待ちのタスクを自動で「進行中」へ戻すか(設計書 1.3。既定は動かさない)
RETURN_TASK_ON_VERSION_REJECT = env_bool("RETURN_TASK_ON_VERSION_REJECT", False)
# 取り込み API の API キー(X-API-Key)。カンマ区切りで複数可。空なら取り込みは常に 401。
INGEST_API_KEYS = env_list("INGEST_API_KEYS")
# 例外発生用の検証エンドポイント(Sentry の疎通確認)。通常は無効。
SENTRY_DEBUG_ENDPOINT_ENABLED = env_bool("SENTRY_DEBUG_ENDPOINT_ENABLED", False)

# --- ログ: 構造化(JSON)で標準出力へ。ローテーションは Docker 側 ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging_json.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {"django.server": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}

# --- Sentry(DSN が無ければ何もしない) ---
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk

    from tracker.sentry import scrub_event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development" if DEBUG else "production"),
        release=os.environ.get("SENTRY_RELEASE") or None,
        send_default_pii=False,  # 個人情報(ユーザー名・IP・Cookie 等)を送らない
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),
        sample_rate=float(os.environ.get("SENTRY_SAMPLE_RATE", "1.0")),  # 無料枠対策のサンプリング
        before_send=scrub_event,
    )
