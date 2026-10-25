#!/usr/bin/env python3
"""docs/diagrams/*.svg を作り直す。  使い方:  python docs/diagrams/build.py

図を直したいときは、ここを編集して再実行する(SVG を手で編集しない)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from diagram import BLUE, INK, MUTED, RED, Diagram  # noqa: E402

OUT = Path(__file__).parent
GRAY = "#8a94a6"
GREEN = "#3da86a"


def architecture() -> str:
    d = Diagram(1600, 1290, "ProductionTracker のシステム構成")

    # --- 利用者 ---
    d.tile(110, 375, "ユーザー", "ブラウザから使う", "person")

    # --- 画面 / API / データ ---
    d.group(250, 130, 360, 490, "画面 (frontend)", "Vite · React 19 · TypeScript", "blue")
    d.tile(430, 245, "画面とルーティング", "React Router\npages / components", "layers")
    d.tile(430, 385, "見た目", "MUI 7 + Sass\nデザイントークン", "palette")
    d.tile(430, 525, "API クライアント", "fetch · CSRF ヘッダ\n401 でログインへ", "plug")

    d.group(740, 130, 520, 490, "API (backend)", "Django 5.2 LTS · DRF · /api/v1", "green")
    d.tile(870, 285, "認証", "Session + CSRF / Token\nX-API-Key(取り込み専用)", "shield")
    d.tile(1130, 285, "業務ルール", "状態遷移・権限\ntracker/models.py", "gear")
    d.tile(870, 475, "取り込み", "冪等 · パス前方一致\ntracker/ingest.py", "terminal")
    d.tile(1130, 475, "監視", "/healthz · JSON ログ", "pulse")

    d.group(1340, 130, 230, 490, "データ", "PostgreSQL 16", "purple")
    d.tile(1455, 375, "PostgreSQL", "一意制約 · CHECK\nvolume: pgdata", "database")

    d.edge([(142, 375), (250, 375)], "HTTPS")
    d.edge([(610, 385), (740, 385)], "REST/JSON")
    d.edge([(1260, 375), (1340, 375)], "SQL")

    # --- 連携ツール(左下) ---
    d.group(24, 670, 220, 590, "連携ツール(自作)", "", "gray")
    d.tile(134, 780, "AssetDataInsightSuite", "send_quality.py", "file")
    d.tile(134, 905, "VisualRegressionQATool", "send_visual.py", "monitor")
    d.tile(134, 1030, "ToolOrchestrationHub", "registry.yaml", "pulse")
    d.tile(134, 1155, "DCC パネル(未実装)", "Houdini など", "plug", dashed=True)

    d.edge([(166, 780), (800, 780), (800, 620)], "POST /ingest/quality · X-API-Key", label_at=0.45)
    d.edge([(166, 905), (850, 905), (850, 620)], "POST /ingest/visual · X-API-Key", label_at=0.45)
    d.edge([(166, 1030), (1000, 1030), (1000, 620)], "GET /healthz(認証なし)", color=GRAY, dashed=True, label_at=0.45)
    d.edge(
        [(166, 1155), (1180, 1155), (1180, 620)],
        "POST /versions/ · Token + Idempotency-Key", color=GRAY, dashed=True, label_at=0.45,
    )

    # --- 観測と保全(右下) ---
    d.tile(1340, 820, "Sentry", "Django + React\n個人情報は送らない", "bug")
    d.tile(1490, 820, "バックアップ", "pg_dump · 毎日\nrestore.sh", "box")
    d.edge([(1340, 788), (1340, 710), (1230, 710), (1230, 620)], "例外", color=GRAY, dashed=True, label_at=0.45)
    d.edge([(1455, 620), (1455, 710), (1490, 710), (1490, 788)], "pg_dump", color=GRAY, dashed=True, label_at=0.45)

    # --- 凡例 ---
    d.note(1270, 1050, "凡例", bold=True, color=INK)
    d.edge([(1270, 1075), (1330, 1075)], "")
    d.note(1340, 1079, "通常のリクエスト")
    d.edge([(1270, 1100), (1330, 1100)], "", color=GRAY, dashed=True)
    d.note(1340, 1104, "補助(監視・保全・未実装の連携)")
    d.note(1270, 1135, "タイルの点線 = 未実装(docs/decisions.md)", color=MUTED, size=11.5)
    return d.svg()


def steplist(d, x, y, w, items, title="手順の説明", cols=2, row_h=66, color="gray"):
    """番号つきの説明欄。items = [(番号, 見出し, [説明の行...]), ...]"""
    rows = -(-len(items) // cols)
    d.group(x, y, w, rows * row_h + 44, title, "", color)
    col_w = (w - 40) / cols
    for i, (n, head, lines) in enumerate(items):
        cx = x + 34 + (i // rows) * col_w
        cy = y + 46 + (i % rows) * row_h
        d.step(n, cx, cy)
        d.note(cx + 24, cy + 5, head, color=INK, bold=True, size=13.5)
        for j, line in enumerate(lines):
            d.note(cx + 24, cy + 23 + j * 17, line, color=MUTED, size=12)


def transition_flow() -> str:
    d = Diagram(1600, 960, "タスクの状態遷移 ― かんばんで列を動かしたときの流れ")

    d.tile(110, 290, "ユーザー", "", "person")
    d.group(250, 130, 340, 370, "ブラウザ (React)", "", "blue")
    d.tile(420, 290, "かんばん画面", "@dnd-kit", "kanban")
    d.step(2, 278, 196)
    d.note(298, 201, "「完了」へなら確認モーダル", size=12.5, color=INK)
    d.step(3, 278, 226)
    d.note(298, 231, "画面を先に動かす(楽観的更新)", size=12.5, color=INK)

    d.group(760, 130, 520, 370, "サーバー (Django)", "", "green")
    d.tile(870, 290, "API", "セッション + CSRF", "braces")
    d.tile(1140, 290, "Task.transition_to", "tracker/models.py", "gear")

    d.group(1350, 130, 220, 370, "データ", "", "purple")
    d.tile(1460, 290, "PostgreSQL", "", "database")

    d.edge([(142, 290), (250, 290)], "")
    d.step(1, 196, 290)
    d.edge([(452, 290), (838, 290)], "POST /tasks/{id}/transition/ {to}", label_at=0.5)
    d.step(4, 645, 262)
    d.edge([(902, 290), (1108, 290)], "行をロックして呼ぶ", label_at=0.5)
    d.step(5, 1005, 262)
    d.step(6, 1172, 262)
    d.edge([(1172, 290), (1428, 290)], "UPDATE status", label_at=0.58)
    d.step(7, 1300, 262)

    # 成功 / 失敗の戻り道
    d.edge([(850, 372), (850, 415), (440, 415), (440, 372)], "200 + 最新のタスク", label_at=0.5)
    d.edge([(900, 372), (900, 455), (400, 455), (400, 372)], "409 / 403 + {code, detail}", color=RED, dashed=True, label_at=0.5, label_color=RED)
    d.step(8, 850, 400)
    d.step(8, 900, 440, color=RED)
    d.edge([(250, 485), (110, 485), (110, 372)], "トースト", color=GRAY, dashed=True, label_at=0.55)
    d.step(9, 110, 440)

    steplist(
        d, 24, 540, 1552,
        [
            (1, "ドロップ", ["ドラッグ・「⋮」メニュー・Shift+←/→ のどれでも、", "同じ処理(onMove)に流れる"]),
            (2, "確認", ["「完了」にするときだけ確認モーダル。", "版が無ければ警告を出す"]),
            (3, "先に動かす", ["元の状態を覚えたうえで、画面だけ先に更新する。", "拒否されたらこの状態へ戻す"]),
            (4, "リクエスト", ["遷移の可否は画面で判断せず、サーバーに任せる。", "本文は {\"to\": \"review\"} など"]),
            (5, "排他", ["トランザクション内でタスクの行をロック", "(select_for_update)。同時操作を直列にする"]),
            (6, "検査(この順)", ["① 遷移表 → 409 invalid_transition", "② 権限 → 403(承認はレビュアーのみ)  ③ 版が無い → 409 version_required"]),
            (7, "保存", ["全ての検査を通ったときだけ status を更新"]),
            (8, "応答", ["成功: 200 + 最新のタスク(次に行ける状態も入る)", "失敗: 409 / 403 + {\"code\", \"detail\"}"]),
            (9, "表示", ["成功はトースト。失敗は元の列へ戻し、", "サーバーの detail(理由)をそのままトーストで出す"]),
        ],
        title="手順の説明", cols=2, row_h=68,
    )
    return d.svg()


def ingest_flow() -> str:
    d = Diagram(1600, 1000, "外部ツールの結果の取り込み ― 品質スキャン(AssetDataInsightSuite)の場合")

    d.group(30, 120, 520, 330, "ツール側(自分の PC)", "", "gray")
    d.tile(130, 260, "insight.db", "AssetDataInsightSuite", "file")
    d.tile(400, 260, "send_quality.py", "scripts/", "terminal")
    d.group(600, 120, 520, 330, "ProductionTracker API", "", "green")
    d.tile(700, 260, "鍵の検査", "X-API-Key", "shield")
    d.tile(1010, 260, "パスの突き合わせ", "tracker/paths.py", "link")
    d.group(1170, 120, 190, 330, "データ", "", "purple")
    d.tile(1265, 260, "PostgreSQL", "", "database")
    d.group(1400, 120, 170, 330, "画面", "", "blue")
    d.tile(1485, 260, "品質タブ", "", "list")

    d.edge([(162, 260), (368, 260)], "読み取り専用", label_at=0.5)
    d.step(1, 265, 232)
    d.step(2, 400, 218)
    d.edge([(432, 260), (668, 260)], "POST /ingest/quality/", label_at=0.5)
    d.step(3, 550, 232)
    d.step(4, 700, 218)
    d.edge([(732, 260), (978, 260)], "認証 OK", label_at=0.5)
    d.step(5, 1010, 218)
    d.edge([(1042, 260), (1233, 260)], "置き換え", label_at=0.5)
    d.step(6, 1137, 232)
    d.edge([(1297, 260), (1453, 260)], "", dashed=True, color=GRAY)
    d.step(9, 1375, 232)

    d.edge([(700, 372), (700, 410), (400, 410), (400, 372)], "201 / 200 + 集計結果", label_at=0.5)
    d.step(7, 735, 395)
    d.step(8, 365, 395)
    d.note(60, 440, "件数を突き合わせる(不一致なら終了コード 1)", size=12.5, color=INK)

    steplist(
        d, 24, 500, 1552,
        [
            (1, "読む", ["insight.db を読み取り専用で開き、最新のスキャン実行を選ぶ。", "元データは書き換えない"]),
            (2, "集計", ["アセットのパスごとに欠陥の数を数える。", "時刻にタイムゾーンが無ければ止まる(--naive-offset で明示)"]),
            (3, "送る", ["POST /api/v1/ingest/quality/ に X-API-Key を付ける。", "鍵は環境変数 INGEST_API_KEY(コマンドラインに書かない)"]),
            (4, "鍵の検査", ["定数時間で比較。無ければ・違えば 401。", "鍵が 1 つも設定されていなければ常に 401(fail closed)"]),
            (5, "突き合わせ", ["区切りを / にそろえ、大文字小文字を区別せず、", "Entity.path との最長の前方一致(crate と crater は別物)"]),
            (6, "保存(冪等)", ["(project, scan_run_id) の行を全て置き換える。再送しても重複しない。", "対応するアセットが無いパスも entity = NULL で残す"]),
            (7, "応答", ["新規は 201、再送(上書き)は 200。", "stored / matched / unmatched / defects_total を返す"]),
            (8, "件数の突き合わせ", ["defects_total と、元 DB の COUNT(*) を比べる。", "一致しなければ終了コード 1(検証チェックリストの項目)"]),
            (9, "表示", ["アセット詳細の「品質」タブ。", "取得日時(スキャン実行の日時と取り込み日時)を固定表示"]),
        ],
        title="手順の説明", cols=2, row_h=68,
    )
    return d.svg()


def operations() -> str:
    d = Diagram(1600, 1000, "運用構成(方式 A)― 自分の PC の docker compose + Cloudflare Tunnel + Access")

    d.tile(110, 300, "外出先の端末", "ブラウザ", "monitor")
    d.group(230, 130, 430, 380, "Cloudflare", "未検証(実環境が必要)", "orange", dashed=True)
    d.tile(350, 300, "Access", "ログインした人だけ通す", "lock", dashed=True)
    d.tile(540, 300, "Tunnel", "cloudflared(PC から外へ接続)", "cloud", dashed=True)

    d.group(740, 110, 830, 460, "自分の PC(WSL2 / Docker)", "電源が入っている間だけ動く", "gray")
    d.group(770, 170, 770, 370, "docker compose", "127.0.0.1 にだけ公開", "blue")
    d.tile(880, 350, "frontend", "Vite :5173", "monitor")
    d.tile(1140, 350, "web", "Django :8000", "gear")
    d.tile(1420, 350, "db", "PostgreSQL · pgdata", "database")

    d.edge([(142, 300), (230, 300)], "HTTPS")
    d.step(1, 186, 268)
    d.edge([(382, 300), (508, 300)], "")
    d.step(2, 445, 300)
    d.edge([(572, 300), (740, 300), (740, 350), (848, 350)], "", label_at=0.5)
    d.step(3, 700, 300)
    d.edge([(912, 350), (1108, 350)], "/api /admin をプロキシ", label_at=0.5)
    d.step(4, 1010, 318)
    d.edge([(1172, 350), (1388, 350)], "SQL", label_at=0.5)
    d.step(5, 1280, 318)

    d.tile(950, 700, "ToolOrchestrationHub", "GET /healthz を監視", "pulse")
    d.tile(1180, 700, "backups/", "pg_dump 毎日(0600)", "box")
    d.tile(1410, 700, "R2(外部)", "rclone · 未検証", "cloud", dashed=True)
    d.tile(720, 700, "Sentry", "エラーのみ・個人情報なし", "bug")
    d.edge([(950, 668), (950, 610), (1160, 610), (1160, 540)], "GET /healthz", color=GRAY, dashed=True, label_at=0.6)
    d.edge([(1180, 668), (1180, 640), (1420, 640), (1420, 540)], "pg_dump", color=GRAY, dashed=True, label_at=0.55)
    d.edge([(1212, 700), (1378, 700)], "rclone copy", color=GRAY, dashed=True)
    d.edge([(720, 668), (720, 590), (1100, 590), (1100, 540)], "例外", color=GRAY, dashed=True, label_at=0.3)

    steplist(
        d, 24, 780, 1552,
        [
            (1, "端末から", ["https で Cloudflare に入る。"]),
            (2, "Access", ["許可した人だけが先へ進める。/admin も同じ入口。"]),
            (3, "Tunnel", ["PC から外へ接続するだけ。PC の待受ポートは開けない。"]),
            (4, "frontend", ["Vite が /api などを web へ中継(開発用の構成)。"]),
            (5, "web → db", ["起動時に migrate。DB はボリュームに保存。"]),
        ],
        title="手順の説明", cols=2, row_h=52,
    )
    return d.svg()


def code_map() -> str:
    d = Diagram(1600, 1020, "コードの地図 ― どこに何があるか、呼び出しの向き")

    # --- backend ---
    d.group(30, 110, 760, 880, "backend/  Django + DRF", "呼び出しは上から下へ", "green")
    bx, bw = 70, 330
    d.box(bx, 170, bw, 70, "config/urls.py", ["/api/v1 · /healthz · /admin のルーティング"], "green")
    d.box(bx, 290, bw, 90, "tracker/views.py", ["入口。絞り込み・並べ替えの検証、", "権限の確認、HTTP の組み立て"], "green")
    d.box(bx, 430, bw, 70, "tracker/serializers.py", ["入力の検証と、出力の整形"], "green")
    d.box(bx, 550, bw, 130, "tracker/models.py", ["データと「ルール」の置き場所", "Task.transition_to(遷移表・権限・条件)", "Version.transition_to / Project.can_*"], "green")
    d.box(bx, 730, bw, 70, "tracker/migrations/", ["スキーマの履歴(前方のみ)"], "green")
    d.tile(235, 905, "PostgreSQL", "", "database", size=56)
    d.edge([(235, 240), (235, 290)], "")
    d.edge([(235, 380), (235, 430)], "")
    d.edge([(235, 500), (235, 550)], "")
    d.edge([(235, 680), (235, 730)], "")
    d.edge([(235, 800), (235, 876)], "")

    sx, sw = 450, 310
    d.box(sx, 170, sw, 70, "tracker/permissions.py", ["見える範囲(visible_*)・書き込み権限"], "gray")
    d.box(sx, 270, sw, 70, "tracker/errors.py", ["統一エラー {code, detail} と業務の例外"], "gray")
    d.box(sx, 370, sw, 70, "tracker/auth.py", ["認証クラス(Session / X-API-Key)"], "gray")
    d.box(sx, 470, sw, 90, "tracker/ingest.py + paths.py", ["取り込み(冪等)と、", "パスの正規化・前方一致"], "gray")
    d.box(sx, 590, sw, 70, "tracker/health.py · sentry.py", ["/healthz と、Sentry へ送る前の除去"], "gray")
    d.box(sx, 690, sw, 110, "tracker/tests/", ["pytest + factory_boy。遷移表は", "4×4 の全組み合わせをテスト"], "gray")
    d.edge([(400, 335), (450, 205)], "", color=GRAY, dashed=True)
    d.edge([(400, 335), (450, 305)], "", color=GRAY, dashed=True)
    d.note(sx, 835, "views は permissions / errors / ingest を使い、\nルールは models だけが持つ。", size=12.5)

    # --- frontend ---
    d.group(830, 110, 740, 880, "frontend/src  React + MUI", "呼び出しは上から下へ", "blue")
    fx, fw = 870, 330
    d.box(fx, 170, fw, 70, "main.tsx → App.tsx", ["起動(テーマ・トースト・認証)とルーティング"], "blue")
    d.box(fx, 290, fw, 90, "pages/", ["画面。データの取得と、画面ごとの状態", "(ProjectLayout が project / members を共有)"], "blue")
    d.box(fx, 430, fw, 90, "components/", ["再利用する部品", "Board · TaskDrawer · Dialogs · FilterChip …"], "blue")
    d.box(fx, 570, fw, 90, "hooks/", ["useResource(取得) · useTaskTransition", "(遷移 + 確認 + トースト) · useTaskParam"], "blue")
    d.box(fx, 710, fw, 90, "api/", ["client.ts(fetch · CSRF · 統一エラー)", "endpoints.ts(URL を 1 か所に) · types.ts"], "blue")
    d.tile(1035, 905, "backend /api/v1", "", "braces", size=56)
    for y0, y1 in [(240, 290), (380, 430), (520, 570), (660, 710), (800, 876)]:
        d.edge([(1035, y0), (1035, y1)], "")

    gx, gw = 1230, 310
    d.box(gx, 170, gw, 70, "context/", ["Auth · Toast · ThemeMode"], "gray")
    d.box(gx, 270, gw, 90, "domain/", ["状態の文言・アイコン・日付の整形", "(ルールは持たない。表示だけ)"], "gray")
    d.box(gx, 390, gw, 110, "styles/", ["_tokens.scss が色・余白の唯一の出どころ", "→ CSS 変数 + MUI テーマ(tokens.module.scss)"], "gray")
    d.box(gx, 530, gw, 70, "*.test.ts(x)", ["Vitest + Testing Library"], "gray")
    d.note(gx, 640, "遷移の可否はサーバーが決める。\n画面は結果(409 / 403 と理由)を\n表示するだけ。", size=12.5)
    return d.svg()


DIAGRAMS = {
    "architecture.svg": architecture,
    "transition-flow.svg": transition_flow,
    "ingest-flow.svg": ingest_flow,
    "operations.svg": operations,
    "code-map.svg": code_map,
}


if __name__ == "__main__":
    for name, fn in DIAGRAMS.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print("wrote", OUT / name)
