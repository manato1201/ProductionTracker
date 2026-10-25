"""外部ツールの結果の取り込み。どちらも冪等(同じキーの再送は上書きで、重複させない)。"""

from collections import defaultdict

from django.db import transaction

from .models import Entity, QualityReport, Version, VisualResult
from .paths import match_entity, normalize_path


@transaction.atomic
def ingest_quality(project, scan_run_id: int, scanned_at, rows: list[dict]) -> dict:
    """(project, scan_run_id) 単位で置き換える。

    アセットパスは Entity.path との前方一致で突き合わせる。一致しないものも
    `entity=None` で保存し、元データの件数と一致するようにする(unmatched として返す)。
    """
    defects_by_path: dict[str, int] = defaultdict(int)
    for row in rows:
        defects_by_path[normalize_path(row["asset_path"])] += row["defects"]

    candidates = list(Entity.objects.filter(project=project).exclude(path="").values_list("id", "path"))

    existing = QualityReport.objects.filter(project=project, scan_run_id=scan_run_id)
    created = not existing.exists()
    existing.delete()

    reports, unmatched = [], []
    for path, defects in defects_by_path.items():
        entity_id = match_entity(path, candidates)
        if entity_id is None:
            unmatched.append(path)
        reports.append(
            QualityReport(
                project=project, entity_id=entity_id, scan_run_id=scan_run_id,
                asset_path=path, defects=defects, scanned_at=scanned_at,
            )
        )
    QualityReport.objects.bulk_create(reports)

    return {
        "created": created,
        "project": project.code,
        "scan_run_id": scan_run_id,
        "received": len(rows),
        "stored": len(reports),
        "matched": len(reports) - len(unmatched),
        "unmatched": sorted(unmatched),
        "defects_total": sum(defects_by_path.values()),
    }


def ingest_visual(*, run_id: str, version: Version, verdict: str, diff_ratio: float, captured_at, conditions: dict):
    """(run_id, version) 単位で上書き。戻り値は (結果, 新規か)。"""
    return VisualResult.objects.update_or_create(
        run_id=run_id,
        version=version,
        defaults={
            "verdict": verdict,
            "diff_ratio": diff_ratio,
            "captured_at": captured_at,
            "conditions": conditions,
        },
    )
