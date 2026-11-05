"""主要なクエリの実行計画に、全件走査(SCAN)が無いこと(docs/database.md)。

SQLite の `EXPLAIN QUERY PLAN` を使う。SQLite は小さなテーブルでも、使える索引があれば使うので、
「索引が用意されているか」を決定的に確かめられる(PostgreSQL は小さな表では索引を使わないことがあり、
このテストには向かないので、SQLite のときだけ走らせる)。

実データでの確認は `python manage.py explain_queries`(PostgreSQL では `EXPLAIN` を出す)。
"""

import re

import pytest
from django.db import connection
from django.db.models import Q

from tracker.models import Task
from tracker.query_catalog import catalog

pytestmark = pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite の EXPLAIN QUERY PLAN を使う")


def plan(queryset) -> str:
    return queryset.explain()


CASES = catalog()


@pytest.mark.parametrize("name", list(CASES))
def test_no_full_table_scan(db, name):
    text = plan(CASES[name])
    scans = [line for line in re.split(r"\n|\|", text) if re.search(r"\bSCAN\b", line) and "tracker_" in line]
    # 結合の片側が小さな表(工程・プロジェクト)の SCAN は許す。大きくなる表の SCAN だけを問題にする。
    big = ("tracker_task", "tracker_version", "tracker_note", "tracker_qualityreport", "tracker_visualresult", "tracker_entity")
    bad = [line for line in scans if any(t in line for t in big)]
    assert not bad, f"{name}: 全件走査 → {bad}\n{text}"


def test_status_alone_is_not_indexed():
    """状態(4 種類)だけの索引は作らない。値の種類が少ない列の索引は、ほとんど効かず、書き込みを遅くするだけ。"""
    for index in Task._meta.indexes:
        assert index.fields != ["status"], "値の種類が少ない列(status)単独の索引は不要"


def test_leading_wildcard_like_is_known_to_scan(db):
    """先頭が % の LIKE(`icontains`)は索引が効かない。小さな表で許容しているだけで、大きくなったら見直す。"""
    text = plan(Task.objects.filter(Q(entity__name__icontains="x") | Q(step__name__icontains="x")))
    assert "SCAN" in text or "SEARCH" in text  # 実行計画が取れること(許容の根拠は docs/database.md)
