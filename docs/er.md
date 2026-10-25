# ER 図(実装済みモデル)

設計書 §1.2 を、実装したモデル(`backend/tracker/models.py`)に合わせて確定したもの。

```mermaid
erDiagram
    PROJECT ||--o{ ENTITY : has
    PROJECT ||--o{ PROJECT_MEMBER : has
    PROJECT ||--o{ QUALITY_REPORT : "scanned in"
    USER ||--o{ PROJECT_MEMBER : "joins as"
    ENTITY ||--o{ TASK : has
    STEP ||--o{ TASK : defines
    USER ||--o{ TASK : "assigned to"
    TASK ||--o{ VERSION : produces
    USER ||--o{ VERSION : "created by"
    USER ||--o{ NOTE : writes
    ENTITY ||--o{ NOTE : "about (generic)"
    TASK ||--o{ NOTE : "about (generic)"
    VERSION ||--o{ NOTE : "about (generic)"
    ENTITY |o--o{ QUALITY_REPORT : "matched by path prefix"
    VERSION ||--o{ VISUAL_RESULT : "checked as"

    PROJECT { string code UK string name date start date due }
    PROJECT_MEMBER { string role "reviewer|artist|viewer" }
    STEP { string code UK string name int order }
    ENTITY { string name string kind "asset(shot は未実装)" string status string path }
    TASK { string status "todo|in_progress|review|done" string priority date due float estimate_h }
    VERSION { int number "タスク内で連番" string status "draft|submitted|approved|rejected" string file_ref string thumb json dcc string idempotency_key }
    NOTE { int content_type_id int object_id string body }
    QUALITY_REPORT { int scan_run_id string asset_path int defects datetime scanned_at }
    VISUAL_RESULT { string run_id string verdict float diff_ratio datetime captured_at json conditions }
```

## 一意制約(重複を DB で防ぐもの)
| 対象 | 制約 |
|---|---|
| Project | `code` |
| ProjectMember | `(project, user)` |
| Entity | `(project, kind, name)` |
| Task | `(entity, step)` — 1 アセットに同じ工程は 1 つ |
| Version | `(task, number)`、`(created_by, idempotency_key)`(鍵があるとき) |
| QualityReport | `(project, scan_run_id, asset_path)` |
| VisualResult | `(run_id, version)` |

## 設計書との差分
- `QUALITY_REPORT` は設計書の `ENTITY` 単位ではなく、**アセットパス単位**の行にした。アセットに対応しない行(`entity` = NULL)も残し、元の `insight.db` と欠陥件数が一致することを確認できるようにするため。
- ノートの対象(3 本の線)は `ContentType` + `object_id` の 1 つの関連(Entity / Task / Version のみ。他は API が 400)。
- `Step`(工程)の初期データはマイグレーション `0002_default_steps` で投入(モデリング・テクスチャ・リグ・アニメーション・FX・ライティング)。
