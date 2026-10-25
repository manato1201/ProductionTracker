import * as Sentry from "@sentry/react";

const SENSITIVE = new Set(["authorization", "x-api-key", "cookie", "x-csrftoken"]);

/** 送信前に認証情報・本文を落とす(トークンが Sentry に出ない担保)。 */
export function scrubEvent<T extends Sentry.ErrorEvent>(event: T): T {
  const req = event.request;
  if (req) {
    if (req.headers) {
      for (const key of Object.keys(req.headers)) {
        if (SENSITIVE.has(key.toLowerCase())) req.headers[key] = "[Filtered]";
      }
    }
    delete req.cookies;
    delete req.data;
  }
  return event;
}

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;
  Sentry.init({
    dsn,
    release: import.meta.env.VITE_APP_RELEASE,
    environment: import.meta.env.MODE,
    // v11 では sendDefaultPii の代わりに dataCollection。ユーザー情報・Cookie・ヘッダ・本文・クエリを送らない
    dataCollection: { userInfo: false, cookies: false, httpHeaders: false, httpBodies: [], urlQueryParams: false },
    tracesSampleRate: 0, // 無料枠のため、性能計測は既定で無効
    beforeSend: scrubEvent,
  });
}

export { Sentry };
