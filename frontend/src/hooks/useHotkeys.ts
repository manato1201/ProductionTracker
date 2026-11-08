import { useEffect, useRef } from "react";

/** 入力欄・選択欄・モーダルの中では、ショートカットを効かせない(T6)。 */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
}

export type HotkeyMap = Record<string, () => void>;

/**
 * 1 キーのショートカット(`/`・`j`・`k`)。修飾キー付き(Shift+矢印など別機能)と、
 * 入力中・ダイアログ表示中は無視する。マップは毎回差し替えてよい(最新を参照する)。
 */
export function useHotkeys(map: HotkeyMap, enabled = true) {
  const ref = useRef(map);
  ref.current = map;
  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
      if (isTypingTarget(e.target)) return;
      if (
        document.querySelector(
          '[role="dialog"], [role="presentation"].MuiDrawer-root',
        )
      )
        return;
      const handler = ref.current[e.key];
      if (!handler) return;
      e.preventDefault();
      handler();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enabled]);
}
