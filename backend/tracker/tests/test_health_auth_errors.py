import json

import pytest
from django.db.utils import OperationalError
from rest_framework.test import APIClient

from tracker.sentry import scrub_event

from .factories import UserFactory


def test_healthz_ok_without_auth(db):
    res = APIClient().get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "db": True}
    assert APIClient().get("/api/v1/healthz").status_code == 200


def test_healthz_reports_db_down_as_503(db, monkeypatch):
    """DB を止めたときに異常を返す(検証チェックリスト)。例外の中身は返さない。"""

    class DeadConnection:
        def cursor(self):
            raise OperationalError("connection refused: host=secret-host password=hunter2")

    monkeypatch.setattr("tracker.health.connection", DeadConnection())
    res = APIClient().get("/healthz")
    assert res.status_code == 503
    assert res.json() == {"status": "error", "db": False}
    assert "hunter2" not in res.content.decode()


def test_healthz_only_get(db):
    assert APIClient().post("/healthz").status_code == 405


# --- ログイン(セッション認証 + CSRF) ---
def test_login_flow_with_csrf(db):
    UserFactory(username="alice")
    c = APIClient(enforce_csrf_checks=True)
    # CSRF トークン無しのログインは拒否(ログイン CSRF 対策)
    assert c.post("/api/v1/auth/login/", {"username": "alice", "password": "pass-12345"}, format="json").status_code == 403
    token = c.get("/api/v1/auth/csrf/").json()["csrf"]
    bad = c.post("/api/v1/auth/login/", {"username": "alice", "password": "nope"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert bad.status_code == 401 and bad.json()["code"] == "authentication_failed"
    ok = c.post("/api/v1/auth/login/", {"username": "alice", "password": "pass-12345"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert ok.status_code == 200 and ok.json()["username"] == "alice"
    assert c.get("/api/v1/me/").json()["username"] == "alice"

    token = c.cookies["csrftoken"].value
    # ログイン後の変更系 API も CSRF が必要
    assert c.post("/api/v1/auth/logout/").status_code == 403
    assert c.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code == 204
    assert c.get("/api/v1/me/").status_code == 401


def test_ui_post_requires_csrf_when_session_authenticated(db, project, artist):
    c = APIClient(enforce_csrf_checks=True)
    c.force_login(artist)
    res = c.post("/api/v1/entities/", {"project": project.id, "name": "x"}, format="json")
    assert res.status_code == 403 and res.json()["code"] == "permission_denied"


# --- Sentry ---
def test_scrub_event_removes_secrets():
    event = {
        "request": {
            "headers": {"Authorization": "Token abc", "X-API-Key": "k", "Cookie": "sessionid=1", "Accept": "*/*"},
            "cookies": {"sessionid": "1"},
            "data": {"body": "secret note"},
        },
        "message": "boom",
    }
    out = json.dumps(scrub_event(event))
    for secret in ("Token abc", "sessionid=1", "secret note"):
        assert secret not in out
    assert '"X-API-Key": "[Filtered]"' in out and '"Accept": "*/*"' in out


def test_sentry_debug_endpoint_disabled_by_default(db, client_for=None):
    admin = UserFactory(is_staff=True)
    c = APIClient()
    c.force_authenticate(admin)
    assert c.get("/api/v1/_debug/sentry/").status_code == 404


def test_sentry_debug_endpoint_raises_when_enabled(db, settings):
    settings.SENTRY_DEBUG_ENDPOINT_ENABLED = True
    admin, user = UserFactory(is_staff=True), UserFactory()
    c = APIClient(raise_request_exception=True)
    c.force_authenticate(user)
    assert c.get("/api/v1/_debug/sentry/").status_code == 404  # 管理者以外は不可
    c.force_authenticate(admin)
    with pytest.raises(RuntimeError):
        c.get("/api/v1/_debug/sentry/")


def test_unexpected_error_returns_json_500_for_api(db, settings):
    """想定外の例外でも、API は統一形式の JSON で 500 を返す(詳細は返さない)。"""
    settings.SENTRY_DEBUG_ENDPOINT_ENABLED = True
    admin = UserFactory(is_staff=True)
    c = APIClient(raise_request_exception=False)
    c.force_authenticate(admin)
    res = c.get("/api/v1/_debug/sentry/")
    assert res.status_code == 500
    assert res.json() == {"code": "server_error", "detail": "サーバーでエラーが発生しました。"}
