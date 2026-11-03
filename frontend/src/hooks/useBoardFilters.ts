import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { NO_FILTERS, parseFilters, writeFilters, type BoardFilters } from "../domain/boardFilters";

/** かんばんの絞り込みを URL に持つ。変更は履歴を積まない(`replace`)ので、戻るボタンが絞り込みの分だけ戻らない。 */
export function useBoardFilters(): [BoardFilters, (patch: Partial<BoardFilters>) => void, () => void] {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(() => parseFilters(params), [params]);
  const update = useCallback(
    (patch: Partial<BoardFilters>) => setParams((prev) => writeFilters(prev, { ...parseFilters(prev), ...patch }), { replace: true }),
    [setParams],
  );
  const reset = useCallback(() => setParams((prev) => writeFilters(prev, NO_FILTERS), { replace: true }), [setParams]);
  return [filters, update, reset];
}
