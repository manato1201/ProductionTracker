"""Cloudflare Access(OIDC)の認証。実際の Cloudflare には繋がず、手元で作った RSA 鍵で署名したトークンで確かめる。"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from tracker import cf_access
from tracker.cf_access import CloudflareAccessAuthentication

from .factories import UserFactory

pytestmark = pytest.mark.django_db

TEAM = "myteam.cloudflareaccess.com"
AUD = "aud-tag-123"


class Whoami(APIView):
    authentication_classes = [CloudflareAccessAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": request.user.username})

    def post(self, request):
        return Response({"user": request.user.username})


@pytest.fixture(scope="module")
def keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def access(settings, monkeypatch, keypair):
    settings.CF_ACCESS_TEAM_DOMAIN = TEAM
    settings.CF_ACCESS_AUD = AUD
    settings.CF_ACCESS_AUTO_CREATE = False
    monkeypatch.setattr(cf_access, "_signing_key", lambda token: keypair.public_key())  # JWKS の取得を使わない
    return settings


def mint(keypair, email="alice@example.com", **over):
    now = int(time.time())
    claims = {"aud": [AUD], "email": email, "iat": now, "exp": now + 300, "iss": f"https://{TEAM}", "sub": "abc", "type": "app"}
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, keypair, algorithm="RS256", headers={"kid": "k1"})


def call(token=None, method="get", csrf=False):
    factory = APIRequestFactory(enforce_csrf_checks=csrf)
    kwargs = {"HTTP_CF_ACCESS_JWT_ASSERTION": token} if token else {}
    request = getattr(factory, method)("/whoami/", **kwargs)
    return Whoami.as_view()(request)


def test_valid_token_authenticates_the_user_with_that_email(access, keypair):
    UserFactory(username="alice", email="alice@example.com")
    res = call(mint(keypair))
    assert res.status_code == 200 and res.data == {"user": "alice"}


def test_email_match_is_case_insensitive(access, keypair):
    UserFactory(username="alice", email="Alice@Example.com")
    assert call(mint(keypair, email="alice@EXAMPLE.com")).status_code == 200


def test_no_header_falls_through_to_other_authentication(access):
    """ヘッダが無ければ何もしない(= 次の認証クラスに任せる)。この View では未認証 → 401。"""
    assert call().status_code in (401, 403)
    assert CloudflareAccessAuthentication().authenticate(APIRequestFactory().get("/")) is None


def test_disabled_without_settings(settings, keypair, monkeypatch):
    """チームか AUD が未設定なら、ヘッダがあっても何もしない(うっかり有効にならない)。"""
    settings.CF_ACCESS_TEAM_DOMAIN = ""
    settings.CF_ACCESS_AUD = ""
    UserFactory(username="alice", email="alice@example.com")
    request = APIRequestFactory().get("/", HTTP_CF_ACCESS_JWT_ASSERTION=mint(keypair))
    assert CloudflareAccessAuthentication().authenticate(request) is None


@pytest.mark.parametrize(
    "over",
    [
        {"aud": ["other-app"]},  # 別のアプリ宛て
        {"iss": "https://evil.cloudflareaccess.com"},  # 別の発行者
        {"exp": int(time.time()) - 10},  # 期限切れ
        {"exp": None},  # 期限なし
        {"aud": None},
    ],
)
def test_invalid_claims_are_rejected(access, keypair, over):
    UserFactory(email="alice@example.com")
    assert call(mint(keypair, **over)).status_code == 401


def test_token_signed_with_another_key_is_rejected(access, keypair):
    """ヘッダの偽装: 手元の別の鍵で署名したトークンは通らない。"""
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    UserFactory(email="alice@example.com")
    assert call(mint(other)).status_code == 401


def test_alg_none_and_hs256_are_rejected(access, keypair):
    UserFactory(email="alice@example.com")
    now = int(time.time())
    claims = {"aud": [AUD], "email": "alice@example.com", "iat": now, "exp": now + 300, "iss": f"https://{TEAM}"}
    unsigned = jwt.encode(claims, key=None, algorithm="none")
    hs = jwt.encode(claims, "shared-secret-that-is-long-enough-for-hs256", algorithm="HS256")
    assert call(unsigned).status_code == 401
    assert call(hs).status_code == 401
    assert call("not-a-jwt").status_code == 401


def test_unregistered_email_is_forbidden_not_created(access, keypair):
    """Access を通っても、アプリに登録されていなければ 403(自動では作らない)。"""
    from django.contrib.auth import get_user_model

    res = call(mint(keypair, email="stranger@example.com"))
    assert res.status_code == 403
    assert not get_user_model().objects.filter(email="stranger@example.com").exists()


def test_auto_create_makes_a_user_without_any_membership(access, keypair):
    from django.contrib.auth import get_user_model

    access.CF_ACCESS_AUTO_CREATE = True
    res = call(mint(keypair, email="new@example.com"))
    assert res.status_code == 200
    user = get_user_model().objects.get(email="new@example.com")
    assert not user.has_usable_password() and not user.is_staff and user.memberships.count() == 0  # 最小権限


def test_ambiguous_email_is_rejected(access, keypair):
    UserFactory(username="a1", email="dup@example.com")
    UserFactory(username="a2", email="dup@example.com")
    assert call(mint(keypair, email="dup@example.com")).status_code == 403


def test_inactive_user_is_not_matched(access, keypair):
    UserFactory(username="gone", email="alice@example.com", is_active=False)
    assert call(mint(keypair)).status_code == 403


def test_missing_email_claim_is_rejected(access, keypair):
    assert call(mint(keypair, email="")).status_code == 401


def test_unsafe_methods_also_require_csrf(access, keypair):
    """Access のクッキーはブラウザが自動で送る。変更系は、セッションと同じく CSRF を検査する。"""
    UserFactory(username="alice", email="alice@example.com")
    token = mint(keypair)
    assert call(token, method="get", csrf=True).status_code == 200
    assert call(token, method="post", csrf=True).status_code == 403


def test_jwks_failure_is_a_401_without_details(access, keypair, monkeypatch):
    def boom(token):
        raise jwt.PyJWKClientError("could not fetch https://myteam.cloudflareaccess.com/cdn-cgi/access/certs")

    monkeypatch.setattr(cf_access, "_signing_key", boom)
    UserFactory(email="alice@example.com")
    res = call(mint(keypair))
    assert res.status_code == 401 and "cdn-cgi" not in str(res.data)


def test_team_domain_is_normalized(settings):
    settings.CF_ACCESS_TEAM_DOMAIN = "https://myteam.cloudflareaccess.com/"
    assert cf_access.team_domain() == TEAM
