import { formatDate, formatDiffRatio, formatPercent, symbolOf } from "./format";

describe("format", () => {
  it("日付のみの値は時間帯の影響を受けずそのまま返す", () => {
    expect(formatDate("2026-10-11")).toBe("2026-10-11");
  });
  it("空は —", () => {
    expect(formatDate(null)).toBe("—");
  });
  it("日時は YYYY-MM-DD にそろえる", () => {
    expect(formatDate("2026-10-11T12:00:00+09:00")).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
  it("割合", () => {
    expect(formatPercent(0.4286)).toBe("43%");
    expect(formatDiffRatio(0.0132)).toBe("1.32%");
  });
  it("記号", () => {
    expect(symbolOf("demo")).toBe("DE");
  });
});
