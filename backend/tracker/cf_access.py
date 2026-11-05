"""Cloudflare Access(OIDC)による認証(任意。既定では無効)。

Cloudflare Access をアプリの前に置くと、通過したリクエストに `Cf-Access-Jwt-Assertion` ヘッダ(署名つきの JWT)が付く。
ここではその JWT を検証し、メールアドレスで既存のユーザーに対応づける。

守っていること:
- **署名・発行者・宛先(AUD)・期限を必ず検証する。** ヘッダを偽装しても、Cloudflare の秘密鍵が無ければ通らない。
  公開鍵は `https://<チーム>.cloudflareaccess.com/cdn-cgi/access/certs`(JWKS)から取り、1 時間キャッシュする。
- **許可するのは RS256 だけ**(アルゴリズムの差し替え攻撃を避ける)。
- **ユーザーの自動作成はしない**(既定)。Access を通っても、アプリに登録されていなければ 403。
  作ってよいなら `CF_ACCESS_AUTO_CREATE=1`。作られたユーザーはどのプロジェクトのメンバーでもない(最小権限)。
- **変更系は CSRF も検査する。** Access のクッキーはブラウザが自動で送るため、CSRF の対象になりうる。
- **`email` が一意に決まらなければ拒否**(同じメールのユーザーが複数いる場合)。

有効にするには `docs/auth.md`(環境変数と認証クラスの並べ方)を見る。
"""

import logging
from functools import lru_cache

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

logger = logging.getLogger(__name__)

HEADER = "HTTP_CF_ACCESS_JWT_ASSERTION"
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
JWKS_LIFESPAN_SECONDS = 3600


def team_domain() -> str:
    """`CF_ACCESS_TEAM_DOMAIN`(例: myteam.cloudflareaccess.com)。スキームや末尾の / は取り除く。"""
    raw = (settings.CF_ACCESS_TEAM_DOMAIN or "").strip()
    return raw.removeprefix("https://").removeprefix("http://").rstrip("/")


@lru_cache(maxsize=4)
def _jwks_client(domain: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"https://{domain}/cdn-cgi/access/certs", cache_keys=True, lifespan=JWKS_LIFESPAN_SECONDS, timeout=5)


def _signing_key(token: str):
    """トークンの `kid` に合う公開鍵。テストではここを差し替える(ネットワークを使わない)。"""
    return _jwks_client(team_domain()).get_signing_key_from_jwt(token).key


def verify_token(token: str) -> dict:
    domain = team_domain()
    try:
        key = _signing_key(token)
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],  # これ以外(none / HS256 など)は受け付けない
            audience=settings.CF_ACCESS_AUD,
            issuer=f"https://{domain}",
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        # 理由(期限切れ・署名の不一致・鍵が取れない)は詳しく返さない。サーバーのログにだけ残す。
        logger.warning("Cloudflare Access の JWT を拒否しました: %s", type(exc).__name__)
        raise AuthenticationFailed("Cloudflare Access の認証情報を確認できません。") from None


def user_for(claims: dict):
    email = (claims.get("email") or "").strip()
    if not email:
        raise AuthenticationFailed("認証情報にメールアドレスがありません。")
    User = get_user_model()
    users = list(User.objects.filter(email__iexact=email, is_active=True)[:2])
    if len(users) > 1:
        raise PermissionDenied("このメールアドレスのユーザーが複数います。管理者に連絡してください。")
    if users:
        return users[0]
    if settings.CF_ACCESS_AUTO_CREATE:
        user = User(username=email[:150], email=email)
        user.set_unusable_password()
        user.save()
        return user
    raise PermissionDenied("このメールアドレスのユーザーは登録されていません。管理者に連絡してください。")


class CloudflareAccessAuthentication(BaseAuthentication):
    """`Cf-Access-Jwt-Assertion` ヘッダの JWT で認証する。設定(チーム・AUD)が無い、またはヘッダが無ければ何もしない。"""

    def authenticate_header(self, request):
        # 返さないと DRF は認証失敗を 403 にしてしまう(401 のため。セッション認証と同じ落とし穴)
        return 'Cloudflare-Access realm="api"'

    def authenticate(self, request):
        if not (team_domain() and settings.CF_ACCESS_AUD):
            return None
        token = request.META.get(HEADER)
        if not token:
            return None  # 次の認証クラス(セッションなど)に任せる
        claims = verify_token(token)
        user = user_for(claims)
        if request.method not in SAFE_METHODS:
            SessionAuthentication().enforce_csrf(request)
        return (user, token)
