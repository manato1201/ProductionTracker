# 3. フロントエンドの道案内

対象: `frontend/src/`(Vite + React 19 + TypeScript、React Router 7、MUI 7、Sass、@dnd-kit)。

## 起動の順序(`main.tsx`)
外側から内側へ、この順で包んでいる(順序に意味がある):

```
ThemeModeProvider   テーマ(ライト/ダーク)。MUI のテーマ + data-theme 属性
 └ ToastProvider    useToast().notify(...) でどこからでもトースト
    └ BrowserRouter
       └ AuthProvider   起動時に CSRF クッキーを取り、/me/ でログイン状態を確認
          └ App        ルーティング
```

- `AuthProvider` は `setUnauthorizedHandler` で、**どの API が 401 を返しても** ログイン画面へ戻す。
- API の URL は `api/endpoints.ts` に集約。fetch は `api/client.ts` だけが呼ぶ(CSRF ヘッダ・統一エラー `ApiError` はここ)。

## ルーティング(`App.tsx`)
| ルート | 画面 | メモ |
|---|---|---|
| `/login` | `LoginPage` | |
| `/projects` | `ProjectsPage` | 一覧 + 並べ替え |
| `/projects/:code` | `ProjectLayout` → `OverviewPage` | `ProjectLayout` が **project と members を読み込み、子へ共有**(`useProject()`) |
| `/projects/:code/board` | `BoardPage` | かんばん |
| `/projects/:code/entities/:id` | `EntityPage` | |
| `/me/tasks` | `MyTasksPage` | `?view=overdue / review` |
| `/debug/sentry` | `DebugSentryPage` | `VITE_SENTRY_DEBUG=1` のときだけ |

URL に状態を持たせるもの: `?tab=`(タブ)、`?task=ID`(ドロワー。`useTaskParam`)。リンクで共有でき、戻るボタン・Esc で閉じる。

## データの取得(`hooks/useResource.ts`)
```ts
const res = useResource(() => tasks.list({ project: code }), [code]);
// res.data / res.loading / res.error / res.reload() / res.setData(updater)
```
- **deps が変わったときだけ**取り直す。古い応答は捨てる(連番で判定)ので、絞り込みを素早く切り替えても表示がぶれない。
- `reload()` は明示の再読み込み。`setData` は先行更新(かんばん)用。
- 全件が要る画面は `getAll`(最大 10 ページ = 2,000 件)。超えたら画面に件数を出す。

> **落とし穴(実際にあった不具合)**: 再読み込みの合図を「更新日時 + 件数」のような **結果からの推測** にしない。状態の変更では変わらず、一覧が古いまま残る。`OverviewPage` の `tasksRevision` のように、**変更があったことを知らせる明示のカウンタ** を持つ。

## かんばんの仕組み
```
Board.tsx(表示とドラッグ)
  └ onMove(task, to)  ← ドラッグ・「⋮」メニュー・Shift+←/→ の 3 経路が同じ関数へ
      └ useTaskTransition.request  「完了」なら確認モーダル → run
          ├ onApply   画面を先に動かす(BoardPage: patchTask)
          ├ tasks.transition(id, to)   サーバーが可否を決める
          ├ 成功: onSuccess(最新のタスクで置き換え)+ 成功トースト
          └ 失敗: onRevert(元の列へ戻す)+ サーバーの detail をトースト
```
- **遷移の可否は画面で判断しない**。拒否されたら戻して理由を出すだけ。メニューに出す候補は、サーバーが返す `task.next_statuses`。
- ドラッグ: `MouseSensor`(6px 動いたら開始。クリックと区別)と `TouchSensor`(200ms 長押し。縦スクロールを妨げない)。キーボードは標準センサーを使わず、**メニューと Shift+←/→** を用意した。
- ドラッグ中の見た目: `DragOverlay` に傾き 2° + 影(`.card--dragging`)、ドロップ先の列は枠線で強調(`.column--over`)。`prefers-reduced-motion` では傾けない。
- 「⋮」ボタンは `onMouseDown` / `onTouchStart` を止める。**dnd-kit は `mousedown` を見る**ので、`pointerdown` を止めても効かない(実際にあった不具合)。

## 見た目(Sass トークン)
```
styles/_tokens.scss     色・余白・フォントの唯一の出どころ($light / $dark のマップ)
  ├ global.scss         CSS 変数 --pt-* として出力。ライト/ダークは data-theme と prefers-color-scheme
  └ tokens.module.scss  :export で JS へ → theme.ts が MUI のテーマに使う
```
- 色は **`--pt-*` を使う**(16 進数を直接書かない)。新しい色を足すときは、ライトとダークの **両方** に定義し、背景に対して 4.5:1 以上あることを確認する(計算方法は [ui-rules.md](../ui-rules.md))。
- 状態は `StatusLabel`(色 + アイコン + 文字)。色だけで区別する表示を作らない。
- 数字・日付は `.num`(等幅)。日付は `domain/format.ts` で `2026-10-11` 形式。
- **幅 360px で横スクロールを出さない**: グリッドの子に `min-width: 0`、長い文字列は `overflow-wrap: anywhere`、かんばんは 900px 未満で 1 列に積む。新しい画面を作ったら 360px で確認する。

## 部品の早見表
| 部品 | 場所 | 使いどころ |
|---|---|---|
| `Board` | `components/Board.tsx` | かんばん(ドラッグ・列・カード) |
| `TaskDrawer` | `components/TaskDrawer.tsx` | 右からのタスク詳細(版・ノート・品質) |
| `Dialogs` / `FormDialog` | `components/` | 作成フォーム。`FormDialog` が送信中の二重送信防止とエラー表示を持つ |
| `FilterChip` | `components/FilterChip.tsx` | 絞り込み・並べ替え。`aria-pressed` つき |
| `StatusLabel` / `PriorityLabel` / `DueText` | `components/` | 状態・優先度・期日の表示(色 + アイコン + 文字) |
| `Feedback`(`EmptyState` / `ErrorNotice` / スケルトン) | `components/Feedback.tsx` | 読み込み中・空・失敗の 3 状態 |
| `VersionsList` / `NotesPanel` / `IntegrationPanels` | `components/` | 版・ノート・品質・画面差分 |

どの画面も **「読み込み中 → 空 → 失敗 → 通常」の 4 状態** を必ず作る(`Feedback.tsx` の部品を使う)。

## 読む順序(おすすめ)
1. `api/client.ts`(`ApiError`・CSRF)→ `api/endpoints.ts`
2. `hooks/useResource.ts` → `hooks/useTaskTransition.tsx`
3. `pages/BoardPage.tsx` → `components/Board.tsx`
4. `pages/OverviewPage.tsx`(`ProjectLayout` の共有と、`tasksRevision`)
5. `styles/_tokens.scss` → `styles/global.scss`

## 確認
- [ ] かんばんで「進行中 → 完了」をドロップしたとき、画面が最初に何をして、拒否されたとき何を元に戻すか、コードで追える。
- [ ] 新しいフィルタ用のチップを 1 つ足すなら、どの部品を使うか。(→ `FilterChip`)
- [ ] ライトでもダークでも読める新しい色を足すには、どのファイルのどこを直すか。
