# 認証と、差し替え口(Phase 6)

## 今の認証
| 用途 | 方式 | 備考 |
|---|---|---|
| 画面 → API | Django のセッション + CSRF | 未認証は 401(`SessionAuthentication401`)。ログイン自体も CSRF を検査する(ログイン CSRF 対策) |
| DCC パネル等 → API | `Authorization: Token <ユーザー別トークン>` | `python manage.py drf_create_token <username>` で発行。`-r` を付けると再発行(古いものは無効) |
| 外部ツール → 取り込み API | `X-API-Key` | **取り込み API 専用**。画面の API には使えない。`INGEST_API_KEYS` に無ければ(空なら)常に 401 |

## ログインの総当たり対策
`POST /auth/login/` は、IP(`X-Forwarded-For` があればその値)ごとに **10 回/分**(`LOGIN_THROTTLE_RATE` で変更)。超えると `429 {"code": "throttled"}`。
キャッシュはプロセスごと(既定の LocMemCache)なので、gunicorn のワーカー数だけ実質の上限は緩くなる。厳密に制限するなら共有キャッシュ(Redis など)を使う。
Cloudflare Access の背後では、そもそも Access を通った人だけがここに届く。

## 差し替え口
認証クラスは環境変数で入れ替えられる(`config/settings.py`):

```
API_AUTHENTICATION_CLASSES=tracker.auth.SessionAuthentication401,rest_framework.authentication.TokenAuthentication
```

外部 ID 基盤(例: Firebase Auth)を足すには:

1. `rest_framework.authentication.BaseAuthentication` を継承したクラスを書く(`Authorization: Bearer <IDトークン>` を検証し、`User` を取得または作成して `(user, token)` を返す)。
2. そのクラスのパスを `API_AUTHENTICATION_CLASSES` に追加する。
3. `ProjectMember` の役割(`role`)は今まで通り Django の `User` に紐づくので、ビュー・権限の変更は不要。

**Firebase は実装していない**(設計書どおり、Django の認証と ORM を学ぶため)。上は差し込み位置の説明であり、動作確認はしていない。
