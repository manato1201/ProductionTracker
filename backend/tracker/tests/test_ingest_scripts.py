"""scripts/send_quality.py: insight.db → 取り込み API の件数一致(検証チェックリスト)。"""

import sqlite3
import sys
from pathlib import Path

import pytest
from rest_framework.test import APIClient

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import send_quality  # noqa: E402
import send_visual  # noqa: E402


@pytest.fixture
def insight_db(tmp_path):
    path = tmp_path / "insight.db"
    con = sqlite3.connect(path)
    con.executescript(
        """
        create table scan_runs(id integer primary key, scanned_at text);
        create table defect_records(id integer primary key, scan_run_id integer, asset_path text);
        insert into scan_runs values (1, '2026-10-24T09:00:00+09:00'), (2, '2026-10-25T09:00:00');
        """
    )
    rows = [
        (2, "assets/props/crate/a.fbx"), (2, "assets/props/crate/a.fbx"),
        (2, "assets\\props\\crate\\b.fbx"), (2, "assets/unknown/c.fbx"), (1, "assets/props/crate/old.fbx"),
    ]
    con.executemany("insert into defect_records(scan_run_id, asset_path) values (?, ?)", rows)
    con.commit()
    con.close()
    return str(path)


def test_payload_uses_latest_run_and_counts_defects(insight_db):
    payload, total = send_quality.build_quality_payload(insight_db, "DEMO")
    assert payload["scan_run_id"] == 2 and total == 4
    assert {r["asset_path"]: r["defects"] for r in payload["results"]} == {
        "assets/props/crate/a.fbx": 2, "assets\\props\\crate\\b.fbx": 1, "assets/unknown/c.fbx": 1,
    }
    assert payload["scanned_at"].endswith("+00:00")  # 時刻帯の無い値は UTC とみなす


def test_specific_run_and_missing_run(insight_db):
    payload, total = send_quality.build_quality_payload(insight_db, "DEMO", 1)
    assert payload["scan_run_id"] == 1 and total == 1
    with pytest.raises(LookupError):
        send_quality.build_quality_payload(insight_db, "DEMO", 99)


def test_identifiers_are_validated(insight_db):
    with pytest.raises(ValueError):
        send_quality.build_quality_payload(insight_db, "DEMO", runs_table="scan_runs; drop table x")


def test_ingested_total_matches_source_db(insight_db, project, entity):
    payload, source_total = send_quality.build_quality_payload(insight_db, "DEMO")
    res = APIClient().post("/api/v1/ingest/quality/", payload, format="json", HTTP_X_API_KEY="test-ingest-key")
    assert res.status_code == 201
    body = res.json()
    assert body["defects_total"] == source_total  # 元の insight.db と一致
    assert body["matched"] == 2 and body["unmatched"] == ["assets/unknown/c.fbx"]


def test_visual_loader_validates_required_fields(tmp_path):
    f = tmp_path / "r.json"
    f.write_text('{"run_id": "r1", "version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="verdict"):
        send_visual.load_results(str(f))
    f.write_text(
        '[{"run_id":"r1","version":1,"verdict":"pass","diff_ratio":0,"captured_at":"2026-10-25T10:00:00Z"}]',
        encoding="utf-8",
    )
    assert len(send_visual.load_results(str(f))) == 1
