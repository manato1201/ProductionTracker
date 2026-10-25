import pytest

from tracker.models import Version

from .factories import StepFactory, TaskFactory, VersionFactory

BASE = "/api/v1"


def create(client, task, **extra):
    payload = {"task": task.id, "file_ref": "P:/project/fx/fluid_v012.hbjson", "comment": "粒子数 48,000", **extra}
    return client.post(f"{BASE}/versions/", payload, format="json")


def test_version_numbers_increment_per_task(client_for, artist, task):
    c = client_for(artist)
    assert [create(c, task).json()["number"] for _ in range(3)] == [1, 2, 3]
    other = TaskFactory(entity=task.entity, step=StepFactory())
    assert create(c, other).json()["number"] == 1


def test_version_create_defaults(client_for, artist, task):
    body = create(client_for(artist), task, thumbnail="https://example.test/t.png", dcc={"app": "houdini", "version": "21.0.700"}).json()
    assert body["status"] == "draft" and body["created_by"] == artist.id
    assert body["thumbnail"].endswith("t.png") and body["dcc"]["app"] == "houdini"
    assert body["task_name"] == "FX" and body["entity_name"] == "crate"


def test_version_create_cannot_start_approved(client_for, artist, task):
    assert create(client_for(artist), task, status="approved").status_code == 400
    assert create(client_for(artist), task, status="submitted").status_code == 201


def test_viewer_and_outsider_cannot_create_version(client_for, viewer, outsider, task):
    assert create(client_for(viewer), task).status_code == 403
    assert create(client_for(outsider), task).status_code == 400


def test_idempotency_key_returns_same_version(client_for, artist, task):
    """Publish の再送で重複しない(設計書 Phase 8)。"""
    c = client_for(artist)
    payload = {"task": task.id, "file_ref": "P:/x/fluid_v012.hip"}
    first = c.post(f"{BASE}/versions/", payload, format="json", headers={"Idempotency-Key": "abc123-12"})
    again = c.post(f"{BASE}/versions/", payload, format="json", headers={"Idempotency-Key": "abc123-12"})
    assert first.status_code == 201 and again.status_code == 200
    assert first.json()["id"] == again.json()["id"]
    assert Version.objects.filter(task=task).count() == 1
    # 鍵が違えば別の版
    third = c.post(f"{BASE}/versions/", payload, format="json", headers={"Idempotency-Key": "abc123-13"})
    assert third.status_code == 201 and third.json()["number"] == 2


def test_idempotency_key_reused_for_other_task_conflicts(client_for, artist, task):
    c = client_for(artist)
    other = TaskFactory(entity=task.entity, step=StepFactory())
    c.post(f"{BASE}/versions/", {"task": task.id, "file_ref": "a"}, format="json", headers={"Idempotency-Key": "k"})
    res = c.post(f"{BASE}/versions/", {"task": other.id, "file_ref": "a"}, format="json", headers={"Idempotency-Key": "k"})
    assert res.status_code == 409 and res.json()["code"] == "idempotency_conflict"


def test_idempotency_key_is_scoped_to_user(client_for, artist, make_user, task):
    other_artist = make_user("artist")
    k = {"Idempotency-Key": "same"}
    a = client_for(artist).post(f"{BASE}/versions/", {"task": task.id, "file_ref": "a"}, format="json", headers=k)
    b = client_for(other_artist).post(f"{BASE}/versions/", {"task": task.id, "file_ref": "b"}, format="json", headers=k)
    assert a.json()["id"] != b.json()["id"]


def test_token_authentication_for_publish(project, artist, task):
    """DCC パネルからは、ユーザー別トークンで版を登録できる(Authorization: Token)。"""
    from rest_framework.authtoken.models import Token
    from rest_framework.test import APIClient

    token = Token.objects.create(user=artist)
    c = APIClient()
    assert create(c, task).status_code == 401
    c.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    assert create(c, task).status_code == 201


def test_version_transitions(client_for, artist, reviewer, task):
    v = create(client_for(artist), task).json()
    url = f"{BASE}/versions/{v['id']}/transition/"
    assert client_for(artist).post(url, {"to": "approved"}, format="json").status_code == 409  # 作成中 → 承認 は不可
    assert client_for(artist).post(url, {"to": "submitted"}, format="json").json()["status"] == "submitted"
    assert client_for(artist).post(url, {"to": "approved"}, format="json").status_code == 403  # 承認はレビュアーのみ
    assert client_for(reviewer).post(url, {"to": "approved"}, format="json").json()["status"] == "approved"
    assert client_for(reviewer).post(url, {"to": "rejected"}, format="json").status_code == 409


@pytest.mark.parametrize("auto_return,expected", [(False, "review"), (True, "in_progress")])
def test_rejecting_version_returns_task_only_when_configured(client_for, reviewer, task, settings, auto_return, expected):
    settings.RETURN_TASK_ON_VERSION_REJECT = auto_return
    task.status = "review"
    task.save()
    v = VersionFactory.create(task, status="submitted")
    res = client_for(reviewer).post(f"{BASE}/versions/{v.id}/transition/", {"to": "rejected"}, format="json")
    assert res.status_code == 200
    task.refresh_from_db()
    assert task.status == expected


def test_version_list_filters(client_for, artist, task):
    VersionFactory.create(task)
    VersionFactory.create(task, status="submitted")
    c = client_for(artist)
    assert c.get(f"{BASE}/versions/?task={task.id}").json()["count"] == 2
    assert c.get(f"{BASE}/versions/?task={task.id}&status=submitted").json()["count"] == 1
    assert c.get(f"{BASE}/versions/?entity={task.entity_id}").json()["count"] == 2
    first = c.get(f"{BASE}/versions/?task={task.id}").json()["results"][0]
    assert first["number"] == 2  # 新しい順


# --- ノート ---
@pytest.mark.parametrize("target", ["entity", "task", "version"])
def test_notes_on_three_target_types(client_for, artist, entity, task, target):
    obj = {"entity": entity, "task": task, "version": None}[target]
    if target == "version":
        obj = VersionFactory.create(task)
    c = client_for(artist)
    res = c.post(f"{BASE}/notes/", {"target_type": target, "target_id": obj.id, "body": " 見るポイント: 影 "}, format="json")
    assert res.status_code == 201
    assert res.json()["body"] == "見るポイント: 影" and res.json()["target_type"] == target
    listed = c.get(f"{BASE}/notes/?target_type={target}&target_id={obj.id}").json()
    assert listed["count"] == 1 and listed["results"][0]["author"] == artist.id


def test_note_rejects_other_target_types(client_for, artist, project):
    for bad in ("project", "user", "contenttype"):
        res = client_for(artist).post(f"{BASE}/notes/", {"target_type": bad, "target_id": project.id, "body": "x"}, format="json")
        assert res.status_code == 400
    assert client_for(artist).get(f"{BASE}/notes/?target_type=project&target_id=1").status_code == 400


def test_note_permissions(client_for, viewer, outsider, artist, entity):
    body = {"target_type": "entity", "target_id": entity.id, "body": "hi"}
    assert client_for(viewer).post(f"{BASE}/notes/", body, format="json").status_code == 403
    assert client_for(outsider).post(f"{BASE}/notes/", body, format="json").status_code == 400
    assert client_for(outsider).get(f"{BASE}/notes/?target_type=entity&target_id={entity.id}").status_code == 404
    assert client_for(viewer).get(f"{BASE}/notes/?target_type=entity&target_id={entity.id}").status_code == 200


def test_note_blank_body_rejected(client_for, artist, entity):
    res = client_for(artist).post(f"{BASE}/notes/", {"target_type": "entity", "target_id": entity.id, "body": "   "}, format="json")
    assert res.status_code == 400
