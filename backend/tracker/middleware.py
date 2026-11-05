from urllib.parse import unquote

from django.http import JsonResponse
from django.utils.cache import add_never_cache_headers


class RejectNulMiddleware:
    """URL(パス・クエリ)に NUL 文字(%00)を含むリクエストを 400 にする。

    PostgreSQL は NUL を含む文字列を扱えず、検索語(`?q=`)やコード(`/projects/<code>/`)に入ると
    500 になる。個々のビューで検査せず、入口で 1 回だけ弾く。本文は各シリアライザが検査する。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "\x00" in unquote(request.META.get("QUERY_STRING", "")) or "\x00" in unquote(request.path):
            return JsonResponse({"code": "validation_error", "detail": "NUL 文字(%00)は使えません。"}, status=400)
        return self.get_response(request)


class ApiNoStoreMiddleware:
    """API の応答をキャッシュさせない(`Cache-Control: no-store`)。

    認証済みのデータが、共有キャッシュ(CDN・プロキシ)や共用端末のブラウザに残らないようにする(OWASP API8)。
    Cloudflare を前に置くので、特に明示しておく。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            add_never_cache_headers(response)
            response["Cache-Control"] = "no-store"
        return response
