# 用語集

講義と実践ガイドに出てくる用語を、分野ごとに並べました。右端は、詳しく説明している回です。
このアプリに固有の用語(「アセット」「工程」「版」など)は、最初にまとめてあります。

## このアプリの言葉
| 用語 | 意味 | 詳しくは |
|---|---|---|
| プロジェクト(Project) | 作品や案件の単位。メンバーと役割を持つ | [L00](L00-intro.md) |
| アセット / Entity | 作る対象(例: 木箱・主人公)。`path`(例 `assets/props/crate`)を持つ | [er.md](../er.md) |
| 工程 / Step | 作業の種類(例: モデリング・FX) | [er.md](../er.md) |
| タスク(Task) | 「あるアセットの、ある工程」の作業。**状態**を持つ | [L06](L06-state-machine.md) |
| 版(Version) | 提出された成果物の版(v1, v2…)。レビューの対象 | [er.md](../er.md) |
| ノート(Note) | タスクや版へのコメント | [er.md](../er.md) |
| 状態(Status) | タスクの進み具合: 未着手 / 進行中 / レビュー / 完了 | [L06](L06-state-machine.md) |
| 役割(Role) | プロジェクト内の立場: アーティスト / レビュアー / 閲覧者 | [L05](L05-drf.md) |
| 取り込み(Ingest) | 外部ツールの結果を API で受け取ること | [L08](L08-concurrency.md)・[L15](L15-scripts.md) |
| 品質レポート | AssetDataInsightSuite が出す、アセットごとの欠陥件数 | [integration.md](../integration.md) |
| 視覚検査の結果 | VisualRegressionQATool の合否と差分率 | [integration.md](../integration.md) |
| モチーフ | 空の列に飾る ASCII の植物(種→芽→花→実) | [L12](L12-ui-css.md) |

## Web・通信
| 用語 | 意味 | 詳しくは |
|---|---|---|
| HTTP | Web の通信の約束事。リクエストとレスポンスの組 | [L01](L01-web.md) |
| URL | 資源の場所を示す文字列(スキーム・ホスト・パス・クエリ) | [L01](L01-web.md) |
| メソッド | GET(読む)・POST(作る)・PATCH(一部直す)・PUT(置き換え)・DELETE(消す) | [L01](L01-web.md) |
| ステータスコード | 結果を示す数字。2xx 成功 / 4xx クライアントの誤り / 5xx サーバーの誤り | [L01](L01-web.md) |
| ヘッダ | リクエスト/レスポンスの付加情報(`Content-Type`・`Authorization` など) | [L01](L01-web.md) |
| JSON | データを書く文字列の形式。ほぼすべての API で使われる | [L01](L01-web.md)・[L10](L10-javascript-typescript.md) |
| REST | 資源を URL で表し、メソッドで操作する API の流儀 | [L01](L01-web.md) |
| API | プログラムから使う窓口 | [L01](L01-web.md) |
| エンドポイント | API の個々の URL | [L05](L05-drf.md) |
| ページネーション | 一覧を一定の件数ずつ返すこと | [L05](L05-drf.md) |
| Cookie | ブラウザが覚え、リクエストに自動で付ける小さな情報 | [L01](L01-web.md) |
| セッション | ログイン状態をサーバー側で覚える仕組み | [L01](L01-web.md)・[L09](L09-security-crypto.md) |
| CORS | 別のオリジンからのリクエストをブラウザが許すかの約束 | [L01](L01-web.md) |
| オリジン | スキーム + ホスト + ポートの組 | [L01](L01-web.md) |
| プロキシ | 通信を中継するもの。リバースプロキシはサーバーの前に立つ | [L16](L16-operations.md) |
| TLS / HTTPS | 通信を暗号化し、相手を確かめる仕組み | [L09](L09-security-crypto.md) |
| DNS | 名前(ドメイン)から IP アドレスを引く仕組み | [L01](L01-web.md) |
| キャッシュ | 同じ応答を使い回すこと。`Cache-Control` で制御 | [L16](L16-operations.md) |

## Python
| 用語 | 意味 | 詳しくは |
|---|---|---|
| 型(type) | 値の種類(整数・文字列・リスト…) | [L02](L02-python.md) |
| 関数 | 名前を付けた処理のまとまり | [L02](L02-python.md) |
| クラス / インスタンス | 設計図 / それから作った実体 | [L02](L02-python.md) |
| 例外 | 異常を伝える仕組み。`try/except` で受ける | [L02](L02-python.md) |
| 内包表記 | リストなどを 1 行で作る書き方 | [L02](L02-python.md) |
| ジェネレータ | 値を 1 つずつ作る(まとめて持たない) | [L02](L02-python.md) |
| `with` 文 | 後始末つきの処理(ファイルを閉じる等) | [L02](L02-python.md) |
| デコレータ | 関数やクラスに機能を足す `@名前` | [L02](L02-python.md) |
| 型ヒント | 値の型の注釈。実行時には強制されない | [L02](L02-python.md) |
| 仮想環境(venv) | プロジェクトごとの独立した Python 環境 | [L00](L00-intro.md) |
| `argparse` | コマンドライン引数を読む標準ライブラリ | [L15](L15-scripts.md) |

## データベース
| 用語 | 意味 | 詳しくは |
|---|---|---|
| RDB | 表(テーブル)でデータを持つ DB | [L03](L03-database.md) |
| テーブル / 行 / 列 | 表 / 1 件のデータ / 項目 | [L03](L03-database.md) |
| 主キー | 行を一意に決める値(通常は `id`) | [L03](L03-database.md) |
| 外部キー | 他の表の行を指す列 | [L03](L03-database.md) |
| 正規化 | 重複を避けて表を分けること | [L03](L03-database.md) |
| SQL | DB を操作する言語(SELECT / INSERT / UPDATE / DELETE) | [L03](L03-database.md) |
| JOIN | 複数の表をキーでつなぐ | [L03](L03-database.md) |
| 索引(インデックス) | 検索を速くする仕組み。書き込みは少し遅くなる | [L03](L03-database.md) |
| 一意制約(UNIQUE) | 同じ値を 2 つ入れさせない | [L03](L03-database.md)・[L08](L08-concurrency.md) |
| CHECK 制約 | 値が条件を満たすことを DB が保証する | [L03](L03-database.md) |
| トランザクション | 「全部成功するか、全部なかったことになる」まとまり | [L03](L03-database.md)・[L08](L08-concurrency.md) |
| ACID | トランザクションの 4 性質(原子性・一貫性・分離性・永続性) | [L03](L03-database.md) |
| ロック | 同時に触らせないための排他(`select_for_update`) | [L08](L08-concurrency.md) |
| N+1 問題 | 一覧 1 回 + 各行ごとに追加の問い合わせが走る性能問題 | [L04](L04-django.md) |
| 実行計画 | DB が検索をどう行うかの手順(`EXPLAIN`) | [L03](L03-database.md) |
| SQL インジェクション | 入力が SQL として解釈されてしまう脆弱性 | [L03](L03-database.md)・[L15](L15-scripts.md) |
| マイグレーション | DB の構造変更を記録・適用する仕組み | [L04](L04-django.md) |
| ダンプ / リストア | DB の書き出し / 書き戻し | [L15](L15-scripts.md) |

## Django / DRF
| 用語 | 意味 | 詳しくは |
|---|---|---|
| MTV | Model(データ)・Template(表示)・View(処理)の分担 | [L04](L04-django.md) |
| ORM | DB の行を Python のオブジェクトとして扱う仕組み | [L04](L04-django.md) |
| QuerySet | まだ実行されていない DB への問い合わせ(遅延評価) | [L04](L04-django.md) |
| ミドルウェア | リクエスト/レスポンスの前後に挟まる共通処理 | [L04](L04-django.md) |
| settings | 設定を集めたモジュール | [L04](L04-django.md)・[L16](L16-operations.md) |
| シリアライザ | オブジェクト ⇔ JSON の変換と入力検査 | [L05](L05-drf.md) |
| ViewSet / Router | 一式の操作をまとめた View / URL を自動で作る仕組み | [L05](L05-drf.md) |
| 認証(authentication) | 「誰か」を確かめる | [L05](L05-drf.md)・[L09](L09-security-crypto.md) |
| 認可 / 権限(permission) | 「その人に許されているか」を確かめる | [L05](L05-drf.md) |
| スロットル | 回数制限(レート制限) | [L05](L05-drf.md)・[L09](L09-security-crypto.md) |
| fixture / factory | テストの準備 / テストデータを作る道具 | [L14](L14-testing.md) |

## アルゴリズム・設計
| 用語 | 意味 | 詳しくは |
|---|---|---|
| 状態機械(FSM) | 状態と、許される遷移の表で振る舞いを定める | [L06](L06-state-machine.md) |
| 遷移表 | 「どの状態からどこへ行けるか」の一覧 | [L06](L06-state-machine.md) |
| 到達可能性 | ある状態から別の状態へたどり着けるか(幅優先探索) | [L06](L06-state-machine.md) |
| 不変条件 | 常に成り立つべき性質 | [L06](L06-state-machine.md) |
| 正規化(パス) | 表記の揺れをそろえる | [L07](L07-strings-paths.md) |
| 最長一致 | 前方一致のうち最も長いものを選ぶ | [L07](L07-strings-paths.md) |
| トライ木 | 文字列を 1 文字ずつ枝分かれで持つ木 | [L07](L07-strings-paths.md) |
| 計算量(O 記法) | 入力が増えたとき、時間や領域がどう増えるか | [L07](L07-strings-paths.md) |
| Unicode / NFC / NFD | 文字の規格 / 結合済みの形 / 分解した形 | [L07](L07-strings-paths.md)・[L17](L17-capstone.md) |
| 競合状態(race condition) | 同時実行で結果が実行順に左右されること | [L08](L08-concurrency.md) |
| 冪等(べきとう) | 同じ操作を何回行っても、結果が 1 回と同じ | [L08](L08-concurrency.md) |
| Idempotency-Key | 同じ要求の再送を見分けるための、クライアントが付ける印 | [L08](L08-concurrency.md) |
| 楽観的更新 | 成功を見込んで先に画面を更新し、失敗したら戻す | [L13](L13-kanban.md) |
| 楽観的ロック / 悲観的ロック | 衝突を後で検出 / 先に排他する | [L08](L08-concurrency.md) |
| 性質ベーステスト | 「どんな入力でも成り立つ性質」を検査する | [L14](L14-testing.md) |
| 差分テスト | 元の実装と新しい実装の結果を突き合わせる | [L17](L17-capstone.md) |
| ファズ | でたらめな入力を大量にぶつけて、落ちないか確かめる | [L14](L14-testing.md) |
| 回帰テスト | 直したバグが再発しないようにするテスト | [L14](L14-testing.md) |

## 認証・暗号・セキュリティ
| 用語 | 意味 | 詳しくは |
|---|---|---|
| ハッシュ | データから固定長の「指紋」を作る一方向の関数 | [L09](L09-security-crypto.md) |
| ソルト | パスワードのハッシュに混ぜる、ユーザーごとのランダム値 | [L09](L09-security-crypto.md) |
| PBKDF2 | 何度も繰り返してハッシュを遅くする、パスワード向けの方式 | [L09](L09-security-crypto.md) |
| 定数時間比較 | 一致までの時間で情報が漏れない比較(`hmac.compare_digest`) | [L09](L09-security-crypto.md) |
| HMAC | 鍵つきのハッシュ。改ざんの検出に使う | [L09](L09-security-crypto.md) |
| JWT | 署名つきの情報(ヘッダ.本体.署名)。Cloudflare Access が使う | [L09](L09-security-crypto.md) |
| RS256 | 公開鍵方式の署名(秘密鍵で署名、公開鍵で検証) | [L09](L09-security-crypto.md) |
| JWKS | 検証用の公開鍵の一覧 | [L09](L09-security-crypto.md) |
| CSRF | ログイン中の利用者に、意図しない操作をさせる攻撃 | [L09](L09-security-crypto.md) |
| XSS | 悪意あるスクリプトを画面に差し込む攻撃 | [security.md](../security.md) |
| SameSite | Cookie を別サイトからの送信に付けるかの設定 | [L01](L01-web.md) |
| レート制限 | 一定時間のリクエスト数に上限を設ける | [L09](L09-security-crypto.md) |
| 最小権限 | 必要な権限だけを与える | [L15](L15-scripts.md)・[L16](L16-operations.md) |
| fail closed | 迷ったら閉じる(危険な設定なら起動しない・拒否する) | [L16](L16-operations.md) |
| OWASP API Top 10 | API の代表的な脆弱性の一覧 | [L16](L16-operations.md)・[security.md](../security.md) |
| 秘密情報 | パスワード・API キー・鍵・トークン。Git やログに出さない | [L15](L15-scripts.md)・[L16](L16-operations.md) |

## JavaScript / TypeScript / React
| 用語 | 意味 | 詳しくは |
|---|---|---|
| `const` / `let` | 再代入できない / できる変数 | [L10](L10-javascript-typescript.md) |
| アロー関数 | `(x) => x + 1` の書き方 | [L10](L10-javascript-typescript.md) |
| 分割代入 / スプレッド | 値を取り出す / 展開する(`{ ...a }`) | [L10](L10-javascript-typescript.md) |
| Promise / `async` / `await` | 非同期の結果 / それを書きやすくする構文 | [L10](L10-javascript-typescript.md) |
| `fetch` | ブラウザ標準の通信関数 | [L10](L10-javascript-typescript.md) |
| イベントループ | 非同期の処理を順に実行する仕組み | [L10](L10-javascript-typescript.md) |
| TypeScript | 型を足した JavaScript | [L10](L10-javascript-typescript.md) |
| ユニオン型 / ジェネリクス | 「A または B」の型 / 型を引数にする | [L10](L10-javascript-typescript.md) |
| コンポーネント | 画面の一部を返す関数 | [L11](L11-react.md) |
| props | 親から子へ渡す値(読み取り専用) | [L11](L11-react.md) |
| state | コンポーネントが覚える、変わる値 | [L11](L11-react.md) |
| effect(`useEffect`) | 描画の外の世界とつなぐ処理と、その後始末 | [L11](L11-react.md) |
| フック(Hook) | `use` で始まる、React の機能を使う関数 | [L11](L11-react.md) |
| Context | 離れた階層へ値を届ける仕組み | [L11](L11-react.md) |
| `key` | リストの要素を見分ける、一意で変わらない値 | [L11](L11-react.md) |
| 仮想 DOM | 画面の記述を比較して差分だけ反映する仕組み | [L11](L11-react.md) |
| JSX | JS の中に書く HTML 風の記法 | [L11](L11-react.md) |
| StrictMode | 開発中に、副作用の問題を見つけやすくする React の機能 | [L11](L11-react.md) |
| バブリング | イベントが子から親へ伝わること | [L13](L13-kanban.md) |
| ドラッグ&ドロップ | 掴んで動かす操作。キーボードの代替が要る | [L13](L13-kanban.md) |
| Vite | フロントエンドの開発サーバー兼ビルド道具 | [L00](L00-intro.md) |
| MUI | React の UI 部品集 | [L12](L12-ui-css.md) |

## 画面・アクセシビリティ
| 用語 | 意味 | 詳しくは |
|---|---|---|
| ボックスモデル | content・padding・border・margin の箱 | [L12](L12-ui-css.md) |
| Flexbox / Grid | 一方向 / 格子のレイアウト | [L12](L12-ui-css.md) |
| CSS 変数 | `--名前` で持ち、`var()` で使う値。実行時に切替できる | [L12](L12-ui-css.md) |
| Sass | CSS を書きやすくする言語(変数・map・mixin) | [L12](L12-ui-css.md) |
| デザイントークン | 色・間隔などを役割の名前で管理する値 | [L12](L12-ui-css.md) |
| コントラスト比 | 文字と背景の明るさの比。通常の文字は 4.5:1 以上 | [L12](L12-ui-css.md) |
| a11y(アクセシビリティ) | 誰でも使えること | [L12](L12-ui-css.md) |
| ARIA / `aria-hidden` | 読み上げ向けの補助属性 / 読み上げ対象から外す | [L12](L12-ui-css.md) |
| スクリーンリーダー | 画面を音声で読み上げる支援技術 | [L12](L12-ui-css.md) |
| `prefers-reduced-motion` | OS の「動きを減らす」設定 | [L12](L12-ui-css.md) |
| `:focus-visible` | キーボード操作時だけ出すフォーカス枠 | [L12](L12-ui-css.md) |

## テスト
| 用語 | 意味 | 詳しくは |
|---|---|---|
| 単体テスト | 1 つの関数やモデルの検査 | [L14](L14-testing.md) |
| API テスト | HTTP の入口から DB まで通した検査 | [L14](L14-testing.md) |
| パラメータ化 | 同じ検査を入力の表で繰り返す | [L14](L14-testing.md) |
| モック | 呼び出しを記録する偽物(`vi.fn()`) | [L14](L14-testing.md) |
| jsdom | Node の中でブラウザの DOM を模すもの | [L14](L14-testing.md) |
| Vitest / Testing Library | フロントのテスト実行 / 利用者目線で部品を探す道具 | [L14](L14-testing.md) |
| 文書テスト | 文書内のコード・抜粋・出力を実際に検証するテスト | [L14](L14-testing.md) |

## 運用
| 用語 | 意味 | 詳しくは |
|---|---|---|
| Docker / イメージ / コンテナ | 環境ごと箱にして動かす仕組み / 設計図 / 実行中の箱 | [L16](L16-operations.md) |
| compose | 複数のコンテナをまとめて扱う | [L16](L16-operations.md) |
| ボリューム | コンテナを消しても残るデータ置き場 | [L16](L16-operations.md) |
| ヘルスチェック | 「仕事ができる状態か」の確認(`/healthz`) | [L16](L16-operations.md) |
| 環境変数 | OS から渡す設定値 | [L16](L16-operations.md) |
| Cloudflare Tunnel | PC から外向きに張る接続で、外部公開する | [L16](L16-operations.md) |
| Cloudflare Access | 公開前に利用者を確かめる門番 | [L16](L16-operations.md) |
| Sentry | 例外を集めて通知するサービス | [L16](L16-operations.md) |
| ログ(JSON ログ) | 動作の記録。1 行 1 JSON だと機械で扱いやすい | [L16](L16-operations.md) |
| 原子的(atomic) | 途中の状態が見えず、全部か無かのどちらか | [L15](L15-scripts.md) |
| 終了コード | コマンドの結果を示す数字(0 = 成功) | [L15](L15-scripts.md) |
| cron | 決まった時刻にコマンドを実行する仕組み | [L15](L15-scripts.md) |
| ロールバック | 前の状態に戻すこと | [L16](L16-operations.md) |

## 文書・開発の進め方
| 用語 | 意味 | 詳しくは |
|---|---|---|
| mermaid | テキストで図を描く記法。Markdown に埋め込める | [diagrams/README.md](../diagrams/README.md) |
| SVG | 拡大しても劣化しない、図のファイル形式 | [L15](L15-scripts.md) |
| ADR / 決定記録 | 設計判断とその理由の記録(`decisions.md`) | [L17](L17-capstone.md) |
| 受け入れ条件 | 「これができたら完成」を確かめられる形で書いたもの | [L17](L17-capstone.md) |
| リファクタリング | 外から見た挙動を変えずに、内部の作りを整える | [L17](L17-capstone.md) |
| 赤→緑 | 失敗するテストを先に書き(赤)、通す(緑) | [L14](L14-testing.md)・[L17](L17-capstone.md) |
