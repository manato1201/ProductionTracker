"""OWASP API Security Top 10(2023)の点検を、自動テストにしたもの(docs/security.md)。

- API2/API5: 全てのエンドポイントは、未認証だと 401(公開するものは許可リストで明示する)
- API1/API5: ロール別の認可の一覧(見えない = 404/400、権限なし = 403)
- API3: 読み取り専用の項目は、書き込めない
- API4: 資源の消費を抑える(ページ・サイズの上限、レート制限)
- API8: 応答をキャッシュさせない
- API9: 新しいエンドポイントを足したら、このテストが認証の扱いを決めさせる
"""

import json

import pytest
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient

from config.urls import api_patterns, router

from .factories import (
    EntityFactory,
    MemberFactory,
    ProjectFactory,
    StepFactory,
    TaskFactory,
    UserFactory,
    VersionFactory,
)

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# API2 / API5 / API9: 全てのエンドポイントは、未認証だと 401
# ---------------------------------------------------------------------------
def all_api_urls():
    """ルーターと手書きの URL から、全ての API の URL(例の ID 付き)を洗い出す。新しい URL は自動で対象になる。"""
    urls = []
    for prefix, viewset, _basename in router.registry:
        urls.append(f"{BASE}/{prefix}/")
        urls.append(f"{BASE}/{prefix}/1/")
        for action in viewset.get_extra_actions():
            urls.append(f"{BASE}/{prefix}/1/{action.url_path}/")
    for pattern in api_patterns:
        route = str(pattern.pattern)
        if route and "<" not in route and not hasattr(pattern, "url_patterns"):
            urls.append(f"{BASE}/{route}")
    return sorted(u for u in set(urls) if _exists(u))


def _exists(url):
    """実在するルートだけを対象にする(ノートに詳細ルートは無い、など)。"""
    try:
        resolve(url)
    except Resolver404:
        return False
    return True


# 認証なしで使えるもの(理由つき)。ここに足すときは、レビューで理由を説明できること。
PUBLIC = {
    f"{BASE}/auth/csrf/": "ログイン前に CSRF クッキーを受け取る",
    f"{BASE}/auth/login/": "ログイン(CSRF とレート制限で守る)",
    f"{BASE}/healthz": "死活監視。DB の可否だけを返す",
    f"{BASE}/ingest/quality/": "認証は X-API-Key(セッションではない)。キーなしは 401",
    f"{BASE}/ingest/visual/": "同上",
}


@pytest.mark.parametrize("url", all_api_urls())
@pytest.mark.parametrize("method", ["get", "post", "patch", "put", "delete"])
def test_every_api_endpoint_requires_authentication(db, url, method):
    res = getattr(APIClient(), method)(url)
    if url in PUBLIC:
        assert res.status_code in (200, 400, 401, 405), f"{method.upper()} {url}: {res.status_code}"
        if url.endswith(("/ingest/quality/", "/ingest/visual/")) and method == "post":
            assert res.status_code == 401
    else:
        assert res.status_code == 401, f"{method.upper()} {url} は未認証で {res.status_code} を返した(401 のはず)"


def test_public_list_is_not_stale():
    """許可リストに、もう無い URL が残っていない。"""
    assert set(PUBLIC) <= set(all_api_urls())


# ---------------------------------------------------------------------------
# API1 / API5: ロール別の認可の一覧
# ---------------------------------------------------------------------------
ROLES = ["outsider", "viewer", "artist", "reviewer", "staff"]


@pytest.fixture
def world(db):
    """1 つのプロジェクトと、役割ごとのクライアント。"""
    project = ProjectFactory(code="AUTHZ")
    users = {
        "outsider": UserFactory(),
        "viewer": UserFactory(),
        "artist": UserFactory(),
        "reviewer": UserFactory(),
        "staff": UserFactory(is_staff=True),
    }
    for role in ("viewer", "artist", "reviewer"):
        MemberFactory(project=project, user=users[role], role=role)
    clients = {}
    for role, user in users.items():
        c = APIClient()
        c.force_authenticate(user)
        clients[role] = c
    entity = EntityFactory(project=project, name="crate")
    step = StepFactory()
    return {"project": project, "entity": entity, "step": step, "clients": clients, "users": users}


def req(world, role, method, path, body=None):
    return getattr(world["clients"][role], method)(f"{BASE}/{path}", body, format="json")


# (操作の名前, 各ロールの期待するステータス)。見えないもの = 404 / 400(存在しない扱い)、権限なし = 403。
# 状態を変える操作は 1 回ごとに世界を作り直す(parametrize ごとに fixture が新しくなる)。
CASES = {
    "プロジェクトを見る": ("get", lambda w: f"projects/{w['project'].id}/", None, dict(outsider=404, viewer=200, artist=200, reviewer=200, staff=200)),
    "プロジェクトを更新": ("patch", lambda w: f"projects/{w['project'].id}/", {"name": "x"}, dict(outsider=404, viewer=403, artist=403, reviewer=200, staff=200)),
    "メンバー一覧": ("get", lambda w: f"projects/{w['project'].id}/members/", None, dict(outsider=404, viewer=200, artist=200, reviewer=200, staff=200)),
    "アセット一覧": ("get", lambda w: "entities/?project=AUTHZ", None, dict(outsider=200, viewer=200, artist=200, reviewer=200, staff=200)),
    "アセットを作る": ("post", lambda w: "entities/", lambda w: {"project": w["project"].id, "name": "n"}, dict(outsider=400, viewer=403, artist=201, reviewer=201, staff=201)),
    "アセットを更新": ("patch", lambda w: f"entities/{w['entity'].id}/", {"name": "y"}, dict(outsider=404, viewer=403, artist=200, reviewer=200, staff=200)),
    "タスクを作る": ("post", lambda w: "tasks/", lambda w: {"entity": w["entity"].id, "step": w["step"].id}, dict(outsider=400, viewer=403, artist=201, reviewer=201, staff=201)),
    "ノートを書く": ("post", lambda w: "notes/", lambda w: {"target_type": "entity", "target_id": w["entity"].id, "body": "b"}, dict(outsider=400, viewer=403, artist=201, reviewer=201, staff=201)),
    "ノートを読む": ("get", lambda w: f"notes/?target_type=entity&target_id={w['entity'].id}", None, dict(outsider=404, viewer=200, artist=200, reviewer=200, staff=200)),
    "版を登録": ("post", lambda w: "versions/", lambda w: {"task": w["task"].id, "file_ref": "f"}, dict(outsider=400, viewer=403, artist=201, reviewer=201, staff=201)),
}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("name", list(CASES))
def test_authorization_matrix(world, name, role):
    method, path, body, expected = CASES[name]
    world["task"] = TaskFactory(entity=world["entity"], step=StepFactory())
    body = body(world) if callable(body) else body
    res = req(world, role, method, path(world), body)
    assert res.status_code == expected[role], f"{name} / {role}: {res.status_code} {res.content[:120]!r}"


TRANSITIONS = {
    # (開始時のタスクの状態, 行き先) → 各ロールの期待
    "着手(未着手 → 進行中)": ("todo", "in_progress", dict(outsider=404, viewer=403, artist=200, reviewer=200, staff=200)),
    "提出(進行中 → レビュー待ち)": ("in_progress", "review", dict(outsider=404, viewer=403, artist=200, reviewer=200, staff=200)),
    "差し戻し(レビュー待ち → 進行中)": ("review", "in_progress", dict(outsider=404, viewer=403, artist=200, reviewer=200, staff=200)),
    "承認(レビュー待ち → 完了)": ("review", "done", dict(outsider=404, viewer=403, artist=403, reviewer=200, staff=403)),
    "不正(未着手 → 完了)": ("todo", "done", dict(outsider=404, viewer=409, artist=409, reviewer=409, staff=409)),
}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("name", list(TRANSITIONS))
def test_task_transition_matrix(world, name, role):
    start, to, expected = TRANSITIONS[name]
    task = TaskFactory(entity=world["entity"], step=StepFactory(), status=start)
    VersionFactory.create(task)  # 「完了」の条件を満たしておく(権限の違いだけを見る)
    res = req(world, role, "post", f"tasks/{task.id}/transition/", {"to": to})
    if name.startswith("不正"):
        # 表にない遷移は、権限より先に 409。見えない人だけは 404(存在を明かさない)
        assert res.status_code == (404 if role == "outsider" else 409)
    else:
        assert res.status_code == expected[role], f"{name} / {role}: {res.status_code}"


@pytest.mark.parametrize("role", ROLES)
def test_version_approval_matrix(world, role):
    task = TaskFactory(entity=world["entity"], step=StepFactory())
    version = VersionFactory.create(task, status="submitted")
    expected = dict(outsider=404, viewer=403, artist=403, reviewer=200, staff=403)
    res = req(world, role, "post", f"versions/{version.id}/transition/", {"to": "approved"})
    assert res.status_code == expected[role]


def test_objects_of_another_project_are_invisible(world):
    """API1(BOLA): 別のプロジェクトのメンバーは、ID を知っていても読めず・書けない。"""
    other = ProjectFactory(code="OTHER")
    intruder = UserFactory()
    MemberFactory(project=other, user=intruder, role="reviewer")  # 自分のプロジェクトではレビュアー
    c = APIClient()
    c.force_authenticate(intruder)
    task = TaskFactory(entity=world["entity"], step=StepFactory())
    version = VersionFactory.create(task)
    for path in (f"entities/{world['entity'].id}/", f"tasks/{task.id}/", f"versions/{version.id}/", f"projects/{world['project'].id}/"):
        assert c.get(f"{BASE}/{path}").status_code == 404, path
    assert c.patch(f"{BASE}/tasks/{task.id}/", {"priority": "high"}, format="json").status_code == 404
    assert c.post(f"{BASE}/tasks/{task.id}/transition/", {"to": "in_progress"}, format="json").status_code == 404
    assert c.post(f"{BASE}/versions/{version.id}/transition/", {"to": "approved"}, format="json").status_code == 404
    # 一覧にも出ない(絞り込みを他人の ID にしても)
    assert c.get(f"{BASE}/tasks/?entity={world['entity'].id}").json()["count"] == 0
    assert c.get(f"{BASE}/versions/?task={task.id}").json()["count"] == 0
    # 自分のプロジェクトに、他人のアセットを指定してタスクを作らせられない
    res = c.post(f"{BASE}/tasks/", {"entity": world["entity"].id, "step": world["step"].id}, format="json")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# API3: 読み取り専用の項目を書き換えられない(マスアサインメント)
# ---------------------------------------------------------------------------
def test_read_only_fields_cannot_be_written(world):
    c = world["clients"]["reviewer"]
    task = TaskFactory(entity=world["entity"], step=StepFactory())
    before = c.get(f"{BASE}/tasks/{task.id}/").json()
    res = c.patch(
        f"{BASE}/tasks/{task.id}/",
        {"status": "done", "id": 999999, "created_at": "2000-01-01T00:00:00Z", "version_count": 99, "is_overdue": True, "next_statuses": []},
        format="json",
    )
    assert res.status_code == 200
    after = res.json()
    for field in ("status", "id", "created_at", "version_count", "is_overdue", "next_statuses"):
        assert after[field] == before[field], field

    project = c.patch(f"{BASE}/projects/{world['project'].id}/", {"id": 999999, "created_at": "2000-01-01T00:00:00Z", "my_role": "viewer", "can_review": False}, format="json")
    assert project.status_code == 200 and project.json()["id"] == world["project"].id and project.json()["can_review"] is True

    created = c.post(f"{BASE}/versions/", {"task": task.id, "file_ref": "f", "number": 77, "created_by": world["users"]["outsider"].id, "id": 5, "status": "draft"}, format="json").json()
    assert created["number"] == 1 and created["created_by"] == world["users"]["reviewer"].id and created["id"] != 5


def test_responses_do_not_leak_sensitive_fields(world):
    """API3: 他のユーザーの情報は、必要な項目だけ(パスワード・メール・トークンを返さない)。"""
    members = world["clients"]["viewer"].get(f"{BASE}/projects/AUTHZ/members/").json()["results"]
    for m in members:
        assert set(m) == {"user", "username", "display_name", "role", "role_label"}
    me = world["clients"]["viewer"].get(f"{BASE}/me/").json()
    assert set(me) == {"id", "username", "display_name", "is_staff"}


# ---------------------------------------------------------------------------
# API4: 資源の消費
# ---------------------------------------------------------------------------
def test_page_size_is_capped(world):
    for i in range(205):
        EntityFactory(project=world["project"], name=f"e{i:03d}")
    res = world["clients"]["artist"].get(f"{BASE}/entities/?project=AUTHZ&page_size=100000").json()
    assert len(res["results"]) == 200 and res["count"] == 206


def test_large_free_text_is_rejected(world):
    task = TaskFactory(entity=world["entity"], step=StepFactory())
    c = world["clients"]["artist"]
    assert c.post(f"{BASE}/versions/", {"task": task.id, "file_ref": "f", "comment": "x" * 5001}, format="json").status_code == 400
    big = {"k": "x" * 30000}
    assert c.post(f"{BASE}/versions/", {"task": task.id, "file_ref": "f", "dcc": big}, format="json").status_code == 400
    assert c.post(f"{BASE}/notes/", {"target_type": "task", "target_id": task.id, "body": "x" * 5001}, format="json").status_code == 400


def test_api_rate_limit(world, monkeypatch):
    """ユーザーごとのレート制限(既定は 1200 回/分。テスト設定では緩めてあるので絞る)。"""
    from django.core.cache import cache
    from rest_framework.throttling import UserRateThrottle

    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, "user", "3/min")
    cache.clear()
    codes = [world["clients"]["artist"].get(f"{BASE}/me/").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    # 別のユーザーには影響しない
    assert world["clients"]["viewer"].get(f"{BASE}/me/").status_code == 200
    cache.clear()


def test_ingest_rate_limit(world, project, monkeypatch):
    from django.core.cache import cache
    from rest_framework.throttling import ScopedRateThrottle

    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "ingest", "2/min")
    cache.clear()
    body = {"project": "DEMO", "scan_run_id": 1, "scanned_at": "2026-10-11T09:00:00+09:00", "results": []}
    codes = [APIClient().post(f"{BASE}/ingest/quality/", body, format="json", HTTP_X_API_KEY="test-ingest-key").status_code for _ in range(4)]
    assert all(c in (200, 201) for c in codes[:2]) and codes[2:] == [429, 429]
    cache.clear()


# ---------------------------------------------------------------------------
# API8: 設定
# ---------------------------------------------------------------------------
def test_api_responses_are_not_cacheable(world):
    """認証済みのデータを、共有キャッシュ(CDN・プロキシ)に残させない。"""
    res = world["clients"]["artist"].get(f"{BASE}/projects/")
    assert "no-store" in res["Cache-Control"]
    assert "no-store" in APIClient().get(f"{BASE}/healthz")["Cache-Control"]


def test_error_responses_do_not_leak_internals(world):
    for res in (APIClient().get(f"{BASE}/projects/"), world["clients"]["artist"].get(f"{BASE}/projects/nope/")):
        body = json.dumps(res.json())
        for secret in ("Traceback", "django.", "File \"", "SECRET_KEY", "/home/"):
            assert secret not in body


# ---------------------------------------------------------------------------
# SQL の指針: 一覧は必ず並び順が決まっている(LIMIT / ページ送りには ORDER BY)
# ---------------------------------------------------------------------------
def test_every_list_queryset_is_ordered(world):
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory

    entity = world["entity"]
    queries = {"notes": f"?target_type=entity&target_id={entity.id}"}
    for prefix, viewset, _ in router.registry:
        if not hasattr(viewset, "list"):
            continue
        request = Request(APIRequestFactory().get(f"/{prefix}/{queries.get(prefix, '')}"))
        request.user = world["users"]["reviewer"]
        view = viewset()
        view.action, view.request, view.kwargs, view.format_kwarg = "list", request, {}, None
        assert view.get_queryset().ordered, f"{prefix} の一覧に ORDER BY が無い(ページ送りで順序がぶれる)"
