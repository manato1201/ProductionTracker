
from tracker.models import Task

from .factories import EntityFactory, ProjectFactory, StepFactory, TaskFactory, VersionFactory

BASE = "/api/v1"


def test_entity_create_and_normalize_path(client_for, project, artist):
    res = client_for(artist).post(
        f"{BASE}/entities/", {"project": project.id, "name": "dragon", "path": "assets\\chars\\dragon\\"}, format="json"
    )
    assert res.status_code == 201
    assert res.json()["path"] == "assets/chars/dragon" and res.json()["kind"] == "asset"


def test_entity_shot_is_not_supported_yet(client_for, project, artist):
    res = client_for(artist).post(f"{BASE}/entities/", {"project": project.id, "name": "s010", "kind": "shot"}, format="json")
    assert res.status_code == 400


def test_entity_duplicate_name_rejected(client_for, project, artist, entity):
    res = client_for(artist).post(f"{BASE}/entities/", {"project": project.id, "name": entity.name}, format="json")
    assert res.status_code == 400


def test_viewer_cannot_write(client_for, project, viewer, entity, step):
    c = client_for(viewer)
    assert c.get(f"{BASE}/entities/?project=DEMO").status_code == 200
    assert c.post(f"{BASE}/entities/", {"project": project.id, "name": "x"}, format="json").status_code == 403
    assert c.patch(f"{BASE}/entities/{entity.id}/", {"name": "y"}, format="json").status_code == 403
    assert c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": step.id}, format="json").status_code == 403


def test_outsider_cannot_create_in_project(client_for, project, outsider):
    res = client_for(outsider).post(f"{BASE}/entities/", {"project": project.id, "name": "x"}, format="json")
    assert res.status_code == 400  # 見えないプロジェクトは「存在しない」として扱う


def test_entity_filters_and_counts(client_for, project, artist, entity, step):
    TaskFactory(entity=entity, step=step, status="done")
    EntityFactory(project=ProjectFactory(code="OTHER"), name="hidden")
    body = client_for(artist).get(f"{BASE}/entities/?project=DEMO&q=cra").json()
    assert body["count"] == 1
    assert body["results"][0]["task_count"] == 1 and body["results"][0]["done_count"] == 1


def test_task_create_defaults_and_validation(client_for, project, artist, entity, step, make_user):
    c = client_for(artist)
    res = c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": step.id, "assignee": artist.id, "due": "2026-10-20"}, format="json")
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "todo" and body["step_name"] == "FX" and body["entity_name"] == "crate"
    assert body["assignee_name"] == artist.username and body["project_code"] == "DEMO"
    # 同じ工程は 1 アセットに 1 つ
    assert c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": step.id}, format="json").status_code == 400
    # 担当者はメンバーのみ
    stranger = make_user(None)
    other = StepFactory()
    res = c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": other.id, "assignee": stranger.id}, format="json")
    assert res.status_code == 400
    # 見積は負にできない
    res = c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": other.id, "estimate_h": -1}, format="json")
    assert res.status_code == 400


def test_status_cannot_be_patched_directly(client_for, artist, task):
    c = client_for(artist)
    res = c.patch(f"{BASE}/tasks/{task.id}/", {"status": "done", "priority": "high"}, format="json")
    assert res.status_code == 200
    assert res.json()["status"] == "todo" and res.json()["priority"] == "high"


def test_task_entity_and_step_are_immutable(client_for, artist, task, entity):
    other = EntityFactory(project=entity.project)
    assert client_for(artist).patch(f"{BASE}/tasks/{task.id}/", {"entity": other.id}, format="json").status_code == 400


def test_transition_endpoint_invalid_is_409(client_for, reviewer, task):
    """未着手 → 完了 は 409(検証チェックリスト)。"""
    res = client_for(reviewer).post(f"{BASE}/tasks/{task.id}/transition/", {"to": "done"}, format="json")
    assert res.status_code == 409
    assert res.json()["code"] == "invalid_transition"
    task.refresh_from_db()
    assert task.status == "todo"


def test_transition_endpoint_unknown_target_is_400(client_for, reviewer, task):
    assert client_for(reviewer).post(f"{BASE}/tasks/{task.id}/transition/", {"to": "nope"}, format="json").status_code == 400
    assert client_for(reviewer).post(f"{BASE}/tasks/{task.id}/transition/", {}, format="json").status_code == 400


def test_full_workflow_through_api(client_for, artist, reviewer, task):
    a, r = client_for(artist), client_for(reviewer)
    url = f"{BASE}/tasks/{task.id}/transition/"
    assert a.post(url, {"to": "in_progress"}, format="json").json()["status"] == "in_progress"
    assert a.post(url, {"to": "review"}, format="json").json()["status"] == "review"
    # アーティストは承認できない(403)
    res = a.post(url, {"to": "done"}, format="json")
    assert res.status_code == 403 and res.json()["code"] == "permission_denied"
    # 版が無いと完了できない(409)
    res = r.post(url, {"to": "done"}, format="json")
    assert res.status_code == 409 and res.json()["code"] == "version_required"
    VersionFactory.create(task)
    body = r.post(url, {"to": "done"}, format="json").json()
    assert body["status"] == "done" and body["version_count"] == 1


def test_outsider_gets_404_on_transition(client_for, outsider, task):
    assert client_for(outsider).post(f"{BASE}/tasks/{task.id}/transition/", {"to": "in_progress"}, format="json").status_code == 404


def test_task_filters(client_for, project, artist, reviewer, entity):
    s1, s2, s3 = StepFactory(), StepFactory(), StepFactory()
    t1 = TaskFactory(entity=entity, step=s1, assignee=artist, status="in_progress", due="2000-01-01")
    t2 = TaskFactory(entity=entity, step=s2, assignee=reviewer, status="done", due="2000-01-01")
    t3 = TaskFactory(entity=entity, step=s3, status="todo")
    c = client_for(artist)
    ids = lambda q: sorted(t["id"] for t in c.get(f"{BASE}/tasks/?{q}").json()["results"])  # noqa: E731
    assert ids("assignee=me") == [t1.id]
    assert ids(f"assignee={reviewer.id}") == [t2.id]
    assert ids("status=todo,in_progress") == sorted([t1.id, t3.id])
    assert ids("overdue=1") == [t1.id]  # 完了済みは期限切れにしない
    assert ids(f"entity={entity.id}&project=DEMO") == sorted([t1.id, t2.id, t3.id])
    assert ids("project=NOPE") == []
    assert c.get(f"{BASE}/tasks/?status=bogus").status_code == 400
    assert c.get(f"{BASE}/tasks/?entity=abc").status_code == 400
    overdue = c.get(f"{BASE}/tasks/?overdue=1").json()["results"][0]
    assert overdue["is_overdue"] is True


def test_task_ordering_due_puts_empty_last(client_for, artist, entity):
    a = TaskFactory(entity=entity, step=StepFactory(), due="2026-01-02")
    b = TaskFactory(entity=entity, step=StepFactory(), due=None)
    c_ = TaskFactory(entity=entity, step=StepFactory(), due="2026-01-01")
    got = [t["id"] for t in client_for(artist).get(f"{BASE}/tasks/?ordering=due").json()["results"]]
    assert got == [c_.id, a.id, b.id]


def test_steps_are_seeded_by_migration(client_for, artist):
    body = client_for(artist).get(f"{BASE}/steps/").json()
    assert {"model", "rig", "fx"} <= {s["code"] for s in body["results"]}


def test_next_statuses_follow_the_transition_table(client_for, artist, task):
    c = client_for(artist)
    assert c.get(f"{BASE}/tasks/{task.id}/").json()["next_statuses"] == ["in_progress"]
    for status, expected in [("in_progress", ["review"]), ("review", ["in_progress", "done"]), ("done", ["in_progress"])]:
        Task.objects.filter(pk=task.pk).update(status=status)
        assert c.get(f"{BASE}/tasks/{task.id}/").json()["next_statuses"] == expected
