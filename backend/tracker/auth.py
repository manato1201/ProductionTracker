import secrets

from django.conf import settings
from rest_framework import authentication, exceptions


class SessionAuthentication401(authentication.SessionAuthentication):
    """セッション認証 + CSRF(DRF 標準)。未認証を 403 ではなく 401 で返す。"""

    def authenticate_header(self, request):
        return 'Session realm="api"'


class IngestPrincipal:
    """取り込み API を呼んだ外部ツール。ユーザーではない。"""

    is_authenticated = True
    is_staff = False
    is_superuser = False
    pk = None

    def __str__(self):
        return "ingest-client"


class IngestApiKeyAuthentication(authentication.BaseAuthentication):
    """`X-API-Key` による認証。取り込み API 専用で、画面の操作には使えない。"""

    header = "HTTP_X_API_KEY"

    def authenticate_header(self, request):
        return "X-API-Key"

    def authenticate(self, request):
        supplied = request.META.get(self.header, "")
        if not supplied:
            raise exceptions.NotAuthenticated("X-API-Key ヘッダが必要です。")
        # 鍵が未設定なら常に拒否(fail closed)。比較は定数時間で行う。
        for key in settings.INGEST_API_KEYS:
            if secrets.compare_digest(supplied.encode(), key.encode()):
                return IngestPrincipal(), supplied
        raise exceptions.AuthenticationFailed("API キーが正しくありません。")
