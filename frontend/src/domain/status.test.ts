import { adjacentStatus, TASK_STATUS_META, TASK_STATUSES } from "./status";

describe("adjacentStatus", () => {
  it("列の並び順で隣の状態を返す", () => {
    expect(adjacentStatus("todo", 1)).toBe("in_progress");
    expect(adjacentStatus("review", 1)).toBe("done");
    expect(adjacentStatus("review", -1)).toBe("in_progress");
  });
  it("端では null", () => {
    expect(adjacentStatus("todo", -1)).toBeNull();
    expect(adjacentStatus("done", 1)).toBeNull();
  });
});

describe("状態の一覧", () => {
  it("並び順はかんばんの列順(META の定義順)", () => {
    expect(TASK_STATUSES).toEqual(["todo", "in_progress", "review", "done"]);
  });
});

describe("状態の見た目", () => {
  it("全ての状態に文字とアイコンがある(色だけにしない)", () => {
    for (const s of TASK_STATUSES) {
      expect(TASK_STATUS_META[s].label.length).toBeGreaterThan(0);
      expect(TASK_STATUS_META[s].Icon).toBeDefined();
    }
  });
  it("ラベルは重複しない", () => {
    const labels = TASK_STATUSES.map((s) => TASK_STATUS_META[s].label);
    expect(new Set(labels).size).toBe(labels.length);
  });
});
