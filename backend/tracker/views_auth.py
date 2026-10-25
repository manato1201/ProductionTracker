from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


class CsrfOnlyAuthentication(BaseAuthentication):
    """ログイン前でも CSRF を検査する(ログイン CSRF 対策)。ユーザーは確定させない。"""

    def authenticate(self, request):
        SessionAuthentication().enforce_csrf(request)
        return None

    def authenticate_header(self, request):
        return 'Session realm="api"'  # 認証失敗を 403 ではなく 401 にする


class CsrfView(APIView):
    """画面の起動時に呼び、CSRF クッキーを受け取る。"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrf": get_token(request)})


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfOnlyAuthentication]

    def post(self, request):
        body = LoginSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        user = authenticate(request, **body.validated_data)
        if user is None:
            raise AuthenticationFailed("ユーザー名またはパスワードが正しくありません。")
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=204)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
