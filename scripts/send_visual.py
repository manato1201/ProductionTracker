#!/usr/bin/env python3
"""VisualRegressionQATool の評価結果を ProductionTracker に取り込む(POST /api/v1/ingest/visual/)。

入力は JSON ファイル。ツール側の出力形式は設計書に記載がないため、このスクリプトが受け取る形を決める:
  {"run_id": "...", "version": <ProductionTracker の版 ID>, "verdict": "pass"|"fail",
   "diff_ratio": 0.0132, "captured_at": "2026-10-11T10:00:00+09:00",
   "conditions": {"resolution": "1920x1080", "fixed_time": "...", "seed": 42}}
複数件は、この形のオブジェクトの配列でもよい。API キーは環境変数 INGEST_API_KEY で渡す。
同じ (run_id, version) の再送は上書きされ、重複しない。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from send_quality import post_json

REQUIRED = ("run_id", "version", "verdict", "diff_ratio", "captured_at")


def load_results(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else [data]
    for i, item in enumerate(items):
        missing = [k for k in REQUIRED if k not in item]
        if missing:
            raise ValueError(f"{i + 1} 件目に必須項目がありません: {', '.join(missing)}")
    return items


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", required=True, help="結果の JSON ファイル")
    p.add_argument("--url", default="http://localhost:8000/api/v1/ingest/visual/")
    args = p.parse_args(argv)

    try:
        items = load_results(args.file)
    except (OSError, ValueError) as e:
        print(f"入力エラー: {e}", file=sys.stderr)
        return 2
    api_key = os.environ.get("INGEST_API_KEY", "")
    if not api_key:
        print("環境変数 INGEST_API_KEY を設定してください。", file=sys.stderr)
        return 2

    failed = 0
    for item in items:
        status, body = post_json(args.url, api_key, item)
        label = f"run_id={item['run_id']} version={item['version']}"
        if status in (200, 201):
            print(f"{label}: HTTP {status}({'新規' if status == 201 else '上書き'})")
        else:
            failed += 1
            print(f"{label}: 失敗 HTTP {status} {body.get('detail', body)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
