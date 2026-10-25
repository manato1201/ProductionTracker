"""取り込み API: 認証・冪等性・パス突き合わせ・件数の一致。"""

import pytest
from rest_framework.test import APIClient

from tracker.models import QualityReport, VisualResult

from .factories import VersionFactory

BASE = "/api/v1"
KEY = {"HTTP_X_API_KEY": "test-ingest-key"}


@pytest.fixture
def ingest_client():
    return APIClient()


def quality_payload(**over):
    payload = {
        "project": "DEMO",
        "scan_run_id": 7,
        "scanned_at": "2026-10-11T09:00:00+09:00",
        "results": [
            {"asset_path": "assets/props/crate/crate.fbx", "defects": 3},
            {"asset_path": "assets/props/crate/crate_lod1.fbx", "defects": 2},
            {"asset_path": "assets/chars/unknown/x.fbx", "defects": 4},
        ],
    }
    payload.update(over)
    return payload


# --- 認証 ---
@pytest.mark.parametrize("path", ["/ingest/quality/", "/ingest/visual/"])
def test_ingest_without_api_key_is_401(ingest_client, project, path):
    res = ingest_client.post(f"{BASE}{path}", {}, format="json")
    assert res.status_code == 401
    assert res["WWW-Authenticate"] == "X-API-Key"


def test_ingest_with_wrong_key_is_401(ingest_client, project):
    res = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", HTTP_X_API_KEY="wrong")
    assert res.status_code == 401


def test_ingest_fails_closed_when_no_keys_configured(ingest_client, project, settings):
    settings.INGEST_API_KEYS = []
    res = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", HTTP_X_API_KEY="")
    assert res.status_code == 401


def test_session_user_cannot_use_ingest(artist, project):
    """取り込み用の鍵は画面の操作に使えず、逆に画面の利用者(セッション)は取り込みを呼べない。"""
    c = APIClient()
    c.force_login(artist)
    assert c.post(f"{BASE}/ingest/quality/", quality_payload(), format="json").status_code == 401


def test_api_key_does_not_work_for_ui_api(ingest_client, project):
    assert ingest_client.get(f"{BASE}/projects/", **KEY).status_code == 401


# --- 品質 ---
def test_quality_ingest_matches_by_prefix_and_reports_unmatched(ingest_client, project, entity):
    res = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", **KEY)
    assert res.status_code == 201
    body = res.json()
    assert body["received"] == 3 and body["stored"] == 3 and body["matched"] == 2
    assert body["unmatched"] == ["assets/chars/unknown/x.fbx"]
    # 元データの欠陥件数と一致(未対応のパスも保存して合計を保つ)
    assert body["defects_total"] == 9
    assert sum(QualityReport.objects.values_list("defects", flat=True)) == 9
    assert QualityReport.objects.filter(entity=entity).count() == 2


def test_quality_ingest_is_idempotent(ingest_client, project, entity):
    first = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", **KEY)
    again = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", **KEY)
    assert (first.status_code, again.status_code) == (201, 200)
    assert QualityReport.objects.count() == 3  # 重複登録しない


def test_quality_resend_overwrites_with_new_content(ingest_client, project, entity):
    ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", **KEY)
    smaller = quality_payload(results=[{"asset_path": "assets/props/crate/crate.fbx", "defects": 1}])
    res = ingest_client.post(f"{BASE}/ingest/quality/", smaller, format="json", **KEY)
    assert res.status_code == 200 and QualityReport.objects.count() == 1
    assert QualityReport.objects.get().defects == 1


def test_quality_other_scan_run_is_kept(ingest_client, project, entity):
    ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(scan_run_id=1), format="json", **KEY)
    ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(scan_run_id=2), format="json", **KEY)
    assert QualityReport.objects.count() == 6


def test_quality_duplicate_paths_are_summed(ingest_client, project, entity):
    rows = [{"asset_path": "assets\\props\\crate\\a.fbx", "defects": 1}, {"asset_path": "assets/props/crate/a.fbx", "defects": 2}]
    res = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(results=rows), format="json", **KEY)
    assert res.json()["stored"] == 1 and res.json()["defects_total"] == 3


@pytest.mark.parametrize(
    "patch",
    [{"project": "NOPE"}, {"scan_run_id": "x"}, {"scanned_at": "yesterday"}, {"results": [{"asset_path": "a", "defects": -1}]}],
)
def test_quality_validation_errors(ingest_client, project, patch):
    res = ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(**patch), format="json", **KEY)
    assert res.status_code == 400 and res.json()["code"] == "validation_error"


def test_quality_reports_are_readable_by_members_only(client_for, ingest_client, project, entity, artist, outsider):
    ingest_client.post(f"{BASE}/ingest/quality/", quality_payload(), format="json", **KEY)
    url = f"{BASE}/quality-reports/?entity={entity.id}"
    assert client_for(artist).get(url).json()["count"] == 2
    assert client_for(outsider).get(url).json()["count"] == 0


# --- 画面差分 ---
def visual_payload(ver, **over):
    p = {
        "run_id": "run-001",
        "version": ver.id,
        "verdict": "fail",
        "diff_ratio": 0.0132,
        "captured_at": "2026-10-11T10:00:00+09:00",
        "conditions": {"resolution": "1920x1080", "fixed_time": "2026-01-01T00:00:00Z", "seed": 42},
    }
    p.update(over)
    return p


def test_visual_ingest_and_idempotency(ingest_client, task):
    version = VersionFactory.create(task)
    first = ingest_client.post(f"{BASE}/ingest/visual/", visual_payload(version), format="json", **KEY)
    again = ingest_client.post(f"{BASE}/ingest/visual/", visual_payload(version, verdict="pass", diff_ratio=0.0), format="json", **KEY)
    assert (first.status_code, again.status_code) == (201, 200)
    assert VisualResult.objects.count() == 1
    row = VisualResult.objects.get()
    assert row.verdict == "pass" and row.conditions["seed"] == 42  # 撮影条件も保存
    # 別の run は別の行
    ingest_client.post(f"{BASE}/ingest/visual/", visual_payload(version, run_id="run-002"), format="json", **KEY)
    assert VisualResult.objects.count() == 2


@pytest.mark.parametrize("patch", [{"version": 999999}, {"verdict": "maybe"}, {"diff_ratio": 1.5}, {"diff_ratio": -0.1}])
def test_visual_validation_errors(ingest_client, task, patch):
    version = VersionFactory.create(task)
    res = ingest_client.post(f"{BASE}/ingest/visual/", visual_payload(version, **patch), format="json", **KEY)
    assert res.status_code == 400


def test_visual_results_listing(client_for, ingest_client, task, artist, outsider):
    version = VersionFactory.create(task)
    ingest_client.post(f"{BASE}/ingest/visual/", visual_payload(version), format="json", **KEY)
    assert client_for(artist).get(f"{BASE}/visual-results/?entity={task.entity_id}").json()["count"] == 1
    assert client_for(artist).get(f"{BASE}/visual-results/?version={version.id}").json()["results"][0]["verdict_label"] == "不合格"
    assert client_for(outsider).get(f"{BASE}/visual-results/?version={version.id}").json()["count"] == 0
