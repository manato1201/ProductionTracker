import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

export interface Resource<T> {
  data: T | undefined;
  loading: boolean;
  error: ApiError | undefined;
  reload: () => Promise<void>;
  setData: (updater: (prev: T | undefined) => T | undefined) => void;
}

/** 取得中・失敗・再読込を持つ最小のデータ取得フック。古い応答は捨てる。 */
export function useResource<T>(fetcher: () => Promise<T>, deps: unknown[]): Resource<T> {
  const [data, setDataState] = useState<T>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError>();
  const seq = useRef(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fetcher, deps);

  const reload = useCallback(async () => {
    const mine = ++seq.current;
    setLoading(true);
    try {
      const result = await run();
      if (mine !== seq.current) return;
      setDataState(result);
      setError(undefined);
    } catch (e) {
      if (mine !== seq.current) return;
      setError(e instanceof ApiError ? e : new ApiError(0, "error", String(e)));
    } finally {
      if (mine === seq.current) setLoading(false);
    }
  }, [run]);

  useEffect(() => {
    void reload();
    return () => {
      seq.current++;
    };
  }, [reload]);

  const setData = useCallback((updater: (prev: T | undefined) => T | undefined) => setDataState(updater), []);
  return { data, loading, error, reload, setData };
}
