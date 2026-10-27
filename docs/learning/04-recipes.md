# 4. 拡張レシピ

「足したい」から逆引きする手順書。**各レシピの「変更する場所」は、実際にコードを検索して洗い出した一覧**(レシピ A は、使い捨てのコピーで手順どおりに実行して通ることを確認済み)。
どのレシピも最後に **必ず全部を流す**:

```bash
cd backend  && pytest -q && ruff check .                 # SQLite
cd backend  && POSTGRES_HOST=... POSTGRES_DB=... pytest -q   # PostgreSQL でも(README 参照)
cd frontend && npx tsc --noEmit && npm test && npm run build
```

> **コンパイラを味方にする**: フロントで型を変えたら `npx tsc --noEmit` が、直すべき場所を全部教えてくれる(テスト用のデータ生成関数も含む)。先に型を変えて、赤くなった所を順に直す。

---

## A. タスクに項目を足す(例: `description`)
**変更する場所**
1. `backend/tracker/models.py` — `Task` に `description = models.TextField("説明", blank=True)`
2. `cd backend && python manage.py makemigrations tracker -n task_description` → **生成された `0004_...py` を読む**(`AddField` だけのはず)→ `migrate`
3. `backend/tracker/serializers.py` — `TaskSerializer.Meta.fields` に `"description"` を足す(書き込み可・読み取り専用は `read_only_fields` で決める)
4. `backend/tracker/tests/test_api_entities_tasks.py` — 作成と PATCH で往復するテストを足す(下のひな形)
5. `frontend/src/api/types.ts` — `Task` に `description: string`
6. `npx tsc --noEmit` — **`src/components/Board.test.tsx` のテスト用データ(`task()` 関数)が赤くなる**ので `description: ""` を足す(実際に起きた)
7. 画面に出す: `components/TaskDrawer.tsx` の詳細 `<dl>` に 1 行、入力は `components/Dialogs.tsx` の `TaskFormDialog` に `TextField`、`api/endpoints.ts` の `tasks.create` / `tasks.update` の引数の型に足す
8. `docs/er.md`(モデル)を直す

**テストのひな形**
```python
def test_task_description_roundtrip(client_for, artist, entity, step):
    c = client_for(artist)
    res = c.post(f"{BASE}/tasks/", {"entity": entity.id, "step": step.id, "description": "メモ"}, format="json")
    assert res.status_code == 201 and res.json()["description"] == "メモ"
    patched = c.patch(f"{BASE}/tasks/{res.json()['id']}/", {"description": "直した"}, format="json")
    assert patched.json()["description"] == "直した"
```
**注意**: 既存の行がある列を `null=False` で足すときは、`default` か `blank=True`(文字列)を付ける。`status` のように **PATCH で直接変えさせない** 項目は `read_only_fields` に入れる。

---

## B. タスクの状態を 1 つ足す(例: 「保留 `blocked`」)
遷移ルールをモデルに集約し、**状態の一覧は 1 か所から導く**ようにしてあるので、変更は少ない。
(使い捨てのコピーで実行した結果: サーバーでは `models.py` を直すだけで、落ちたのは下の「テスト」の 4 件だけ。フロントでは `tsc` が数か所を指摘する。ASCII モチーフの追加後は、`domain/motif.ts` の対応表も `Record` なので指摘される。)

**サーバー**
1. `models.py` — `Task.Status` に `BLOCKED = "blocked", "保留"`。`Task.TRANSITIONS` に、**行き先と戻り先の両方**を足す(例: 進行中 → 保留、保留 → 進行中)。`next_statuses` は表から自動で出る
2. `makemigrations`(`choices` の変更。`AlterField` になる)→ 読む → `migrate`
3. (任意)`management/commands/seed_demo.py` のデモデータ

> プロジェクトの状態別の件数(`n_<状態>` の集計と `task_counts`)は `Task.Status` から導いているので、**足さなくてよい**。

**フロント**
4. `api/types.ts` — `TaskStatus` と `TaskCounts` に `blocked`
5. `domain/status.tsx` — `TASK_STATUS_META`(文言とアイコン)に足す。**`TASK_STATUSES`(並び順 = かんばんの列順 = Shift+←/→ の隣)は META の定義順から自動で決まる**ので、**入れたい位置に書く**(`Record<TaskStatus, …>` なので、書き忘れると型エラー)
5b. `domain/motif.ts` — `GROWTH_STAGE_OF_STATUS`(`Record<TaskStatus, …>`)に、空の列に出す植物の段階を足す(**書き忘れると型エラー**。段階を増やすなら `GROWTH_FRAMES` に 2 コマ追加。寸法は幅 9 × 高さ 4)
6. `styles/_tokens.scss` — `status-blocked` を **ライトとダークの両方**に(背景に対し 4.5:1 以上)
7. `styles/global.scss` — `.status--blocked` と `.stack-bar__seg--blocked` と `.ascii-motif--blocked`、かんばんの `grid-template-columns: repeat(4, …)` を **列数に合わせる**
8. `pages/MyTasksPage.tsx` — 既定ビューの `status` 一覧に入れるか決める

> **型が教えてくれないもの**(手で探す): 6・7 の SCSS、8 の文字列。`grep -rn "in_progress" frontend/src backend/tracker` で同じ書かれ方をしている場所を洗い出す。

**テスト**(赤くなるものを直す)
9. `tests/test_task_transitions.py` — 全組み合わせの表(`ALLOWED`)に新しい遷移を足す。**組み合わせは自動で増える**(`for a in S for b in S`)ので、足し忘れは必ずテストが落ちる
10. `tests/test_api_entities_tasks.py`(`next_statuses`)、`tests/test_api_projects.py`(件数の辞書に `blocked`)
11. フロント: `Board.test.tsx` の `task()` の遷移表、`StackedBar.test.tsx` の件数、`status.test.ts` の並び順(`tsc` が指摘する)

**文書**: [ui-rules.md](../ui-rules.md) の状態の表、[er.md](../er.md)、[状態遷移の図](../diagrams/transition-flow.svg)(必要なら)。

**注意**: 状態を足すと「承認」「完了の条件」など **追加ルールの置き場所**(`transition_to` の 2・3 段目)も見直す。新しい状態に入る/出るときの権限が必要なら、そこに足す。

---

## C. 新しい API を足す(例: 参照のみ / 作成)
1. `serializers.py` — 入出力の形(出力専用なら `read_only_fields = fields`)
2. `views.py` — `ViewSet` を作る。**`get_queryset` は必ず `visible_*` から始める**(`permissions.py`。足りなければここに足す)。絞り込みは `int_param` / `choice_param`、並べ替えは `apply_ordering`(許可リスト)
3. 書き込みは `require_write(request.user, project)`。業務ルールは **ビューでなくモデルのメソッド**に置く(違反は `DomainError` のサブクラスを投げる)
4. `config/urls.py` — `router.register(...)`
5. `tests/` — **401(未認証)/ 404(他人のデータ)/ 403(閲覧者)/ 400(不正な入力)/ 正常** の 5 つを最低限
6. `frontend/src/api/endpoints.ts` と `types.ts`(URL はここだけに書く)
7. [README](../../README.md) の API 表と、[integration.md](../integration.md)(外部が使うなら)

---

## D. 新しい画面を足す
1. `pages/NewPage.tsx` — データは `useResource`。**「読み込み中(スケルトン)→ 空(`EmptyState`)→ 失敗(`ErrorNotice`)→ 通常」の 4 状態**を必ず作る
2. `App.tsx` — `<Route>` を足す(認証が要る画面は `RequireAuth` の内側)
3. ナビに出すなら `components/AppLayout.tsx` の `NavItem`
4. 状態の表示は `StatusLabel`、日付は `formatDate`、数字は `.num`、色は `--pt-*`
5. **幅 360px で横スクロールが出ない**ことをブラウザで確認(開発者ツールのレスポンシブ表示)。ライト・ダークの両方
6. 部品に切り出せるロジック(判定・整形)は、画面でなく `domain/` か部品に置いて Vitest を書く

---

## E. 新しい取り込み口を足す(例: ビルド結果)
1. `serializers.py` — 入力用シリアライザ。**時刻は `AwareDateTimeField`**(タイムゾーン必須)
2. **冪等性の鍵を決める**(何が同じ送信かを一意に表せるか)。モデルに `UniqueConstraint`、`ingest.py` に `update_or_create` か「置き換え」の関数
3. `views_ingest.py` — `IngestBase` を継承した `post`(認証は `X-API-Key`、CSRF の対象外)
4. `config/urls.py` — `ingest/<名前>/`
5. `scripts/send_<名前>.py` — 鍵は **環境変数**(コマンドラインに書かない)。**元データと取り込み結果の件数を突き合わせ、不一致なら終了コード 1**
6. `tests/test_ingest.py` — **キーなし 401 / 再送で重複しない / 不正入力 400 / 件数一致**
7. [integration.md](../integration.md) と [取り込みの流れ](../diagrams/ingest-flow.svg)(`docs/diagrams/build.py`)

---

## F. 役割を足す(例: `producer`)
1. `models.py` — `ProjectMember.Role` に追加。**書き込める役割なら `WRITER_ROLES` に入れる**。承認できる役割を増やすなら `Project.can_review_as`(**判定はこの 2 つの関数だけ**)
2. `makemigrations`(`choices`)
3. フロント `api/types.ts` の `Role`。文言はサーバーの `role_label` が返すので、画面の変更は基本なし
4. テスト: `tests/test_api_projects.py` の「フラグがモデルの判定と常に一致する」テストに新しい役割を足す

---

## G. `shot`(ショット)に対応する
`Entity.kind` は既にある。**API が `asset` 以外を 400 で拒否している**(`EntitySerializer.validate_kind`)のが唯一の制限。
1. `validate_kind` を外す(または許可する値を増やす)
2. 一意制約は `(project, kind, name)` なので、同名のアセットとショットは共存できる
3. 画面: アセット一覧の絞り込み(`?kind=`)と、作成フォームの種別選択
4. `tests/test_api_entities_tasks.py` の `test_entity_shot_is_not_supported_yet` を、新しい仕様に書き換える

---

## H. 認証を差し替える(外部 ID 基盤)
[auth.md](../auth.md) の「差し替え口」。`BaseAuthentication` を継承したクラスを書き、環境変数 `API_AUTHENTICATION_CLASSES` に足す。ビューや権限の変更は不要(役割は `User` に紐づく)。

---

## 変更を出す前のチェックリスト
- [ ] 変更に対応するテストを **先に** 書いた(バグ修正は、まず再現するテストを赤にしてから直した)
- [ ] `visible_*` を通さずにデータを返していない
- [ ] 業務ルールをビュー / 画面に書いていない(モデルに置いた)
- [ ] 画面の新しい表示は「色 + アイコン + 文字」、ライト・ダーク・360px で確認した
- [ ] マイグレーションを読んだ(既存データで失敗しないか)
- [ ] 資料を直した([er.md](../er.md)・[integration.md](../integration.md)・この章・図)
