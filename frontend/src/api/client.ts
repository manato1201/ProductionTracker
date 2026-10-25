import type { Page } from "./types";

const BASE = "/api/v1";

/** サーバーの統一エラー形式 `{code, detail, errors?}` を保持する。 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public detail: string,
    public errors?: Record<string, unknown>,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

type UnauthorizedHandler = () => void;
let onUnauthorized: UnauthorizedHandler | null = null;
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  onUnauthorized = handler;
}

export function readCookie(name: string, source: string = document.cookie): string | null {
  const hit = source.split("; ").find((c) => c.startsWith(`${name}=`));
  return hit ? decodeURIComponent(hit.slice(name.length + 1)) : null;
}

export type Query = Record<string, string | number | boolean | null | undefined>;

export function withQuery(path: string, query?: Query): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

async function toError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    return new ApiError(res.status, body.code ?? "error", body.detail ?? res.statusText, body.errors);
  } catch {
    return new ApiError(res.status, "error", `サーバーからの応答を読めませんでした(${res.status})`);
  }
}

export async function request<T>(method: string, path: string, body?: unknown, query?: Query): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    const csrf = readCookie("csrftoken");
    if (csrf) headers["X-CSRFToken"] = csrf;
  }
  let res: Response;
  try {
    res = await fetch(withQuery(`${BASE}${path}`, query), {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "network_error", "サーバーに接続できません。");
  }
  if (!res.ok) {
    const err = await toError(res);
    if (res.status === 401 && onUnauthorized) onUnauthorized();
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const get = <T>(path: string, query?: Query) => request<T>("GET", path, undefined, query);
export const post = <T>(path: string, body?: unknown) => request<T>("POST", path, body ?? {});
export const patch = <T>(path: string, body: unknown) => request<T>("PATCH", path, body);

/** 全ページを順に読む(上限 maxPages)。ボードなど一覧全体が要る画面用。 */
export async function getAll<T>(path: string, query?: Query, maxPages = 10): Promise<{ items: T[]; count: number }> {
  const items: T[] = [];
  let count = 0;
  for (let page = 1; page <= maxPages; page++) {
    const res = await get<Page<T>>(path, { ...query, page, page_size: 200 });
    items.push(...res.results);
    count = res.count;
    if (!res.next) break;
  }
  return { items, count };
}
