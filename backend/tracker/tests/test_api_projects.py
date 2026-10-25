import pytest
from django.db import IntegrityError, transaction

from .factories import EntityFactory, MemberFactory, ProjectFactory, StepFactory, TaskFactory

BASE = "/api/v1"


def test_requires_authentication(db):
    from rest_framework.test import APIClient

    res = APIClient().get(f"{BASE}/projects/")
    assert res.status_code == 401
    assert res.json()["code"] == "not_authenticated"


def test_list_shows_only_projects_user_belongs_to(client_for, project, artist):
    ProjectFactory(code="OTHER")
    res = client_for(artist).get(f"{BASE}/projects/")
    assert res.status_code == 200
    assert [p["code"] for p in res.json()["results"]] == ["DEMO"]


def test_staff_sees_all_projects(client_for, project, make_user):
    ProjectFactory(code="OTHER")
    staff = make_user(None, is_staff=True)
    res = client_for(staff).get(f"{BASE}/projects/")
    assert res.json()["count"] == 2


def test_create_makes_creator_a_reviewer(client_for, outsider):
    res = client_for(outsider).post(f"{BASE}/projects/", {"code": "NEW", "name": "新作", "due": "2026-12-31"}, format="json")
    assert res.status_code == 201
    body = res.json()
    assert body["my_role"] == "reviewer" and body["can_review"] is True
    assert body["task_counts"]["total"] == 0 and body["progress"] == 0


@pytest.mark.parametrize("code", ["1abc", "has space", "日本語", ""])
def test_create_rejects_invalid_code(client_for, outsider, code):
    res = client_for(outsider).post(f"{BASE}/projects/", {"code": code, "name": "x"}, format="json")
    assert res.status_code == 400
    assert res.json()["code"] == "validation_error"


def test_create_rejects_duplicate_code_and_bad_dates(client_for, outsider, project):
    c = client_for(outsider)
    assert c.post(f"{BASE}/projects/", {"code": "DEMO", "name": "x"}, format="json").status_code == 400
    res = c.post(f"{BASE}/projects/", {"code": "Z", "name": "x", "start": "2026-02-01", "due": "2026-01-01"}, format="json")
    assert res.status_code == 400


def test_retrieve_by_id_or_code(client_for, project, artist):
    c = client_for(artist)
    assert c.get(f"{BASE}/projects/{project.id}/").json()["code"] == "DEMO"
    assert c.get(f"{BASE}/projects/DEMO/").json()["id"] == project.id
    assert c.get(f"{BASE}/projects/NOPE/").status_code == 404


def test_cannot_see_other_projects(client_for, project, outsider):
    assert client_for(outsider).get(f"{BASE}/projects/DEMO/").status_code == 404


def test_patch_only_by_reviewer(client_for, project, artist, reviewer):
    assert client_for(artist).patch(f"{BASE}/projects/{project.id}/", {"name": "変更"}, format="json").status_code == 403
    res = client_for(reviewer).patch(f"{BASE}/projects/{project.id}/", {"name": "変更"}, format="json")
    assert res.status_code == 200 and res.json()["name"] == "変更"


def test_code_cannot_change(client_for, project, reviewer):
    res = client_for(reviewer).patch(f"{BASE}/projects/{project.id}/", {"code": "XXX"}, format="json")
    assert res.status_code == 400


def test_task_counts_and_progress(client_for, project, artist, step):
    e = EntityFactory(project=project)
    TaskFactory(entity=e, step=step, status="done")
    TaskFactory(entity=e, step=StepFactory(), status="todo")
    body = client_for(artist).get(f"{BASE}/projects/DEMO/").json()
    assert body["task_counts"] == {"todo": 1, "in_progress": 0, "review": 0, "done": 1, "total": 2}
    assert body["progress"] == 0.5


def test_pagination_defaults_and_limits(client_for, outsider):
    for i in range(55):
        p = ProjectFactory(code=f"P{i:03d}")
        MemberFactory(project=p, user=outsider)
    c = client_for(outsider)
    first = c.get(f"{BASE}/projects/").json()
    assert first["count"] == 55 and len(first["results"]) == 50 and first["next"]
    assert len(c.get(f"{BASE}/projects/?page=2").json()["results"]) == 5
    assert len(c.get(f"{BASE}/projects/?page_size=1000").json()["results"]) == 55  # 上限 200 内


def test_ordering_is_whitelisted(client_for, project, artist):
    c = client_for(artist)
    assert c.get(f"{BASE}/projects/?ordering=name").status_code == 200
    assert c.get(f"{BASE}/projects/?ordering=password").status_code == 400


def test_members_list(client_for, project, artist, reviewer):
    res = client_for(artist).get(f"{BASE}/projects/DEMO/members/").json()
    assert {m["role"] for m in res["results"]} == {"artist", "reviewer"}


def test_unknown_api_path_is_json_404(client_for, artist):
    res = client_for(artist).get(f"{BASE}/nope/")
    assert res.status_code == 404 and res.json()["code"] == "not_found"


def test_project_code_is_case_insensitively_unique(client_for, outsider, project):
    """demo と DEMO を別物にしない。DB の制約が最後の砦で、API は 500 でなく 400 を返す。"""
    res = client_for(outsider).post(f"{BASE}/projects/", {"code": "demo", "name": "x"}, format="json")
    assert res.status_code == 400 and res.json()["code"] == "validation_error"
    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectFactory(code="Demo")


def test_viewer_cannot_write_flag(client_for, project, viewer):
    body = client_for(viewer).get(f"{BASE}/projects/DEMO/").json()
    assert (body["my_role"], body["can_write"], body["can_review"]) == ("viewer", False, False)


def test_permission_flags_follow_the_model_rules(client_for, project, artist, reviewer, make_user):
    """UI に出す can_write / can_review は、モデルの判定(Project.can_write / can_review)と常に一致する。"""
    staff = make_user(None, is_staff=True)
    for user in (artist, reviewer, staff):
        body = client_for(user).get(f"{BASE}/projects/DEMO/").json()
        assert body["can_write"] == project.can_write(user)
        assert body["can_review"] == project.can_review(user)
    assert client_for(staff).get(f"{BASE}/projects/DEMO/").json()["can_review"] is False  # 管理者でも承認はレビュアーのみ
