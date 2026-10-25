from rest_framework.permissions import BasePermission

from .auth import IngestPrincipal
from .errors import Forbidden
from .models import Project, ProjectMember


class IsIngestClient(BasePermission):
    """取り込み API は X-API-Key で認証された外部ツールのみ(セッションの利用者は不可)。"""

    def has_permission(self, request, view):
        return isinstance(request.user, IngestPrincipal)


def visible_projects(user):
    """利用者が見られるプロジェクト。管理者は全て、それ以外はメンバーになっているもの。"""
    if user.is_staff:
        return Project.objects.all()
    return Project.objects.filter(pk__in=ProjectMember.objects.filter(user=user).values("project_id"))


def require_write(user, project: Project) -> None:
    if not project.can_write(user):
        raise Forbidden("このプロジェクトを編集する権限がありません。")


def visible_entities(user):
    from .models import Entity

    return Entity.objects.filter(project__in=visible_projects(user))


def visible_tasks(user):
    from .models import Task

    return Task.objects.filter(entity__project__in=visible_projects(user))


def visible_versions(user):
    from .models import Version

    return Version.objects.filter(task__entity__project__in=visible_projects(user))
