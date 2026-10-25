#!/bin/sh
# 起動のたびにマイグレーションを適用する(適用前のバックアップ手順は docs/operations.md)。
set -e
python manage.py migrate --noinput
python manage.py ensure_admin
exec "$@"
