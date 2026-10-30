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
    d.tile(870, 285, "認証", "Session + CSRF / Token\nAccess JWT(任意)\nX-API-Key(取り込み専用)", "shield")
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
    d = Diagram(1600, 1040, "運用構成(方式 A)― 自分の PC の docker compose + Cloudflare Tunnel + Access")

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
            (2, "Access", ["許可した人だけが先へ進める。/admin も同じ入口。", "Django も JWT を検証できる(任意・未検証)"]),
            (3, "Tunnel", ["PC から外へ接続するだけ。PC の待受ポートは開けない。"]),
            (4, "frontend", ["Vite が /api などを web へ中継(開発用の構成)。"]),
            (5, "web → db", ["起動時に migrate。DB はボリュームに保存。"]),
        ],
        title="手順の説明", cols=2, row_h=66,
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
    d.box(gx, 270, gw, 90, "domain/", ["状態の文言・アイコン・日付の整形・モチーフ", "(ルールは持たない。表示だけ)"], "gray")
    d.box(gx, 390, gw, 110, "styles/", ["_tokens.scss が色・余白の唯一の出どころ", "→ CSS 変数 + MUI テーマ(tokens.module.scss)"], "gray")
    d.box(gx, 530, gw, 70, "*.test.ts(x)", ["Vitest + Testing Library"], "gray")
    d.note(gx, 640, "遷移の可否はサーバーが決める。\n画面は結果(409 / 403 と理由)を\n表示するだけ。", size=12.5)
    return d.svg()


def request_pipeline() -> str:
    d = Diagram(1600, 900, "1 本のリクエストが通る関門 ― 上から順に検査し、最初に失敗した所で止まる")
    ORANGE, PURPLE = "#e08a3c", "#8a6fd6"

    gates_top = [
        (160, "Cloudflare Access", "入口(許可した人だけ)\nJWT を付けて通す", "lock", "ログイン画面へ", GRAY),
        (460, "ミドルウェア", "NUL を弾く\nキャッシュ禁止を付ける", "gear", "400 NUL 文字", RED),
        (760, "認証", "Session+CSRF / Token\nAccess JWT / X-API-Key", "shield", "401 / 403 CSRF", RED),
        (1060, "レート制限", "ユーザー・ログイン\n・取り込み", "pulse", "429 throttled", RED),
        (1360, "入力の検証", "JSON だけ・型・範囲\n・サイズ上限", "braces", "415 / 400", RED),
    ]
    gates_bottom = [
        (1360, "見える範囲", "visible_* で最初に絞る", "list", "404(存在を明かさない)", RED),
        (1060, "権限", "役割(viewer は書けない)", "lock", "403 permission_denied", RED),
        (760, "業務ルール", "Task.transition_to\n遷移表→権限→条件", "gear", "409 / 403", RED),
        (460, "データベース", "一意制約・CHECK\n・行ロック", "database", "400 / 409(最後の砦)", RED),
    ]
    n = 1
    for x, title, sub, icon, reject, col in gates_top:
        d.tile(x, 250, title, sub, icon)
        d.step(n, x - 44, 214, color=BLUE)
        d.pill(x - text_w(reject) / 2, 352, reject, color=col)
        n += 1
    for x, title, sub, icon, reject, col in gates_bottom:
        d.tile(x, 620, title, sub, icon)
        d.step(n, x - 44, 584, color=BLUE)
        d.pill(x - text_w(reject) / 2, 722, reject, color=col)
        n += 1
    d.tile(160, 620, "成功", "200 / 201 + JSON", "check", accent="#3da86a")

    for (x1, *_), (x2, *_) in zip(gates_top, gates_top[1:]):
        d.edge([(x1 + 40, 250), (x2 - 40, 250)], "")
    d.edge([(1360, 384), (1360, 578)], "")
    for (x1, *_), (x2, *_) in zip(gates_bottom, gates_bottom[1:]):
        d.edge([(x1 - 40, 620), (x2 + 40, 620)], "")
    d.edge([(420, 620), (200, 620)], "")

    d.note(40, 140, "エッジ(Cloudflare)→ Django のミドルウェア・認証・制限 → DRF の検証・権限 → ドメイン(モデル)→ DB", color=INK, size=13.5, bold=True)
    d.note(40, 800, "凡例", bold=True, color=INK)
    d.pill(100, 783, "赤い札 = その関門で拒否されたときの応答", color=RED)
    d.note(40, 850, "どの関門も、通ったあとに前の関門へ戻らない。後ろの関門ほど、業務の意味に近い(ルール・DB)。\n前の関門ほど、安く・早く拒否できる(NUL・レート制限・認証)。", color=MUTED, size=12.5)
    return d.svg()


def text_w(s: str, size: float = 12.5) -> float:
    from diagram import text_width

    return (text_width(s, size) + 22) / 1.0


def auth_flow() -> str:
    d = Diagram(1600, 1010, "認証の経路 ― 誰が、どのヘッダで、どの認証クラスに届くか")
    d.tile(130, 230, "画面(ブラウザ)", "ログインして使う", "monitor")
    d.tile(130, 400, "Access を通った端末", "Cloudflare Access", "cloud", dashed=True)
    d.tile(130, 570, "DCC パネル(未実装)", "Houdini など", "plug", dashed=True)
    d.tile(130, 740, "外部ツール", "取り込みスクリプト", "terminal")

    d.group(420, 120, 640, 760, "Django: 認証クラスを上から順に試す", "REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']", "green")
    d.tile(740, 250, "SessionAuthentication401", "セッション + CSRF\n(未認証は 401)", "shield")
    d.tile(740, 410, "CloudflareAccessAuthentication", "JWT(RS256)の署名・発行者・宛先・期限\nメールで既存ユーザーに対応づけ", "lock", dashed=True)
    d.tile(740, 580, "TokenAuthentication", "Authorization: Token <ユーザー別>\n(期限なし・要確認)", "braces")
    d.tile(740, 750, "IngestApiKeyAuthentication", "X-API-Key(取り込み API 専用)\n定数時間で比較", "terminal")

    d.edge([(162, 230), (698, 230)], "Cookie sessionid + X-CSRFToken", label_at=0.5)
    d.edge([(162, 400), (676, 400)], "Cf-Access-Jwt-Assertion", color=GRAY, dashed=True, label_at=0.45)
    d.edge([(162, 570), (676, 570)], "Authorization: Token …", color=GRAY, dashed=True, label_at=0.5)
    d.edge([(162, 740), (676, 740)], "X-API-Key", label_at=0.5)

    d.tile(1330, 400, "request.user", "Django の User\n(役割はプロジェクトごと)", "person")
    d.tile(1330, 750, "IngestPrincipal", "ユーザーではない外部ツール\n(画面の API は呼べない)", "terminal")
    d.edge([(782, 250), (1100, 250), (1100, 400), (1298, 400)], "", label_at=0.5)
    d.edge([(812, 410), (1100, 410)], "", arrow=False)
    d.edge([(782, 580), (1100, 580), (1100, 400)], "", arrow=False)
    d.edge([(812, 750), (1298, 750)], "", label_at=0.5)

    d.step(1, 560, 200)
    d.step(2, 590, 372, color=GRAY)
    d.step(3, 590, 542, color=GRAY)
    d.step(4, 560, 712)

    d.group(1120, 880, 440, 100, "どれにも当たらない / 失敗", "", "red", dashed=True)
    d.note(1140, 935, "401: 認証情報なし・不正   403: Access は通ったが未登録 / CSRF 失敗", color=RED, size=12)
    d.note(40, 930, "ヘッダが無ければ次のクラスへ進む。ヘッダがあって不正なら、そこで 401(次へは進まない)。", color=MUTED, size=12.5)
    d.note(40, 960, "取り込み API は IngestApiKeyAuthentication だけ。セッションやトークンでは通らず、キーでは画面の API に入れない。", color=MUTED, size=12.5)
    return d.svg()


def data_model() -> str:
    d = Diagram(1600, 960, "データモデル ― テーブルと関係(太字 = 主要な項目、UK = 一意、FK = 外部キー)")

    def table(x, y, w, title, rows, color="blue"):
        d.box(x, y, w, 46 + 18 * len(rows), title, rows, color)

    table(40, 90, 330, "Project", ["code  UK(大文字小文字を区別しない)", "name", "start / due"], "blue")
    table(40, 290, 330, "ProjectMember", ["project  FK → Project", "user  FK → User", "role  reviewer / artist / viewer", "UK (project, user)"], "blue")
    table(40, 500, 330, "User(Django 標準)", ["username / email", "is_staff(管理者。承認はできない)"], "gray")

    table(450, 90, 340, "Entity(アセット)", ["project  FK", "name / kind(asset)/ status", "path(品質との突き合わせ用)", "UK (project, kind, name)"], "green")
    table(450, 330, 340, "Task", ["entity  FK / step  FK", "status  todo → … → done", "priority / due / estimate_h ≥ 0", "assignee  FK → User(SET NULL)", "UK (entity, step)"], "green")
    table(450, 610, 340, "Step(工程)", ["code  UK / name / order", "初期データはマイグレーション"], "gray")

    table(870, 330, 340, "Version", ["task  FK / number(タスク内の連番)", "status  draft/submitted/approved/rejected", "file_ref / thumb / comment / dcc", "created_by  FK / idempotency_key", "UK (task, number)"], "purple")
    table(870, 610, 340, "VisualResult", ["version  FK / run_id", "verdict / diff_ratio  0〜1", "captured_at / conditions", "UK (run_id, version)"], "purple")

    table(1290, 90, 290, "QualityReport", ["project  FK / entity  FK(NULL 可)", "scan_run_id / asset_path", "defects(bigint)/ scanned_at", "UK (project, run, path)"], "orange")
    table(1290, 440, 290, "Note", ["content_type + object_id", "author  FK / body", "対象 = Entity / Task / Version"], "orange")

    d.edge([(370, 140), (450, 140)], "1 : N", color=BLUE)
    d.edge([(205, 190), (205, 290)], "1 : N")
    d.edge([(205, 500), (205, 408)], "1 : N", arrow=False)
    d.edge([(620, 208), (620, 330)], "1 : N")
    d.edge([(620, 610), (620, 466)], "1 : N", arrow=False)
    d.edge([(790, 430), (870, 430)], "1 : N")
    d.edge([(1040, 466), (1040, 610)], "1 : N")
    d.edge([(790, 130), (1290, 130)], "1 : N(パスの前方一致)", color=GRAY, dashed=True, label_at=0.5)
    d.edge([(370, 560), (410, 560), (410, 450), (450, 450)], "assignee", color=GRAY, dashed=True, label_at=0.5)
    d.edge([(1290, 500), (1210, 440)], "GFK", color=GRAY, dashed=True, label_at=0.5)

    d.note(40, 720, "読み方", bold=True, color=INK)
    d.note(40, 745, "・1 つのアセットに、工程ごとに 1 つのタスク(UK (entity, step))。\n・版の番号はタスクの中で 1, 2, 3 …(行ロックで採番)。\n・品質・画面差分は取り込んだ結果の保存先(参照用。編集しない)。\n・ノートは外部キーでなく ContentType + id なので、\n  対象を消すと一緒に消えるよう GenericRelation を持たせてある。", color=MUTED, size=12.5)
    d.note(450, 800, "派生する値は保存しない(進捗・件数・期限切れ・次に行ける状態は計算する)。", color=MUTED, size=12.5)
    return d.svg()


def lecture_roadmap() -> str:
    d = Diagram(1600, 900, "講義の地図 ― 基礎から順に、最後は総合演習")
    cols = [
        ("基礎", "blue", 30, [("L01 Web の仕組み", "HTTP · REST · Cookie", "link"), ("L02 Python の基礎", "型 · クラス · 例外", "terminal"), ("L03 データベースと SQL", "キー · 索引 · トランザクション", "database")]),
        ("フレームワーク", "green", 350, [("L04 Django の基礎", "モデル · ORM · マイグレーション", "layers"), ("L05 Django REST framework", "シリアライザ · ViewSet · 認証", "braces")]),
        ("アルゴリズム", "purple", 670, [("L06 状態機械", "遷移表 · 全組み合わせ", "gear"), ("L07 文字列とパス", "正規化 · 最長前方一致", "link"), ("L08 並行制御と冪等性", "ロック · 一意制約", "lock"), ("L09 認証と暗号", "ハッシュ · JWT · 制限", "shield")]),
        ("フロントエンド", "orange", 990, [("L10 JavaScript / TypeScript", "非同期 · 型", "braces"), ("L11 React の基礎", "state · effect · フック", "layers"), ("L12 画面づくり", "CSS · Sass · アクセシビリティ", "palette"), ("L13 かんばん", "イベント · ドラッグ", "kanban")]),
        ("品質と運用", "red", 1310, [("L14 テスト", "pytest · Vitest", "check"), ("L15 スクリプトを読む", "シェル · Python", "terminal"), ("L16 運用", "Docker · 監視 · 安全", "box"), ("L17 総合演習", "機能を 1 つ足す", "file")]),
    ]
    for title, color, x, items in cols:
        h = 120 + 130 * len(items)
        d.group(x, 100, 260, h, title, "", color)
        for i, (t, sub, icon) in enumerate(items):
            d.tile(x + 130, 210 + i * 130, t, sub, icon)
    for x in (290, 610, 930, 1250):
        d.edge([(x, 330), (x + 60, 330)], "")
    d.note(40, 800, "読む順は L01 → L17。 基礎(青)が不安なら L01〜L03 から。 すでに Django / React を知っているなら、L06〜L09(アルゴリズム)と L14〜L16 から読んでもよい。", color=MUTED, size=13)
    d.note(40, 830, "各講義の最後に確認問題と答え。 ◆ 掲載したコードは、実行して確かめてある(backend/tracker/tests/test_docs.py)。", color=MUTED, size=13)
    return d.svg()


DIAGRAMS = {
    "architecture.svg": architecture,
    "transition-flow.svg": transition_flow,
    "ingest-flow.svg": ingest_flow,
    "operations.svg": operations,
    "code-map.svg": code_map,
    "request-pipeline.svg": request_pipeline,
    "auth-flow.svg": auth_flow,
    "data-model.svg": data_model,
    "lecture-roadmap.svg": lecture_roadmap,
}


if __name__ == "__main__":
    for name, fn in DIAGRAMS.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print("wrote", OUT / name)
