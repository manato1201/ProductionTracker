# 6. 困ったとき

症状 → 原因 → 確かめ方 → 直し方。**まずステータスコードと `code` を見る**(統一エラー形式なので、`code` で原因がほぼ決まる)。

## API / 画面
| 症状 | 原因 | 確かめる / 直す |
|---|---|---|
| 画面がログイン画面へ戻される | どれかの API が **401**(セッション切れ・未ログイン) | ブラウザの Network で 401 の API を探す。再ログイン。トークン・API キーのヘッダを付けていないか |
| **403** `CSRF Failed` | CSRF クッキーが無い / ヘッダ `X-CSRFToken` が無い / オリジンが信頼されていない | `GET /api/v1/auth/csrf/` で `csrftoken` クッキーが付くか。別のホスト名(Tunnel)で開いているなら `DJANGO_CSRF_TRUSTED_ORIGINS` と `DJANGO_ALLOWED_HOSTS` |
| **403** `permission_denied`(状態遷移) | 承認(レビュー待ち → 完了)をレビュアー以外が試した / 閲覧者 | プロジェクトの自分の役割(概要タブ)。管理画面でメンバーの役割を直す。**`is_staff` でも承認はできない** |
| **409** `invalid_transition` | 遷移表にない移動(例: 未着手 → 完了) | `next_statuses` に出ている状態だけ行ける。表は `Task.TRANSITIONS` |
| **409** `version_required` | 版が 1 つも無いのに「完了」 | 版を登録する。ルールを外すなら `REQUIRE_VERSION_FOR_COMPLETION=0` |
| **400** `validation_error` | 入力の誤り。`errors` に項目別の理由が入る | レスポンスの `detail`(先頭 1 件)と `errors` |
| **404** なのに、あるはずのデータ | **見える範囲の外**(プロジェクトのメンバーでない) | 管理画面でメンバーに入れる。管理者(`is_staff`)は全て見える |
| **429** `throttled`(ログイン) | 10 回/分を超えた | 1 分待つ。変えるなら `LOGIN_THROTTLE_RATE`。プロセスを再起動するとカウントが消える |
| **400** `NUL 文字(%00)は使えません` / `値が大きすぎます` | URL や JSON に NUL、bigint を超える数 | 送り手を直す(正しい入力ではない)。PostgreSQL は NUL を保存できず、通すと 500 になるため入口で弾いている |
| **415** `Unsupported media type` | JSON 以外(フォーム・multipart)で送った | `Content-Type: application/json` で送る |
| 一覧が 50 件で止まる | ページネーション(既定 50・上限 200) | `?page=2`、`?page_size=200`。`next` を辿る |
| 絞り込みが 400 | `?status=` などに、選択肢にない値 | 値の一覧がエラーメッセージに出る |
| 概要の「タスク」タブが、ドロワーでの変更後も古い | 再読み込みの合図が足りない(過去の不具合) | `OverviewPage` の `tasksRevision`。新しい画面でも「変更があった」ことを明示の値で伝える |

## 開発環境
| 症状 | 原因 | 直し方 |
|---|---|---|
| `Invalid HTTP_HOST header`(400) | `DJANGO_ALLOWED_HOSTS` に無いホスト名 | `.env` に追加。compose の `web` の healthcheck は `localhost` を使うので、**`localhost` を消さない** |
| Vite が `Blocked request. This host is not allowed` | Vite の `allowedHosts` | `VITE_ALLOWED_HOSTS` にホスト名を入れる |
| 起動時に `DJANGO_SECRET_KEY が未設定です` | `DJANGO_DEBUG=0` で鍵が空 | 開発は `DJANGO_DEBUG=1`。公開は強い鍵を設定 |
| `docker compose up` で `frontend` が起動しない | `web` が healthy にならない(`depends_on`) | `docker compose logs web`。DB の接続、マイグレーションのエラーを見る |
| `migrate` が `0003` で失敗 | 既存データが新しい制約に違反(`demo` と `DEMO` の両方、負の見積など) | 違反するデータを直してから再実行。本番は先にバックアップ |
| `npm ci` が失敗(Docker) | `package-lock.json` と `package.json` のずれ | `npm install` でロックを更新してコミット |
| ESLint を入れたい | `typescript-eslint` が TypeScript 7 に未対応 | [decisions.md](../decisions.md) 参照(TypeScript を下げる必要がある) |

## 取り込み
| 症状 | 原因 | 直し方 |
|---|---|---|
| **401** | `X-API-Key` が無い・違う、または鍵が 1 つも設定されていない | `INGEST_API_KEYS`(サーバー)と `INGEST_API_KEY`(スクリプトの環境変数)を合わせる。未設定は常に 401(安全側) |
| **400** `タイムゾーン付きで指定してください` | 時刻にタイムゾーンが無い | 送り手を直す。`send_quality.py` は `--naive-offset +09:00` |
| 品質タブに出ない / `unmatched` が多い | `Entity.path` と `asset_path` が前方一致しない(基準ディレクトリ・表記の違い) | レスポンスの `unmatched` を見て、アセットの `path` を直す。恒常的なずれは `paths.py` に対応表を足す |
| 再送したら件数が増えた? | 増えない(冪等)。同じ `(project, scan_run_id)` は置き換わる | レスポンスが **200**(新規は 201)になっているか |
| スクリプトの終了コードが 1(件数が一致しない) | 取り込み後の `defects_total` が元 DB の `COUNT(*)` と違う | 元 DB の表・列名の想定が違う可能性。`--defects-table` などで合わせる |
| 画面差分が 400 `存在しない版です` | `version` に ProductionTracker の **版の ID** を渡していない | 版の ID は `GET /versions/?task=` の `id` |

## 運用
| 症状 | 原因 / 確かめ方 | 直し方 |
|---|---|---|
| `/healthz` が 503 | DB に接続できない | `docker compose ps` / `logs db`。**DB 停止時に 503 になるのは仕様**(Hub が検知する) |
| `restore.sh` が「件数が一致しません」 | バックアップ後にデータが増えた(`.counts` は **取得時点**の件数) | 同じダンプから復元した直後に比べる。ダンプと `.counts` をセットで保管 |
| Sentry にイベントが来ない | DSN 未設定 / サンプリング / 無料枠超過 | `SENTRY_DSN`、`SENTRY_SAMPLE_RATE`。疎通は `/debug/sentry`(`VITE_SENTRY_DEBUG=1`)と `SENTRY_DEBUG_ENDPOINT_ENABLED=1` |
| ログにトークンが出ていないか不安 | アプリはリクエストヘッダをログしない | `docker compose logs web | grep -i token` で確認。Sentry へは `tracker/sentry.py` が除去 |

## それでも分からないとき
1. **再現する手順**を書き出す(どの画面・どのユーザー・どの操作)
2. ブラウザの Network で、失敗した API の **ステータスと `code` / `detail`** を見る
3. サーバーのログ(JSON、標準出力)を見る。500 なら例外のスタックトレースが出ている
4. `backend/tracker/tests/` に近いテストがあるか探す(仕様の確認)
5. 直したら、原因を [learning-log.md](../learning-log.md) に残す
