# 8. セキュリティとデータベースの見方

機能を足す・直すときに、**何を確かめるか**の手引き。結果の一覧は [security.md](../security.md)・[database.md](../database.md)。この章は「自分で点検できる」ようになるための読み方。

## 考え方(3 つ)
1. **点検は文章でなく、テストにする。** 一度見たきりの点検は、次の変更で崩れる。「全エンドポイントは未認証で 401」のように、**新しい機能が自動で対象になる**テストにすると、足し忘れが起きない。
2. **正しい入力の次に、壊れた入力を試す。** 500 が出たら、それは不具合(4xx で拒否するか、正しく扱う)。DB が違うと落ち方も違う(PostgreSQL は NUL 文字、SQLite は巨大な整数)ので、**両方の DB で流す**。
3. **最小権限。** 誰に・何を許すかを表にして、表のとおりにテストする。表にないものは許さない(許可リスト)。

## OWASP API Top 10 を、このアプリで見る
| リスク | 自分で確かめる問い | 見る場所 |
|---|---|---|
| API1 オブジェクト単位の認可 | **他のプロジェクトの ID** を URL に入れたら、読めて・書ける? | `permissions.py` の `visible_*`、`test_objects_of_another_project_are_invisible` |
| API2 認証 | ログインを何度も間違えたら? トークンは盗まれたらどうなる? | `views_auth.py`(制限)、`cf_access.py` |
| API3 プロパティ単位の認可 | PATCH に `status` や `id` を混ぜたら書き換わる? 応答に余計な個人情報は? | `serializers.py` の `read_only_fields` |
| API4 資源の消費 | 巨大な本文・1 秒に 1000 回・`page_size=1000000` は? | `settings.py` のレート、`StandardPagination`、`MAX_JSON_CHARS` |
| API5 機能単位の認可 | 閲覧者が書ける? アーティストが承認できる? | `test_authorization_matrix` |
| API7 SSRF | サーバーが、利用者の渡した URL を取りに行く場所はある? | (無い。`thumbnail` は保存するだけ) |
| API8 設定 | エラーにスタックトレースが出る? 応答がキャッシュされる? | `middleware.py`、`check --deploy` |
| API9 在庫 | 知らないうちに増えたエンドポイントは? | `test_every_api_endpoint_requires_authentication` |

## 新しい API を足したときの手順(セキュリティ)
1. `get_queryset` は **`visible_*` から始める**(API1)。
2. 入力は **シリアライザで検証**する。読み取り専用の項目は `read_only_fields`(API3)。文字列は NUL を拒否、数は範囲、自由記述は上限(API4)。
3. 書き込みは `require_write`、承認のような特別な操作はモデルのメソッドに権限の検査を置く(API5)。
4. `test_security_audit.py` を流す。**未認証で 401 でなければ落ちる**。公開するなら `PUBLIC` に **理由つき**で足す(API9)。
5. ロール別の期待を、`CASES` に 1 行足す(表のとおりか)。
6. 壊れた入力を `test_robustness.py` に足す(500 にならないか)。

## 401・403・404 をどう選ぶか
| 迷ったら | 答え |
|---|---|
| ログインしていない | 401 |
| ログインしているが、その操作はできない役割 | 403 |
| その対象が**見えるはずのない人** | 404(存在を教えない)。作成時に、見えない親を指定したなら 400 |
| ルール上できない状態 | 409(権限より先に判定してよい) |

## データベースの見方(SQL の指針)
| 問い | どうやって確かめるか |
|---|---|
| そのクエリは索引を使っている? | `python manage.py explain_queries`(実データ)、`tests/test_query_plans.py`(SQLite) |
| その列に索引は要る? | **値の種類が多い**列(ID・日付・名前)に。状態のように数種類しかない列の単独の索引は要らない |
| 列に関数をかけて検索している? | 索引にも**同じ関数**をかける(`LOWER(code)` の索引には `Lower("code")` で検索)。さもないと索引が効かない |
| ページ送りの一覧に `ORDER BY` は? | `apply_ordering`。`test_every_list_queryset_is_ordered` が強制 |
| `COUNT` は NULL を数える? | **列を指定した `COUNT(列)` は数えない**。「無いものは 0 件」にしたいなら、そのまま使う。行数を数えたいなら `COUNT(*)` |
| 派生する値を保存していない? | 進捗・件数のような**計算できる値は保存しない**(更新のたびにずれる) |
| 一意にしたいものは DB の制約? | アプリの検査だけでは同時実行で破れる。**DB の一意制約が最後の砦** |

## 実行計画の読み方(PostgreSQL)
```
Bitmap Heap Scan on tracker_task        ← 索引で見つけた行だけを読む(良い)
  Recheck Cond: (entity_id = 1)
  ->  Bitmap Index Scan on tracker_task_entity_id_...   ← 索引を使っている
Seq Scan on tracker_task                ← 全件走査。大きな表で出たら要注意
Sort                                    ← 並べ替え。索引の順序で済ませられないか
```
小さな表では、索引があっても `Seq Scan` が選ばれることがある(全件を読むほうが速いため)。**判断は実データの件数で**する。

## 演習
1. `PUBLIC`(未認証で通すもの)に、新しいエンドポイントを足すとき、何を書かなければならないか。(→ 理由。レビューで説明できること)
2. 閲覧者を `viewer` から `artist` に変えると、`test_authorization_matrix` のどの行が落ちるか。予想してから試す。
3. `Task.status` 単独の索引を戻すと、どのテストが落ちるか。なぜそのテストが要るのか説明する。
4. `?q=` の検索が遅くなったと想定して、先頭が `%` の `LIKE` を速くする方法を調べる。(→ `pg_trgm`。ただし [database.md](../database.md) の「許容していること」の前提を確認してから)
5. Cloudflare Access のテスト(`test_cf_access.py`)で、`alg=none` のトークンが通ると何が起きるか、言葉で説明する。
