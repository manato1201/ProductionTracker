"""環境変数から管理者を 1 人作る(docker compose の初回起動用)。既にいれば何もしない。"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD があれば管理者を作る"

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not (username and password):
            self.stdout.write("DJANGO_SUPERUSER_* が未設定のため、管理者は作りません。")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"管理者 {username} は既にあります。")
            return
        User.objects.create_superuser(username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f"管理者 {username} を作成しました。"))
