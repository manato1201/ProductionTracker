#!/usr/bin/env python3
"""AssetDataInsightSuite の insight.db を ProductionTracker に取り込む(POST /api/v1/ingest/quality/)。

標準ライブラリのみ。API キーはコマンドラインではなく環境変数 INGEST_API_KEY で渡す(履歴・ps に残さない)。

前提(設計書にスキーマの記載がないため、実データで要確認):
  scan_runs(<id>, <scanned_at>)  と  defect_records(<scan_run_id>, <asset_path>) が 1 欠陥 = 1 行
  列名・表名は --*-column / --*-table で変えられる。

終了コード: 0 = 取り込み成功かつ欠陥件数が元の DB と一致 / 1 = 不一致・失敗 / 2 = 引数・入力の誤り
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _ident(name: str) -> str:
    """表名・列名は識別子のみ許可(SQL に埋め込むため)。"""
    if not name.replace("_", "").isalnum():
        raise ValueError(f"不正な識別子です: {name!r}")
    return name


def build_quality_payload(
    db_path: str,
    project: str,
    scan_run_id: int | None = None,
    *,
    runs_table: str = "scan_runs",
    run_id_column: str = "id",
    scanned_at_column: str = "scanned_at",
    defects_table: str = "defect_records",
    defect_run_column: str = "scan_run_id",
    path_column: str = "asset_path",
) -> tuple[dict, int]:
    """(送信する本文, 元 DB の欠陥件数)を返す。scan_run_id 省略時は最新の実行。"""
    runs, run_id_col, scanned_col = _ident(runs_table), _ident(run_id_column), _ident(scanned_at_column)
    defects, defect_run, path_col = _ident(defects_table), _ident(defect_run_column), _ident(path_column)

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # 元データは読み取り専用で開く
    try:
        if scan_run_id is None:
            row = con.execute(f"SELECT {run_id_col}, {scanned_col} FROM {runs} ORDER BY {scanned_col} DESC, {run_id_col} DESC LIMIT 1").fetchone()
        else:
            row = con.execute(f"SELECT {run_id_col}, {scanned_col} FROM {runs} WHERE {run_id_col} = ?", (scan_run_id,)).fetchone()
        if row is None:
            raise LookupError("対象のスキャン実行が insight.db に見つかりません。")
        run_id, scanned_at = row
        rows = con.execute(
            f"SELECT {path_col}, COUNT(*) FROM {defects} WHERE {defect_run} = ? GROUP BY {path_col} ORDER BY {path_col}", (run_id,)
        ).fetchall()
        total = con.execute(f"SELECT COUNT(*) FROM {defects} WHERE {defect_run} = ?", (run_id,)).fetchone()[0]
    finally:
        con.close()

    payload = {
        "project": project,
        "scan_run_id": int(run_id),
        "scanned_at": _as_iso(scanned_at),
        "results": [{"asset_path": path, "defects": int(count)} for path, count in rows],
    }
    return payload, int(total)


def _as_iso(value) -> str:
    """ISO 8601 文字列か UNIX 秒を ISO 8601(タイムゾーン付き)にする。時刻帯の無い文字列は UTC とみなす。"""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


def post_json(url: str, api_key: str, payload: dict, timeout: float = 30.0) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, {"detail": e.reason}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", required=True, help="insight.db のパス")
    p.add_argument("--project", required=True, help="ProductionTracker のプロジェクトコード")
    p.add_argument("--url", default="http://localhost:8000/api/v1/ingest/quality/")
    p.add_argument("--scan-run-id", type=int, help="省略時は最新の実行")
    p.add_argument("--dry-run", action="store_true", help="送信せず、本文の要約だけ表示する")
    for flag, default in [
        ("runs-table", "scan_runs"), ("run-id-column", "id"), ("scanned-at-column", "scanned_at"),
        ("defects-table", "defect_records"), ("defect-run-column", "scan_run_id"), ("path-column", "asset_path"),
    ]:
        p.add_argument(f"--{flag}", default=default)
    args = p.parse_args(argv)

    try:
        payload, source_total = build_quality_payload(
            args.db, args.project, args.scan_run_id,
            runs_table=args.runs_table, run_id_column=args.run_id_column, scanned_at_column=args.scanned_at_column,
            defects_table=args.defects_table, defect_run_column=args.defect_run_column, path_column=args.path_column,
        )
    except (sqlite3.Error, LookupError, ValueError) as e:
        print(f"入力エラー: {e}", file=sys.stderr)
        return 2

    print(f"scan_run_id={payload['scan_run_id']} アセットパス {len(payload['results'])} 件 / 欠陥 {source_total} 件(元 DB)")
    if args.dry_run:
        return 0

    api_key = os.environ.get("INGEST_API_KEY", "")
    if not api_key:
        print("環境変数 INGEST_API_KEY を設定してください。", file=sys.stderr)
        return 2
    status, body = post_json(args.url, api_key, payload)
    if status not in (200, 201):
        print(f"送信に失敗しました: HTTP {status} {body.get('detail', body)}", file=sys.stderr)
        return 1
    print(f"HTTP {status}: 保存 {body['stored']} 件(アセットに対応 {body['matched']} / 未対応 {len(body['unmatched'])})、欠陥 {body['defects_total']} 件")
    for path in body["unmatched"]:
        print(f"  未対応のパス: {path}")
    if body["defects_total"] != source_total:
        print(f"件数が一致しません: 元 {source_total} / 取り込み {body['defects_total']}", file=sys.stderr)
        return 1
    print("件数一致: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
