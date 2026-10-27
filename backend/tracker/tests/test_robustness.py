"""変な入力で 500 を出さない(どの入力でも 4xx で拒否するか、正常に扱う)。

PostgreSQL は NUL 文字や範囲外の整数を例外にする(SQLite は黙って通す)ので、
`POSTGRES_HOST=... pytest` で PostgreSQL でも流すこと。
"""

import json

import pytest
from rest_framework.test import APIClient

from .factories import VersionFactory

BASE = "/api/v1"
KEY = {"HTTP_X_API_KEY": "test-ingest-key"}
HUGE = "9" * 30
NUL = "\x00"


def ok_or_client_error(res):
    assert res.status_code < 500, f"{res.status_code}: {res.content[:200]!r}"


# --- GET: クエリパラメータ ---
LIST_PATHS = ["projects", "entities", "tasks", "versions", "steps", "quality-reports", "visual-results"]
BAD_QUERIES = [
    "page=abc", "page=0", "page=-1", f"page={HUGE}", "page_size=abc", "page_size=-5", "page_size=0", f"page_size={HUGE}",
    "ordering=", "ordering=%00", "ordering=-", "q=%00", "q=%25", "q=" + "x" * 20000,
    f"project={HUGE}", f"entity={HUGE}", f"assignee={HUGE}", f"task={HUGE}", f"version={HUGE}",
    "project=%00", "status=%00", "assignee=me,me", "overdue=maybe",
]


@pytest.mark.parametrize("path", LIST_PATHS)
@pytest.mark.parametrize("query", BAD_QUERIES)
def test_list_endpoints_never_500_on_odd_query(client_for, artist, task, path, query):
    ok_or_client_error(client_for(artist).get(f"{BASE}/{path}/?{query}"))


@pytest.mark.parametrize("path", ["tasks", "entities", "versions", "projects"])
@pytest.mark.parametrize("pk", [HUGE, "%00", "abc", "-1", "0"])
def test_detail_endpoints_never_500_on_odd_id(client_for, artist, task, path, pk):
    ok_or_client_error(client_for(artist).get(f"{BASE}/{path}/{pk}/"))


@pytest.mark.parametrize("path", ["tasks", "versions"])
def test_transition_on_odd_id(client_for, artist, task, path):
    res = client_for(artist).post(f"{BASE}/{path}/{HUGE}/transition/", {"to": "done"}, format="json")
    ok_or_client_error(res)


def test_notes_odd_targets(client_for, artist):
    c = client_for(artist)
    ok_or_client_error(c.get(f"{BASE}/notes/?target_type=entity&target_id={HUGE}"))
    ok_or_client_error(c.get(f"{BASE}/notes/?target_type=%00&target_id=1"))
    ok_or_client_error(c.post(f"{BASE}/notes/", {"target_type": "entity", "target_id": int(HUGE), "body": "x"}, format="json"))


# --- POST / PATCH: 本文 ---
def test_nul_and_huge_values_in_writes(client_for, artist, project, entity, step, task):
    c = client_for(artist)
    cases = [
        ("post", "projects", {"code": "NUL1", "name": f"a{NUL}b"}),
        ("post", "projects", {"code": f"A{NUL}", "name": "x"}),
        ("post", "entities", {"project": project.id, "name": f"a{NUL}", "path": f"p{NUL}"}),
        ("post", "tasks", {"entity": int(HUGE), "step": step.id}),
        ("post", "tasks", {"entity": entity.id, "step": int(HUGE)}),
        ("post", "tasks", {"entity": entity.id, "step": step.id, "assignee": int(HUGE)}),
        ("post", "tasks", {"entity": entity.id, "step": step.id, "estimate_h": 1e308}),
        ("post", "tasks", {"entity": entity.id, "step": step.id, "estimate_h": "NaN"}),
        ("patch", f"tasks/{task.id}", {"estimate_h": "Infinity"}),
        ("post", "versions", {"task": task.id, "file_ref": f"a{NUL}"}),
        ("post", "versions", {"task": task.id, "file_ref": "a", "dcc": {"k": f"v{NUL}"}}),
        ("post", "versions", {"task": task.id, "file_ref": "a", "dcc": {f"k{NUL}": 1}}),
        ("post", "versions", {"task": task.id, "file_ref": "a", "comment": f"c{NUL}"}),
        ("post", "notes", {"target_type": "task", "target_id": task.id, "body": f"b{NUL}"}),
        ("post", f"tasks/{task.id}/transition", {"to": f"x{NUL}"}),
    ]
    for method, path, body in cases:
        res = getattr(c, method)(f"{BASE}/{path}/", body, format="json")
        ok_or_client_error(res)


def test_odd_idempotency_key_and_json_shapes(client_for, artist, task):
    c = client_for(artist)
    payload = {"task": task.id, "file_ref": "a"}
    ok_or_client_error(c.post(f"{BASE}/versions/", payload, format="json", headers={"Idempotency-Key": "k" * 500}))
    for body in ("[]", '"str"', "123", "null", "{", ""):
        res = c.post(f"{BASE}/versions/", body, content_type="application/json")
        ok_or_client_error(res)


def test_deeply_nested_json_is_a_400_not_a_500(client_for, artist, task):
    body = '{"task": 1, "file_ref": "a", "dcc": ' + "[" * 5000 + "]" * 5000 + "}"
    res = client_for(artist).post(f"{BASE}/versions/", body, content_type="application/json")
    assert res.status_code == 400


def test_form_and_multipart_bodies_are_rejected(client_for, artist, project):
    """画面・スクリプトは JSON だけを送る。他の形式は受け付けない(415)。"""
    res = client_for(artist).post(f"{BASE}/projects/", {"code": "FORM1", "name": "x"})  # multipart
    assert res.status_code == 415


# --- 取り込み ---
def quality(**over):
    p = {
        "project": "DEMO", "scan_run_id": 1, "scanned_at": "2026-10-11T09:00:00+09:00",
        "results": [{"asset_path": "a/b.fbx", "defects": 1}],
    }
    p.update(over)
    return p


@pytest.mark.parametrize(
    "patch",
    [
        {"scan_run_id": int(HUGE)}, {"scan_run_id": -1}, {"scan_run_id": 1.5},
        {"results": [{"asset_path": f"a{NUL}", "defects": 1}]},
        {"results": [{"asset_path": "a", "defects": int(HUGE)}]},
        {"results": [{"asset_path": "a", "defects": 1.5}]},
        {"results": [{"asset_path": "a" * 501, "defects": 1}]},
        {"results": "x"}, {"results": None}, {"project": NUL}, {"project": "x" * 33},
        {"scanned_at": "0000-01-01T00:00:00Z"}, {"scanned_at": "9999-12-31T23:59:59+23:59"},
    ],
)
def test_quality_ingest_odd_values(project, patch):
    res = APIClient().post(f"{BASE}/ingest/quality/", quality(**patch), format="json", **KEY)
    ok_or_client_error(res)


@pytest.mark.parametrize(
    "patch",
    [
        {"run_id": NUL}, {"run_id": "x" * 65}, {"version": int(HUGE)}, {"version": 0}, {"diff_ratio": 1e308},
        {"diff_ratio": "NaN"}, {"conditions": {"k": f"v{NUL}"}}, {"conditions": {f"k{NUL}": 1}}, {"conditions": []},
        {"captured_at": "0000-01-01T00:00:00Z"}, {"verdict": NUL},
    ],
)
def test_visual_ingest_odd_values(task, patch):
    version = VersionFactory.create(task)
    p = {"run_id": "r", "version": version.id, "verdict": "pass", "diff_ratio": 0.1, "captured_at": "2026-10-11T10:00:00+09:00"}
    p.update(patch)
    res = APIClient().post(f"{BASE}/ingest/visual/", json.dumps(p), content_type="application/json", **KEY)
    ok_or_client_error(res)


# --- 認証まわり ---
def test_login_odd_bodies(db):
    c = APIClient()
    for body in ({"username": NUL, "password": "x"}, {"username": "a" * 10000, "password": "x"}, {"username": ["a"], "password": "x"}):
        ok_or_client_error(c.post(f"{BASE}/auth/login/", body, format="json"))


# --- 修正した挙動を具体的に確認する(500 でなく、理由つきの 400) ---
def test_nul_in_url_is_a_400_with_unified_error(client_for, artist, project):
    c = client_for(artist)
    for url in (f"{BASE}/tasks/?q=%00", f"{BASE}/projects/a%00b/", f"{BASE}/entities/?project=%00"):
        res = c.get(url)
        assert res.status_code == 400 and res.json()["code"] == "validation_error"


def test_huge_ids_are_a_400(client_for, artist, project):
    c = client_for(artist)
    assert c.get(f"{BASE}/tasks/?entity={HUGE}").status_code == 400
    assert c.get(f"{BASE}/entities/?project={HUGE}").status_code == 400
    assert c.get(f"{BASE}/projects/{HUGE}/").status_code == 404


def test_nul_inside_json_fields_is_a_400(client_for, artist, task):
    res = client_for(artist).post(
        f"{BASE}/versions/", {"task": task.id, "file_ref": "a", "dcc": {"app": f"x{NUL}"}}, format="json"
    )
    assert res.status_code == 400 and "dcc" in res.json()["detail"]


def test_quality_defects_can_exceed_32_bits(project, entity):
    """同じパスの欠陥数は合算する。32 ビットを超えても保存できる(bigint)。"""
    rows = [{"asset_path": "assets/props/crate/a.fbx", "defects": 2_000_000_000}] * 3
    res = APIClient().post(f"{BASE}/ingest/quality/", quality(results=rows), format="json", **KEY)
    assert res.status_code == 201 and res.json()["defects_total"] == 6_000_000_000
