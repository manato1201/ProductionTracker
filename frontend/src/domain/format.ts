const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;
const pad = (n: number) => String(n).padStart(2, "0");

/** 日付は `2026-10-11` 形式に統一(決めごと P1)。日時は端末の時間帯で `2026-10-11 09:30`。 */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  if (DATE_ONLY.test(value)) return value;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${formatDate(value)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function formatPercent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

export function formatDiffRatio(ratio: number): string {
  return `${(ratio * 100).toFixed(2)}%`;
}

/** プロジェクトコードの先頭 2 文字(一覧の「記号」)。 */
export function symbolOf(code: string): string {
  return code.slice(0, 2).toUpperCase();
}
