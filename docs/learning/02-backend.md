# 2. バックエンドの道案内

対象: `backend/`(Django 5.2 LTS + Django REST framework)。

## 1 本のリクエストが通る道
`POST /api/v1/tasks/12/transition/` を例に、上から順に通る場所:

| 段 | 場所 | 何をするか |
|---|---|---|
| 1 | `config/urls.py` | `SimpleRouter` が `TaskViewSet` に結びつける |
| 2 | 認証クラス(`settings.py` の `API_AUTHENTICATION_CLASSES`) | セッション(CSRF 検査つき)か、`Authorization: Token` で利用者を決める。無ければ **401** |
| 3 | `TaskViewSet.get_queryset` | `visible_tasks(user)` で **見えるタスクだけ** に絞り、`?status=` などで絞り込む。見えなければ **404** |
| 4 | `TaskViewSet.transition` | 入力 `{"to": ...}` を `TransitionSerializer` で検証(不正な値は **400**) |
| 5 | `select_for_update` | トランザクション内でタスクの行をロック(同時操作を直列に) |
| 6 | **`Task.transition_to`**(`models.py`) | 遷移表 → 権限 → 追加条件の順に検査。**ここが唯一のルール** |
| 7 | `TaskSerializer` | 最新のタスク(`next_statuses` を含む)を返す |
| 8 | `errors.exception_handler` | 例外を `{"code", "detail"}` に統一して返す |

> 図: [状態遷移の流れ](../diagrams/transition-flow.svg)

## 1. モデルとルール(`tracker/models.py`)
### 状態遷移
`Task.TRANSITIONS` が遷移表。`transition_to(to, user)` の検査の順序は固定:

1. 表にない → `InvalidTransition`(**409** `invalid_transition`)。誰が試しても同じ。
2. 書き込み権限が無い → `Forbidden`(**403**)。
3. レビュー待ち → 完了 は、レビュアーのみ → `Forbidden`(**403**)。**`is_staff` でも不可**。
4. 完了にするとき版が 1 つも無い → `RuleViolation`(**409** `version_required`)。`REQUIRE_VERSION_FOR_COMPLETION=0` で外せる。

`Version.transition_to` は別の遷移表(作成中 → 提出済み → 承認 / 却下)。承認・却下はレビュアーのみ。却下でタスクを自動で差し戻すかは `RETURN_TASK_ON_VERSION_REJECT`(既定は動かさない)。

### 役割と権限
判定は `Project.can_write_as(role, is_staff)` / `can_review_as(role)` の **2 つの静的メソッドだけ**。モデルの `can_write(user)` も、API が UI に返す `can_write` / `can_review` も、同じ関数を通る(ずれない)。

### 制約(DB が最後の砦)
`Project.code` の大文字小文字を区別しない一意、`Task(entity, step)` の一意、`Version(task, number)` の一意、`Version(created_by, idempotency_key)`(鍵があるときだけ)、`QualityReport(project, scan_run_id, asset_path)`、`VisualResult(run_id, version)`、CHECK(`estimate_h >= 0`、`diff_ratio` は 0〜1)。一覧は [er.md](../er.md)。

### ノート(`GenericForeignKey`)
`Note` は `content_type` + `object_id` で、Entity / Task / Version のどれにも付く。外部キーではないので、対象が消えても自動では消えない → 3 つのモデルに **`GenericRelation("Note")`** を足して連鎖削除にしている(消し忘れると孤児ノートが残る)。

## 2. 見える範囲と権限(`tracker/permissions.py`)
| 関数 | 役割 |
|---|---|
| `visible_projects(user)` | 管理者は全て、それ以外はメンバーのプロジェクト |
| `visible_entities / tasks / versions(user)` | 上のプロジェクトに属するものだけ |
| `require_write(user, project)` | 書き込めなければ `Forbidden`(403) |
| `IsIngestClient` | 取り込み API は `X-API-Key` で認証された外部ツールだけ |

**新しい API を作るときは、必ず `visible_*` から QuerySet を始める**(権限漏れの最大の原因を最初に塞ぐ)。

## 3. 入口で使う道具(`tracker/views.py`)
| 関数 | 役割 |
|---|---|
| `int_param(request, name)` | 整数のクエリ。不正は 400 |
| `choice_param(request, name, choices)` | 選択肢にある値だけ。タイプミスが「0 件」に見えないよう 400 にする |
| `project_q(request, prefix)` | `?project=` は id でもコードでも指定できる |
| `apply_ordering(...)` | `?ordering=` は **許可リストだけ**。同順位は id で固定(ページ送りがぶれない) |

一覧は全てページネーション(`StandardPagination`: 既定 50・上限 200)。

## 4. エラー(`tracker/errors.py`)
全てのエラーは `{"code": "...", "detail": "..."}`(検証エラーは `errors` も付く)。

| 状況 | HTTP | `code` |
|---|---|---|
| 未認証 / 認証失敗 | 401 | `not_authenticated` / `authentication_failed` |
| 権限なし・CSRF 失敗 | 403 | `permission_denied` |
| 見えない・無い | 404 | `not_found` |
| 入力の誤り・不正なクエリ | 400 | `validation_error` |
| 表にない遷移 | 409 | `invalid_transition` |
| 追加条件を満たさない | 409 | `version_required`(`RuleViolation` の code) |
| 同じ Idempotency-Key を別タスクに | 409 | `idempotency_conflict` |
| レート制限を超えた(ログイン・API・取り込み) | 429 | `throttled` |
| JSON 以外の本文 | 415 | `unsupported_media_type` |
| 想定外の例外 | 500 | `server_error`(Sentry に届く) |

業務ルール違反は `DomainError` のサブクラスを **モデル層から投げる**。HTTP への変換は `exception_handler` だけが担う(モデルは HTTP を知らない)。

## 5. 認証(`tracker/auth.py`、`tracker/cf_access.py`)
| 方式 | 用途 | 備考 |
|---|---|---|
| セッション + CSRF | 画面 | `SessionAuthentication401` で未認証を 401 にする。ログインも CSRF を検査(`views_auth.CsrfOnlyAuthentication`) |
| `Authorization: Token` | DCC パネルなど | `drf_create_token` で発行 |
| `X-API-Key` | 取り込み API **だけ** | 定数時間で比較。鍵が未設定なら常に 401(fail closed) |

差し替え方は [auth.md](../auth.md)。**Cloudflare Access(OIDC)の JWT** も、`tracker/cf_access.py` の認証クラスを足すだけで使える(任意・既定は無効)。点検の結果は [security.md](../security.md)。

## 6. 取り込み(`ingest.py` / `paths.py` / `views_ingest.py`)
- `ingest_quality`: `(project, scan_run_id)` の行を **全て置き換える**(冪等)。先にプロジェクトの行をロックして、同時再送を直列にする。
- `paths.match_entity`: 区切りを `/` にそろえ、大文字小文字を区別せず、`Entity.path` との **最長の前方一致**(`crate` と `crater` は別物)。
- 時刻はタイムゾーン付き必須(`AwareDateTimeField`)。黙って補わない。
- 図: [取り込みの流れ](../diagrams/ingest-flow.svg)。契約: [integration.md](../integration.md)。

## 7. 同時実行と冪等性
| 場面 | 手当て |
|---|---|
| タスクの状態遷移 | `select_for_update` で行をロック |
| 版番号の採番 | `Version.create_for_task` がタスク行をロックして `max(number)+1`。`(task, number)` の一意制約が最後の砦 |
| 版の再送 | `Idempotency-Key`(ユーザーごとに一意)。同じ鍵は同じ版を 200 で返す |
| 取り込みの再送 | `(project, scan_run_id)` / `(run_id, version)` で上書き |

SQLite では `select_for_update` は何もしない。同時実行の検証は PostgreSQL でしかできない(テストは両方で走らせている)。

## 8. DB とマイグレーション
- 変更したら `python manage.py makemigrations tracker -n <短い名前>` → **生成物を必ず読む** → `migrate`。
- 制約を足すマイグレーション(`0003`)は、**既存データが違反していると失敗する**。本番は先にバックアップ → 別 DB で試す([operations.md](../operations.md))。
- `0002_default_steps` はデータマイグレーション(工程の初期データ)。`get_or_create` で何度流しても同じ。
- 古いマイグレーションは書き換えない(適用済みの DB と食い違う)。

## 9. 設定(`config/settings.py`)
全て環境変数から読む(一覧は `.env.example`)。覚えておく 3 つ:
- `DJANGO_DEBUG=0` で `DJANGO_SECRET_KEY` が空だと **起動しない**。
- `POSTGRES_HOST` があれば PostgreSQL、無ければ SQLite。
- テストは `config/settings_test.py`(MD5 ハッシュ・ログインの制限を緩める・`testserver` を許可)。

## 10. 補助コマンド・管理画面
| 何を | どう |
|---|---|
| デモデータ | `python manage.py seed_demo --password <pw>` |
| 管理者を作る | `ensure_admin`(環境変数 `DJANGO_SUPERUSER_*`)または `createsuperuser` |
| API トークン | `python manage.py drf_create_token <ユーザー名>`(`-r` で再発行) |
| メンバーの追加・役割の変更 | 管理画面 `/admin/` → プロジェクト → メンバー(API・画面は無い) |

## 読む順序(おすすめ)
1. `tests/test_task_transitions.py`(仕様がそのまま書いてある)
2. `models.py` の `Task` → `transition_to`
3. `views.py` の `TaskViewSet`(`get_queryset` と `transition`)
4. `serializers.py` の `TaskSerializer`
5. `permissions.py` → `errors.py`
6. `ingest.py` → `paths.py`

## 確認
- [ ] 「未着手 → 完了」を試すと何が返る? どのコードがそれを決める?(→ 409 `invalid_transition`、`Task.transition_to`)
- [ ] `visible_tasks` を使わずに `Task.objects.all()` から始めたビューを作ると、何が起きる?(→ 見えないはずのタスクが見える)
- [ ] `is_staff` のユーザーが「完了」にできないのは、どの関数のどの条件?
- [ ] 新しいエンドポイントを足すとき、テストで最低限確かめる 4 つのステータスコードは?(→ 401 / 403 / 404 / 正常)
