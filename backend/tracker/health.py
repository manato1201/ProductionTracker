import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


@never_cache
@require_GET
def healthz(request):
    """死活監視(認証なし)。DB 接続の可否のみ返し、例外の中身は返さない。"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("healthz: database check failed")
        return JsonResponse({"status": "error", "db": False}, status=503)
    return JsonResponse({"status": "ok", "db": True})


class SentryDebugView(APIView):
    """Sentry の疎通確認用。管理者のみ・環境変数で有効にしたときだけ例外を起こす。"""

    def get(self, request):
        if not (settings.SENTRY_DEBUG_ENDPOINT_ENABLED and request.user.is_staff):
            raise NotFound()
        raise RuntimeError("Sentry 疎通確認のための意図的な例外(Django)")
