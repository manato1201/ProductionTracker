"""監査ログ(設計 S-C): 版・ノートの変更を、誰が・いつ・何を、だけ残す。本文は残さない。"""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from tracker.audit import record
from tracker.models import AuditEvent, Project

from .factories import ProjectFactory, UserFactory

BASE = "/api/v1"
SECRET_COMMENT = "社外秘のコメント-XYZ"
SECRET_PATH = "P:/secret/internal_path_v1.hbjson"
SECRET_NOTE = "ノート本文の秘密-ABC"


def events():
    return list(AuditEvent.objects.order_by("id"))


def make_version(client, task, **extra):
    payload = {"task": task.id, "file_ref": SECRET_PATH, "comment": SECRET_COMMENT, **extra}
    return client.post(f"{BASE}/versions/", payload, format="json")


def test_version_create_is_recorded_without_comment_or_path(client_for, artist, task, project):
    res = make_version(client_for(artist), task)
    assert res.status_code == 201
    (e,) = events()
    assert (e.action, e.actor_id, e.actor_name, e.project_id, e.project_code) == (
        "version.create", artist.id, artist.username, project.id, "DEMO")
    assert (e.target_type, e.target_id) == ("version", res.json()["id"])
    assert e.detail == {"number": 1, "status": "draft", "task": task.id}
    dump = str(e.__dict__)
    assert SECRET_COMMENT not in dump and SECRET_PATH not in dump


def test_idempotent_replay_is_not_recorded_twice(client_for, artist, task):
    c = client_for(artist)
    for _ in range(2):
        c.post(f"{BASE}/versions/", {"task": task.id, "file_ref": "a"}, format="json", headers={"Idempotency-Key": "k1"})
    assert [e.action for e in events()] == ["version.create"]


def test_refused_changes_leave_no_record(client_for, viewer, outsider, task):
    assert make_version(client_for(viewer), task).status_code == 403
    assert make_version(client_for(outsider), task).status_code == 400
    assert events() == []


def test_version_transition_records_from_and_to_and_the_reviewer(client_for, artist, reviewer, task):
    v = make_version(client_for(artist), task).json()
    url = f"{BASE}/versions/{v['id']}/transition/"
    assert client_for(artist).post(url, {"to": "submitted"}, format="json").status_code == 200
    assert client_for(artist).post(url, {"to": "approved"}, format="json").status_code == 403  # 却下・承認はレビュアーのみ
    assert client_for(reviewer).post(url, {"to": "approved"}, format="json").status_code == 200
    got = [(e.action, e.actor_name, e.detail.get("from"), e.detail.get("to")) for e in events()[1:]]
    assert got == [
        ("version.transition", artist.username, "draft", "submitted"),
        ("version.transition", reviewer.username, "submitted", "approved"),
    ]


def test_invalid_transition_leaves_no_record(client_for, artist, task):
    v = make_version(client_for(artist), task).json()
    res = client_for(artist).post(f"{BASE}/versions/{v['id']}/transition/", {"to": "approved"}, format="json")
    assert res.status_code in (403, 409)
    assert [e.action for e in events()] == ["version.create"]


def test_note_is_recorded_with_length_only(client_for, artist, task):
    res = client_for(artist).post(
        f"{BASE}/notes/", {"target_type": "task", "target_id": task.id, "body": SECRET_NOTE}, format="json")
    assert res.status_code == 201
    (e,) = events()
    assert (e.action, e.actor_name, e.target_type, e.target_id) == ("note.create", artist.username, "note", res.json()["id"])
    assert e.detail == {"body_length": len(SECRET_NOTE), "on_type": "task", "on_id": task.id}
    assert SECRET_NOTE not in str(e.__dict__)


def test_viewer_note_is_refused_and_not_recorded(client_for, viewer, task):
    res = client_for(viewer).post(
        f"{BASE}/notes/", {"target_type": "task", "target_id": task.id, "body": "x"}, format="json")
    assert res.status_code == 403 and events() == []


def test_recorder_drops_unlisted_detail_keys(task, artist, project):
    record(user=artist, action="note.create", project=project, target_type="note", target_id=1,
           body_length=3, body="leak", comment="leak", file_ref="leak")
    (e,) = events()
    assert e.detail == {"body_length": 3}


# ---- 追記のみ
def test_events_cannot_be_updated_or_deleted(artist, project):
    e = record(user=artist, action="note.create", project=project, target_type="note", target_id=1)
    e.actor_name = "someone-else"
    with pytest.raises(PermissionError):
        e.save()
    with pytest.raises(PermissionError):
        e.delete()
    assert AuditEvent.objects.get(pk=e.pk).actor_name == artist.username


def test_admin_site_is_read_only(project):
    model_admin = admin.site._registry[AuditEvent]
    request = RequestFactory().get("/admin/")
    request.user = get_user_model().objects.create_superuser("root", password="pass-12345")
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)


def test_records_outlive_the_user_and_the_project(artist, project):
    record(user=artist, action="note.create", project=project, target_type="note", target_id=1)
    artist.delete()
    Project.objects.filter(pk=project.pk).delete()
    (e,) = events()
    assert e.actor_id is None and e.project_id is None
    assert e.actor_name.startswith("user") and e.project_code == "DEMO"


# ---- 読み出し
def read(client, project, query=""):
    return client.get(f"{BASE}/projects/{project.code}/audit/{query}")


def test_reviewer_and_staff_can_read_but_artist_viewer_outsider_cannot(client_for, artist, reviewer, viewer, outsider, task, project):
    make_version(client_for(artist), task)
    staff = UserFactory(is_staff=True)

    for who in (reviewer, staff):
        res = read(client_for(who), project)
        assert res.status_code == 200
        (row,) = res.json()["results"]
        assert row["action"] == "version.create" and row["actor_name"] == artist.username
    assert read(client_for(artist), project).status_code == 403
    assert read(client_for(viewer), project).status_code == 403
    assert read(client_for(outsider), project).status_code == 404  # 見えないプロジェクトは存在も教えない


def test_anonymous_reads_get_401(project):
    from rest_framework.test import APIClient

    assert read(APIClient(), project).status_code == 401


def test_read_is_newest_first_filterable_and_scoped_to_the_project(client_for, artist, reviewer, task, project):
    c = client_for(artist)
    v = make_version(c, task).json()
    c.post(f"{BASE}/notes/", {"target_type": "task", "target_id": task.id, "body": "n"}, format="json")
    # 別プロジェクトの記録は混ざらない
    other = ProjectFactory()
    record(user=artist, action="note.create", project=other, target_type="note", target_id=99)

    rows = read(client_for(reviewer), project).json()["results"]
    assert [r["action"] for r in rows] == ["note.create", "version.create"]
    assert all(r["target_id"] != 99 for r in rows)
    only = read(client_for(reviewer), project, "?action=version.create").json()["results"]
    assert [r["target_id"] for r in only] == [v["id"]]
    assert read(client_for(reviewer), project, "?action=bogus").status_code == 400


def test_read_response_has_no_secret_fields(client_for, artist, reviewer, task, project):
    make_version(client_for(artist), task)
    text = read(client_for(reviewer), project).content.decode()
    assert SECRET_COMMENT not in text and SECRET_PATH not in text

