import { useEffect, useState } from "react";
import type { TaskStatus } from "../api/types";
import { FRAME_INTERVAL_MS, GROWTH_FRAMES, GROWTH_STAGE_OF_STATUS } from "../domain/motif";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

/**
 * 植物の成長の ASCII モチーフ(飾り)。空の列・待機の状態にだけ使う。
 * - 読み上げ対象にしない(aria-hidden)。意味は隣の文字(「タスクはありません」)が持つ。
 * - 色は既存の状態トークン(.status--*)。新しい色は足さない。
 * - `prefers-reduced-motion` では静止画 1 枚。タブが隠れている間は動かさない(描画負荷を使わない)。
 */
export function AsciiPlant({ status }: { status: TaskStatus }) {
  const frames = GROWTH_FRAMES[GROWTH_STAGE_OF_STATUS[status]];
  const reduced = usePrefersReducedMotion();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (reduced || frames.length < 2) {
      setIndex(0);
      return;
    }
    const timer = window.setInterval(() => {
      if (!document.hidden) setIndex((i) => (i + 1) % frames.length);
    }, FRAME_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [reduced, frames]);

  return (
    <pre className={`ascii-motif ascii-motif--${status}`} aria-hidden="true" data-testid="ascii-plant">
      {frames[index].join("\n")}
    </pre>
  );
}
