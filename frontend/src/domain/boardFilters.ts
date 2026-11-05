import type { Priority } from "../api/types";

/**
 * かんばんの絞り込み。状態を URL の検索パラメータに持つ(使いやすさの提案 UX3)ので、
 * リンクで「この絞り込みを見て」と共有でき、再読み込みや戻るボタンでも保たれる。
 * 例: `?assignee=me&priority=high,urgent&overdue=1&q=crate`
 */
export type Assignee = "all" | "me" | "none";
export interface BoardFilters {
  assignee: Assignee;
  priorities: Priority[];
  overdueOnly: boolean;
  q: string;
}

export const NO_FILTERS: BoardFilters = { assignee: "all", priorities: [], overdueOnly: false, q: "" };
const PRIORITY_VALUES: readonly Priority[] = ["low", "normal", "high", "urgent"];
const MAX_QUERY = 100; // 検索語の長さの上限(URL を巨大にしない)

/** URL からの読み取り。知らない値・壊れた値は無視して、既定(絞り込みなし)にする(共有リンクが壊れていても画面は開く)。 */
export function parseFilters(params: URLSearchParams): BoardFilters {
  const assignee = params.get("assignee");
  const priorities = (params.get("priority") ?? "")
    .split(",")
    .filter((p, i, all): p is Priority => (PRIORITY_VALUES as readonly string[]).includes(p) && all.indexOf(p) === i);
  return {
    assignee: assignee === "me" || assignee === "none" ? assignee : "all",
    priorities,
    overdueOnly: params.get("overdue") === "1",
    q: (params.get("q") ?? "").slice(0, MAX_QUERY),
  };
}

/** 既定の値は URL に載せない(URL を短く保つ)。絞り込み以外のパラメータ(`task` など)はそのまま残す。 */
export function writeFilters(prev: URLSearchParams, filters: BoardFilters): URLSearchParams {
  const next = new URLSearchParams(prev);
  for (const key of ["assignee", "priority", "overdue", "q"]) next.delete(key);
  if (filters.assignee !== "all") next.set("assignee", filters.assignee);
  if (filters.priorities.length) next.set("priority", filters.priorities.join(","));
  if (filters.overdueOnly) next.set("overdue", "1");
  if (filters.q) next.set("q", filters.q.slice(0, MAX_QUERY));
  return next;
}

export const hasFilter = (f: BoardFilters) => f.assignee !== "all" || f.priorities.length > 0 || f.overdueOnly || f.q !== "";
