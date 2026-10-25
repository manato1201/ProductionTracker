"""デモデータの投入(開発・画面確認用)。同じ名前があれば作り直さない。"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import Entity, Project, ProjectMember, Step, Task, Version

User = get_user_model()


class Command(BaseCommand):
    help = "デモ用のプロジェクト・ユーザー・アセット・タスクを作る"

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="デモユーザー(demo_reviewer / demo_artist / demo_viewer)のパスワード")

    def handle(self, *args, password, **options):
        users = {}
        for name, role in [("demo_reviewer", "reviewer"), ("demo_artist", "artist"), ("demo_viewer", "viewer")]:
            user, created = User.objects.get_or_create(username=name)
            if created:
                user.set_password(password)
                user.save()
            users[role] = user

        project, _ = Project.objects.get_or_create(
            code="DEMO",
            defaults={"name": "デモ作品", "start": timezone.localdate(), "due": timezone.localdate() + timedelta(days=60)},
        )
        for role, user in users.items():
            ProjectMember.objects.get_or_create(project=project, user=user, defaults={"role": role})

        steps = {s.code: s for s in Step.objects.all()}
        today = timezone.localdate()
        specs = [
            ("木箱", "assets/props/crate", ["model", "texture"]),
            ("ドラゴン", "assets/chars/dragon", ["model", "rig", "fx"]),
            ("焚き火", "assets/fx/campfire", ["fx", "light"]),
        ]
        for i, (name, path, step_codes) in enumerate(specs):
            entity, _ = Entity.objects.get_or_create(project=project, kind="asset", name=name, defaults={"path": path})
            for j, code in enumerate(step_codes):
                Task.objects.get_or_create(
                    entity=entity,
                    step=steps[code],
                    defaults={
                        "assignee": users["artist"],
                        "due": today + timedelta(days=(i * 3 + j * 2) - 2),
                        "priority": ["normal", "high", "low", "urgent"][(i + j) % 4],
                        "status": ["todo", "in_progress", "review", "done"][(i + j) % 4],
                    },
                )
        for task in Task.objects.filter(entity__project=project, status__in=["review", "done"]):
            if not task.versions.exists():
                Version.create_for_task(task, file_ref=f"P:/demo/{task.entity.name}_v001", created_by=users["artist"], status="submitted")
        self.stdout.write(self.style.SUCCESS("デモデータを作成しました(プロジェクトコード: DEMO)"))
