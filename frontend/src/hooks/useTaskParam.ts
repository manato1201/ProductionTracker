import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/** 開いているタスク(ドロワー)を URL の `?task=` に持つ。リンクで共有でき、戻るボタンで閉じられる。 */
export function useTaskParam(): [number | null, (id: number | null) => void] {
  const [params, setParams] = useSearchParams();
  const raw = params.get("task");
  const id = raw && /^\d+$/.test(raw) ? Number(raw) : null;
  const set = useCallback(
    (next: number | null) =>
      setParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          if (next === null) p.delete("task");
          else p.set("task", String(next));
          return p;
        },
        { replace: next === null },
      ),
    [setParams],
  );
  return [id, set];
}
