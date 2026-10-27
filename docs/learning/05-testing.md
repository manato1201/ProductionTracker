# 5. テストの書き方

**テストが仕様書**。期待する挙動(ステータスコード・エラーコード)は、まず `backend/tracker/tests/` を読む。

## 実行
```bash
cd backend
pytest -q                          # 全件(SQLite。約 3 秒)
pytest -q -x                       # 最初の失敗で止める
pytest -q -k transition            # 名前で絞る
pytest -q tracker/tests/test_task_transitions.py::test_only_reviewer_can_approve
# PostgreSQL でも同じテストが走る(select_for_update や制約は本物の DB で確認する価値がある)
POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=pt_test pytest -q
ruff check .

cd ../frontend
npm test                           # Vitest(1 回だけ実行)
npx tsc --noEmit                   # 型チェック(テスト用データの型も検査される)
npm run build                      # 型チェック + ビルド
```

## 何をどこでテストしているか
| 層 | 場所 | 例 |
|---|---|---|
| ルール(状態遷移・権限) | `tests/test_task_transitions.py` | **4×4 の全組み合わせ**を `parametrize`。表を変えれば必ず落ちる |
| API(認証・見える範囲・検証) | `test_api_projects.py` / `test_api_entities_tasks.py` / `test_api_versions_notes.py` | 401 / 403 / 404 / 400 / 409 の網羅 |
| 取り込み | `test_ingest.py` / `test_ingest_scripts.py` | キーなし 401、再送で重複しない、件数一致 |
| 運用の安全 | `test_health_auth_errors.py` | DB 停止で 503、CSRF、ログインの制限、Sentry の除去 |
| 純粋な関数 | `test_paths.py`、`domain/*.test.ts` | 入出力だけのテスト |
| 部品 | `components/*.test.tsx` | 見た目(文字・アイコン)とキーボード操作 |
| API クライアント | `api/client.test.ts` | エラーの変換、CSRF ヘッダ |

## 道具(`tests/conftest.py`)
| fixture | 中身 |
|---|---|
| `project` | コード `DEMO` のプロジェクト |
| `make_user(role)` | プロジェクトに `role` で参加するユーザー。`make_user(None)` は非メンバー。`is_staff=True` なども渡せる |
| `reviewer` / `artist` / `viewer` / `outsider` | 役割ごとのユーザー(`outsider` は非メンバー) |
| `client_for(user)` | そのユーザーでログイン済みの `APIClient`(`force_authenticate`) |
| `entity` / `step` / `task` | `crate` アセット / `FX` 工程 / その組のタスク |

データは `factories.py`(factory_boy)で作る。`VersionFactory.create(task)` は採番つき。

## 型(パターン)
**API のテストの骨格**(新しいエンドポイントは最低この 5 つ):
```python
def test_requires_auth(db):                    # 401
    assert APIClient().get(f"{BASE}/xxx/").status_code == 401

def test_outsider_gets_404(client_for, outsider, ...):   # 見えないものは「無い」
    assert client_for(outsider).get(f"{BASE}/xxx/{obj.id}/").status_code == 404

def test_viewer_cannot_write(client_for, viewer, ...):   # 403
    assert client_for(viewer).post(f"{BASE}/xxx/", {...}, format="json").status_code == 403

def test_invalid_input(client_for, artist, ...):         # 400。code も確かめる
    res = client_for(artist).post(f"{BASE}/xxx/", {...bad...}, format="json")
    assert res.status_code == 400 and res.json()["code"] == "validation_error"

def test_happy_path(client_for, artist, ...):            # 正常
    ...
```
**表を丸ごとテストする**(ルールが表のとき):
```python
ALL_PAIRS = [(a, b) for a in S for b in S]
@pytest.mark.parametrize("src,dst", ALL_PAIRS)
def test_table(...):
    if (src, dst) in ALLOWED: ...通る
    else: with pytest.raises(InvalidTransition): ...
```
**DB の制約**は、API をすり抜けても守られることを `pytest.raises(IntegrityError)` + `transaction.atomic()` で確かめる(`test_estimate_has_db_level_guard`)。

## 落とし穴(実際にはまった)
| 症状 | 原因 | 対策 |
|---|---|---|
| 「セッションの人は取り込みを呼べない」のテストが 401 でなく **403** | `force_authenticate` は認証クラスを **素通り**する | 本物のセッション(`force_login`)で試す |
| ログインのテストが **401**(パスワードは合っているのに) | ファクトリがパスワードを保存していない | `UserFactory._create` で `create_user` を使う |
| テスト中のモックが次のテストに残る | `monkeypatch` を使わず直接差し替えた | `monkeypatch.setattr` / `settings` fixture を使う(自動で戻る) |
| CSRF の挙動を試したいのに素通り | 既定の `APIClient` は CSRF を検査しない | `APIClient(enforce_csrf_checks=True)` |
| 日時が絡むテストが日付をまたいで落ちる | 「今日」を固定していない | 期限は `2000-01-01` のように **十分に過去 / 未来** の固定値にする |
| `Response` をモックして 2 回目で本文が読めない(フロント) | `Response` の本文は使い捨て | `mockImplementation(async () => new Response(...))` で毎回作る |

## フロントのテスト
- Vitest + Testing Library + `userEvent`。**画面の文字(アクセシブルな名前)で探す**: `getByRole("button", { name: /状態を変更/ })`。クラス名では探さない。
- ドラッグ操作そのものは再現しない(ブラウザ依存)。**キーボード操作とメニュー**が同じ `onMove` に流れることをテストする(`Board.test.tsx`)。
- 状態の表示は、**文字とアイコンがある**ことをテストする(色だけに頼っていない保証)。
- API はモックする(`vi.spyOn(globalThis, "fetch")`)。サーバーとの結合はバックエンド側のテストと、下の手動確認で見る。

## 手で確認するチェックリスト(画面を変えたとき)
自動テストがカバーしにくいもの。**ブラウザで** 1 回ずつ:
1. かんばん: 「進行中」→「完了」にドロップ → 確認モーダル → **拒否されて元の列へ戻り、理由のトースト**
2. 「進行中」→「レビュー待ち」(正常)。カードが移り、成功トースト
3. キーボード: カードにフォーカス → `Shift + →`(移動)/ `Enter`(詳細)
4. 「⋮」→「状態を変更」(メニュー)。**ボタンの上でマウスを動かしてもドラッグが始まらない**
5. ドロワーで状態を変える → 閉じたあと **一覧(概要のタスクタブ)が更新されている**
6. 閲覧者(`demo_viewer`)でログイン: 書き込みのボタンが出ない
7. ライト / ダーク(ヘッダーのボタン)。**グレースケール表示でも状態の区別がつく**
8. **幅 360px**(開発者ツールのレスポンシブ)で横スクロールが出ない。全画面
9. 品質タブ・画面差分タブ: 「取得日時」が出ている(取り込みの後)
10. DB を止めて `/healthz` が `503` になる

## バグを直すときの習慣
1. **まず再現する**(テストを書いて赤にする。画面の不具合は、手順を決めてブラウザで再現する)
2. 直す → 同じ手順で緑になることを確かめる
3. 再発防止のテストを残す。**何が原因だったか**を [learning-log.md](../learning-log.md) に 1〜3 行書く

## 確認
- [ ] 新しいエンドポイントのテストを、上の 5 つの型で書ける。
- [ ] `force_authenticate` と `force_login` の違いを説明できる。
- [ ] PostgreSQL でテストを走らせる意味を 1 つ挙げられる。(→ `select_for_update`・制約・並行処理は SQLite では確かめられない)
