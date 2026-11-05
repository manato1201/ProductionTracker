"""主要なクエリの実行計画を出す(索引が効いているかの確認)。実データで走らせること。

PostgreSQL では `EXPLAIN`、SQLite では `EXPLAIN QUERY PLAN`。見るのは次の 3 点:
  - 大きな表で `Seq Scan`(PostgreSQL)/ `SCAN`(SQLite)が出ていないか
  - 並べ替えに `Sort` が出ていないか(索引で並べ替えを済ませられるか)
  - 行数の見積もりが実際と大きくずれていないか(`--analyze` で実測も出る。`ANALYZE` を先に)
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from tracker.models import Entity, Project, Task
from tracker.query_catalog import catalog


class Command(BaseCommand):
    help = "主要なクエリの実行計画を表示する"

    def add_arguments(self, parser):
        parser.add_argument("--analyze", action="store_true", help="実際に実行して実測も出す(EXPLAIN ANALYZE。PostgreSQL)")

    def handle(self, *args, analyze, **options):
        User = get_user_model()
        ids = {
            "project": getattr(Project.objects.order_by("id").first(), "id", 1),
            "entity": getattr(Entity.objects.order_by("id").first(), "id", 1),
            "task": getattr(Task.objects.order_by("id").first(), "id", 1),
            "user": getattr(User.objects.order_by("id").first(), "id", 1),
        }
        extra = {"analyze": True} if analyze and connection.vendor == "postgresql" else {}
        for name, queryset in catalog(ids).items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n■ {name}"))
            self.stdout.write(queryset.explain(**extra))
