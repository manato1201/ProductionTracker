import pytest
from rest_framework.test import APIClient

from .factories import (
    EntityFactory,
    MemberFactory,
    ProjectFactory,
    StepFactory,
    TaskFactory,
    UserFactory,
)


@pytest.fixture
def project(db):
    return ProjectFactory(code="DEMO", name="デモ")


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def make_user(project):
    """プロジェクトに `role` で参加するユーザーと、そのログイン済みクライアントを作る。"""

    def make(role="artist", **kwargs):
        user = UserFactory(**kwargs)
        if role:
            MemberFactory(project=project, user=user, role=role)
        return user

    return make


@pytest.fixture
def reviewer(make_user):
    return make_user("reviewer")


@pytest.fixture
def artist(make_user):
    return make_user("artist")


@pytest.fixture
def viewer(make_user):
    return make_user("viewer")


@pytest.fixture
def outsider(db):
    return UserFactory()


@pytest.fixture
def client_for():
    return _client_for


@pytest.fixture
def entity(project):
    return EntityFactory(project=project, name="crate", path="assets/props/crate")


@pytest.fixture
def step(db):
    return StepFactory(code="fx", name="FX")


@pytest.fixture
def task(entity, step):
    return TaskFactory(entity=entity, step=step)
