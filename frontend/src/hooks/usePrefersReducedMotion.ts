import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

/** OS の「視差効果を減らす」設定。matchMedia が無い環境(テストなど)では false。 */
export function usePrefersReducedMotion(): boolean {
  const read = () => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(QUERY).matches;
  const [reduced, setReduced] = useState(read);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mql = window.matchMedia(QUERY);
    const onChange = () => setReduced(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return reduced;
}
