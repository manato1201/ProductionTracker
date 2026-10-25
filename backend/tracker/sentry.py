"""Sentry へ送る前に、認証情報や本文を取り除く(トークンが Sentry に出ないことの担保)。"""

SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie", "x-csrftoken", "idempotency-key"}


def scrub_event(event, hint=None):
    request = event.get("request")
    if request:
        headers = request.get("headers")
        if isinstance(headers, dict):
            for name in list(headers):
                if name.lower() in SENSITIVE_HEADERS:
                    headers[name] = "[Filtered]"
        request.pop("cookies", None)
        request.pop("data", None)  # リクエスト本文(コメント・パスなど)は送らない
    return event
