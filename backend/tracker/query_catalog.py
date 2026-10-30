"""主要なクエリの一覧(実行計画の確認用)。実際の API が発行する絞り込み・並べ替えと同じ形にしてある。

使い道は 2 つ:
- `tests/test_query_plans.py` — SQLite の EXPLAIN QUERY PLAN で、全件走査が無いことを確かめる
- `python manage.py explain_queries` — 実データ(PostgreSQL)の実行計画を見る
"""

from django.utils import timezone

from .models import Entity, Note, Project, ProjectMember, QualityReport, Task, Version, VisualResult


def catalog(ids: dict | None = None) -> dict:
    ids = {"entity": 1, "user": 1, "task": 1, "project": 1, "version": 1, "content_type": 1, **(ids or {})}
    today = timezone.localdate()
    return {
        "タスク: アセットで": Task.objects.filter(entity_id=ids["entity"]),
        "タスク: 担当者で(自分のタスク)": Task.objects.filter(assignee_id=ids["user"]).order_by("due"),
        "タスク: 担当者 + 期限切れ": Task.objects.filter(assignee_id=ids["user"], due__lt=today).exclude(status="done"),
        "タスク: プロジェクトで(かんばん)": Task.objects.filter(entity__project_id=ids["project"]),
        "版: タスクで(新しい順)": Version.objects.filter(task_id=ids["task"]).order_by("-created_at"),
        "版: アセットで": Version.objects.filter(task__entity_id=ids["entity"]),
        "ノート: 対象で(新しい順)": Note.objects.filter(content_type_id=ids["content_type"], object_id=ids["entity"]).order_by("-created_at"),
        "品質: アセットで(新しい順)": QualityReport.objects.filter(entity_id=ids["entity"]).order_by("-scanned_at"),
        "品質: 同じ実行の置き換え": QualityReport.objects.filter(project_id=ids["project"], scan_run_id=1),
        "画面差分: 版で": VisualResult.objects.filter(version_id=ids["version"]),
        "画面差分: 再送の判定": VisualResult.objects.filter(run_id="r", version_id=ids["version"]),
        "アセット: プロジェクトで": Entity.objects.filter(project_id=ids["project"]).order_by("name"),
        "メンバー: ユーザーで(見える範囲)": ProjectMember.objects.filter(user_id=ids["user"]),
        "メンバー: プロジェクトで": ProjectMember.objects.filter(project_id=ids["project"]),
        "プロジェクト: コードで": Project.objects.filter(code="DEMO"),
        "版: 再送の判定(Idempotency-Key)": Version.objects.filter(created_by_id=ids["user"], idempotency_key="k"),
    }
