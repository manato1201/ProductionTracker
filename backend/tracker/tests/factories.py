import factory
from django.contrib.auth import get_user_model

from tracker.models import (
    Entity,
    Project,
    ProjectMember,
    Step,
    Task,
    Version,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = "pass-12345"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # パスワードをハッシュ化して保存する(ログインのテストで使う)
        return model_class.objects.create_user(*args, **kwargs)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    code = factory.Sequence(lambda n: f"PRJ{n}")
    name = factory.Sequence(lambda n: f"Project {n}")


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectMember

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = ProjectMember.Role.ARTIST


class StepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Step
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"step{n}")
    name = factory.Sequence(lambda n: f"Step {n}")


class EntityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entity

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"asset{n}")
    path = ""


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    entity = factory.SubFactory(EntityFactory)
    step = factory.SubFactory(StepFactory)


class VersionFactory:
    @staticmethod
    def create(task, **kwargs):
        kwargs.setdefault("file_ref", "P:/x/v.hip")
        return Version.create_for_task(task, **kwargs)
