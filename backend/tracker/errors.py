"""エラー形式の統一: 全てのエラーは `{"code": "...", "detail": "..."}`(検証エラーは `errors` も付く)。"""

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    """業務ルール違反。モデル層から投げ、API 層で HTTP ステータスに変換する。"""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "domain_error"

    def __init__(self, detail: str, code: str | None = None):
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code


class InvalidTransition(DomainError):
    """遷移表にない状態変更(409)。"""

    status_code = status.HTTP_409_CONFLICT
    code = "invalid_transition"


class RuleViolation(DomainError):
    """遷移自体は表にあるが、追加条件を満たさない(409)。例: 版が無いまま完了。"""

    status_code = status.HTTP_409_CONFLICT
    code = "rule_violation"


class Forbidden(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


class IdempotencyConflict(DomainError):
    status_code = status.HTTP_409_CONFLICT
    code = "idempotency_conflict"


def _flatten(errors) -> str:
    """検証エラーの先頭 1 件を 'field: message' にして detail に使う。"""
    if isinstance(errors, dict):
        for key, value in errors.items():
            inner = _flatten(value)
            return inner if key in {"non_field_errors", "detail"} else f"{key}: {inner}"
    if isinstance(errors, (list, tuple)):
        return _flatten(errors[0]) if errors else ""
    return str(errors)


def exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response({"code": exc.code, "detail": exc.detail}, status=exc.status_code)
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # 想定外の例外は 500(Sentry に届く)

    if isinstance(exc, exceptions.ValidationError):
        response.data = {
            "code": "validation_error",
            "detail": _flatten(exc.detail),
            "errors": exc.detail,
        }
    elif isinstance(exc, exceptions.APIException):
        response.data = {"code": exc.default_code, "detail": _flatten(exc.detail)}
    return response
