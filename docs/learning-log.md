# 学習ログ(各スキルで詰まった点)

実装中に実際に引っかかったことの記録。新しいものを上に足す。

## Django / DRF
- **未認証が 401 でなく 403 になる。** DRF は認証クラスが `authenticate_header()` を返さないと、未認証・認証失敗を 403 に変える。`SessionAuthentication` を継承して `authenticate_header` を足し、画面側が 401 を見てログイン画面へ戻せるようにした(`tracker/auth.py`)。ログイン用の CSRF だけ検査するクラスでも同じ。
- **`force_authenticate` は認証クラスを素通りする。** 「画面の利用者(セッション)は取り込み API を呼べない」を `force_authenticate` で試すと、認証クラスが動かず 401 でなく 403(権限クラスで拒否)になる。実際のセッションを使う `force_login` で試すのが正しい。
- **`select_for_update` は SQLite では何もしない。** 版番号の連番(タスク行をロック)は PostgreSQL でしか効果を検証できない。テストを SQLite と PostgreSQL 16 の両方で通した(同時実行そのものの負荷試験はしていない)。`(task, number)` の一意制約を最後の砦にしてある。
- **`UniqueConstraint` に `condition=`(鍵が NULL でないときだけ一意)**で、Idempotency-Key を「鍵があるときだけユーザーごとに一意」にできた。NULL を許す一意制約は DB によって扱いが違うので、条件付きにして意図を明示した。
- 遷移ルールをモデルのメソッドに集約すると、API・テスト・(将来の)管理画面が同じルールを通る。**全 4×4 の組み合わせ表を parametrize** でテストしたので、表を変えたら必ずテストが落ちる(設計書の「全遷移の表」のテスト)。

## pytest / factory_boy
- `PostGenerationMethodCall("set_password")` + `skip_postgeneration_save = True` だと、**パスワードが DB に保存されない**。ログインのテストが 401 になり、原因はファクトリだった。`_create` で `create_user` を呼ぶ形にした。
- 設定を `config.settings_test` に分けた。`DJANGO_SECRET_KEY` 未設定でも起動する分岐を本体に入れず、テスト用モジュールで許可する。

## React / React Router
- 画面の状態(開いているタスク)は `?task=ID` に持たせると、共有・戻るボタン・Esc で閉じる、が URL だけで済む。
- 取得フックは「古い応答を捨てる」(連番で判定)だけで、フィルタを素早く切り替えても表示がぶれなかった。TanStack Query は入れていない(規模的に不要と判断。かんばんの先行更新と巻き戻しは自前で数十行)。

## MUI
- **AppBar の z-index がドロワーを覆った。** 固定の AppBar(`zIndex: drawer + 1`)の下に、右から出すタスクのドロワーの上端(題名・閉じるボタン)が隠れていた。スクリーンショットで気づいた。ドロワーを `zIndex: modal` にして解決。
- 狭い幅(360px)で、タスクの行の右端(優先度・状態・期日)が縮まず **374px まで横にはみ出した**。ブラウザで全画面の `scrollWidth` を計測して発覚。行を縦に積む指定を足した。

## Sass
- デザイントークンの出どころを 1 つにするため、`_tokens.scss` に Sass マップで定義 → CSS 変数(`--pt-*`)として出力し、同じ値を `tokens.module.scss` の `:export` で JS(MUI テーマ)にも渡した。ライト/ダークは `data-theme` と `prefers-color-scheme` の両方に対応。
- 色のコントラストは目視でなく計算で確認した(8 色 × 3 背景 × 2 テーマ、全て 4.5:1 以上)。

## Sentry
- **`@sentry/react` v11 に `sendDefaultPii` が無い。** 代わりに `dataCollection`(userInfo / cookies / httpHeaders / httpBodies / urlQueryParams を個別に指定)。型チェックで気づいた。
- Sentry に実際にイベントが届くことは、DSN が無く確認できていない。代わりに、**送信の直前(トランスポート)を差し替えて**、Django の意図的な例外が 1 件捕捉され、Authorization / X-API-Key / Cookie が含まれないことを確認した。React 側は `scrubEvent` を単体テストで確認。

## Vite / TypeScript / Vitest
- `vite.config.ts` で `process.env` を使うと、`@types/node` が無く型エラー。
- fetch のモックで同じ `Response` を 2 回返すと、2 回目に本文が読めない(使い捨て)。`mockImplementation` で毎回作る。
- 並べ替えや絞り込みのチップは、`aria-pressed` を付けるとテストでも画面読み上げでも状態が分かる。

## ドラッグ&ドロップ
- ポインタ操作と、キーボード・タッチの代替操作を**同じ関数(`onMove`)に流す**と、拒否されたときの巻き戻しとトーストが 1 か所で済む。
- ドロップ前に遷移の可否を UI で判断せず、サーバーの 409/403 を信じて戻す(設計書の方針)。そのぶん「どの遷移が可能か」は `next_statuses` でサーバーから受け取る。

## Docker
- この開発環境には Docker のデーモンがなく、`docker compose config` による構文確認までしかできていない。`docker compose up` での起動、DB 停止時の `/healthz`(代わりに PostgreSQL を直接止めて確認済み)は、手元の PC での確認が必要。
