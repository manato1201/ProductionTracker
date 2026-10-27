import type { TaskStatus } from "../api/types";

/**
 * ASCII モチーフ「植物の成長」(設計書 追補 2026-10-27)。種 → 芽 → 花 → 実 を、工程の状態に対応づける。
 * 空の列・待機の状態にだけ出す飾り。本文や操作部品には使わない(読み上げ対象にもしない)。
 *
 * 各段階は 2 コマ(ゆっくり揺れる / 脈打つ)。幅 9 文字・高さ 4 行にそろえてある。
 * `prefers-reduced-motion` のときは先頭の 1 コマだけを出す(静止画)。
 */
export type GrowthStage = "seed" | "sprout" | "flower" | "fruit";

export const GROWTH_FRAMES: Record<GrowthStage, readonly (readonly string[])[]> = {
  seed: [
    ["         ", "         ", "    o    ", "~~~~~~~~~"],
    ["         ", "         ", "    O    ", "~~~~~~~~~"],
  ],
  sprout: [
    ["         ", "   \\ /   ", "    |    ", "~~~~~~~~~"],
    ["         ", "   \\|/   ", "    |    ", "~~~~~~~~~"],
  ],
  flower: [
    ["   (*)   ", "    |    ", "   \\|/   ", "~~~~~~~~~"],
    ["   (@)   ", "    |    ", "   \\|/   ", "~~~~~~~~~"],
  ],
  fruit: [
    ["   \\|/   ", "  o-|-o  ", "    |    ", "~~~~~~~~~"],
    ["   \\|/   ", "  O-|-o  ", "    |    ", "~~~~~~~~~"],
  ],
};

/** 状態 → 段階。Record なので、状態を足してここを書き忘れると型エラーになる。 */
export const GROWTH_STAGE_OF_STATUS: Record<TaskStatus, GrowthStage> = {
  todo: "seed",
  in_progress: "sprout",
  review: "flower",
  done: "fruit",
};

export const FRAME_INTERVAL_MS = 900;
