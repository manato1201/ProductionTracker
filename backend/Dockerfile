FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_ALLOW_INSECURE_KEY=1 python manage.py collectstatic --noinput \
 && useradd --create-home app && chown -R app /app
USER app

ENTRYPOINT ["/app/entrypoint.sh"]
# 本番相当: gunicorn。開発の compose では runserver に差し替える。
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
