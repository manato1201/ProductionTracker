# ER 図(実装済みモデル)

設計書 §1.2 を、実装したモデル(`backend/tracker/models.py`)に合わせて確定したもの。

![データモデル](diagrams/data-model.svg)

## 関係(全体)
属性を省いて、関係だけを描いた図(読みやすさのため)。属性は次の節。

```mermaid
erDiagram
    direction LR
    PROJECT ||--o{ ENTITY : "has"
    PROJECT ||--o{ PROJECT_MEMBER : "has"
    USER ||--o{ PROJECT_MEMBER : "joins as"
    ENTITY ||--o{ TASK : "has"
    STEP ||--o{ TASK : "defines"
    USER |o--o{ TASK : "assigned to"
    TASK ||--o{ VERSION : "produces"
    USER |o--o{ VERSION : "created by"
    VERSION ||--o{ VISUAL_RESULT : "checked as"
    PROJECT ||--o{ QUALITY_REPORT : "scanned in"
    ENTITY |o--o{ QUALITY_REPORT : "matched by path prefix"
    USER |o--o{ NOTE : "writes"
    ENTITY ||--o{ NOTE : "about (generic)"
    TASK ||--o{ NOTE : "about (generic)"
    VERSION ||--o{ NOTE : "about (generic)"
```

読み方: `||--o{` は「1 対 多」、`|o--o{` は「0 または 1 対 多」(担当者なし・作成者なし・アセットに対応しないスキャン行がありうる)。

## 属性(主要なもの)
```mermaid
erDiagram
    direction LR
    PROJECT {
        string code UK "大文字小文字を区別しない"
        string name
        date start
        date due
    }
    PROJECT_MEMBER {
        string role "reviewer / artist / viewer"
    }
    ENTITY {
        string name
        string kind "asset(shot は未実装)"
        string status
        string path "品質との突き合わせ用"
    }
    TASK {
        string status "todo / in_progress / review / done"
        string priority
        date due
        float estimate_h "0 以上"
    }
    VERSION {
        int number "タスク内で連番"
        string status "draft / submitted / approved / rejected"
        string file_ref
        string thumb
        json dcc
        string idempotency_key "ユーザーごとに一意"
    }
    PROJECT ||--o{ ENTITY : has
    PROJECT ||--o{ PROJECT_MEMBER : has
    ENTITY ||--o{ TASK : has
    TASK ||--o{ VERSION : produces
```

```mermaid
erDiagram
    direction LR
    NOTE {
        int content_type_id "GenericForeignKey"
        int object_id
        string body
    }
    QUALITY_REPORT {
        int scan_run_id
        string asset_path
        int defects "bigint(同じパスを合算するため)"
        datetime scanned_at
    }
    VISUAL_RESULT {
        string run_id
        string verdict
        float diff_ratio "0 から 1"
        datetime captured_at
        json conditions "解像度・固定時刻・シード"
    }
    VERSION ||--o{ VISUAL_RESULT : "checked as"
    ENTITY |o--o{ QUALITY_REPORT : "matched by path prefix"
```

## 状態(どこからどこへ行けるか)
遷移表は `Task.TRANSITIONS` / `Version.TRANSITIONS`(`backend/tracker/models.py`)。

```mermaid
stateDiagram-v2
    direction LR
    [*] --> todo
    todo --> in_progress : 着手
    in_progress --> review : 提出
    review --> in_progress : 差し戻し
    review --> done : 承認(レビュアーのみ・版が必要)
    done --> in_progress : 再開
```

```mermaid
stateDiagram-v2
    direction LR
    [*] --> draft
    draft --> submitted : 提出
    submitted --> approved : 承認(レビュアーのみ)
    submitted --> rejected : 却下(レビュアーのみ)
    rejected --> draft : 作り直し
    approved --> [*]
```

## 一意制約(重複を DB で防ぐもの)
| 対象 | 制約 |
|---|---|
| Project | `code`(**大文字小文字を区別しない**: `demo` と `DEMO` は同じ。API は 400 を返す) |
| ProjectMember | `(project, user)` |
| Entity | `(project, kind, name)` |
| Task | `(entity, step)` — 1 アセットに同じ工程は 1 つ |
| Version | `(task, number)`、`(created_by, idempotency_key)`(鍵があるとき) |
| QualityReport | `(project, scan_run_id, asset_path)`(同じ実行は「全て置き換え」で冪等) |
| VisualResult | `(run_id, version)` |

## DB の CHECK 制約(API の検証をすり抜けても DB が守るもの)
| 対象 | 制約 |
|---|---|
| Task | `estimate_h` は NULL か 0 以上 |
| VisualResult | `diff_ratio` は 0〜1 |

## 削除の連鎖
アセット → タスク → 版 の順に消える。**ノートは対象と一緒に消える**(`GenericRelation`。孤児を残さない)。
プロジェクトを消すと、アセット・メンバー・品質レポートも消える。ユーザーを消しても、版・ノートは作成者が空(NULL)になるだけで残る。

## 設計書との差分
- `QUALITY_REPORT` は設計書の `ENTITY` 単位ではなく、**アセットパス単位**の行にした。アセットに対応しない行(`entity` = NULL)も残し、元の `insight.db` と欠陥件数が一致することを確認できるようにするため。
- ノートの対象(3 本の線)は `ContentType` + `object_id` の 1 つの関連(Entity / Task / Version のみ。他は API が 400)。
- `Step`(工程)の初期データはマイグレーション `0002_default_steps` で投入(モデリング・テクスチャ・リグ・アニメーション・FX・ライティング)。
