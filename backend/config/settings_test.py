"""pytest 用の設定。既定は SQLite。POSTGRES_HOST を渡せば PostgreSQL でも同じテストが走る。"""

import os

os.environ.setdefault("DJANGO_ALLOW_INSECURE_KEY", "1")

from .settings import *  # noqa: E402,F401,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
ALLOWED_HOSTS = [*ALLOWED_HOSTS, "testserver"]  # noqa: F405
INGEST_API_KEYS = ["test-ingest-key"]
SENTRY_DSN = ""
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"login": "1000/min"}}  # noqa: F405
LOGGING_CONFIG = None  # テスト出力にログを混ぜない
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405 静的ファイルはテストで使わない
