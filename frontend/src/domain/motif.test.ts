import { GROWTH_FRAMES, GROWTH_STAGE_OF_STATUS } from "./motif";
import { TASK_STATUSES } from "./status";

describe("ASCII モチーフ(植物の成長)", () => {
  it("全ての状態に段階が対応する(種 → 芽 → 花 → 実)", () => {
    expect(TASK_STATUSES.map((s) => GROWTH_STAGE_OF_STATUS[s])).toEqual(["seed", "sprout", "flower", "fruit"]);
  });

  it("全てのコマが同じ寸法(幅 9 文字・高さ 4 行)で、揺れても位置が動かない", () => {
    for (const frames of Object.values(GROWTH_FRAMES)) {
      expect(frames.length).toBeGreaterThanOrEqual(2);
      for (const frame of frames) {
        expect(frame).toHaveLength(4);
        for (const line of frame) expect(line).toHaveLength(9);
      }
    }
  });

  it("ASCII だけで描く(絵文字・全角を使わない)", () => {
    for (const frames of Object.values(GROWTH_FRAMES)) {
      for (const line of frames.flat()) expect(line).toMatch(/^[\x20-\x7e]*$/);
    }
  });
});
