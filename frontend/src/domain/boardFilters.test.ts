import { hasFilter, NO_FILTERS, parseFilters, writeFilters } from "./boardFilters";

const params = (s: string) => new URLSearchParams(s);

describe("かんばんの絞り込み(URL)", () => {
  it("URL から読む", () => {
    expect(parseFilters(params("assignee=me&priority=high,urgent&overdue=1&q=crate"))).toEqual({
      assignee: "me", priorities: ["high", "urgent"], overdueOnly: true, q: "crate",
    });
  });

  it("何も無ければ絞り込みなし", () => {
    expect(parseFilters(params(""))).toEqual(NO_FILTERS);
    expect(hasFilter(NO_FILTERS)).toBe(false);
  });

  it("知らない値・重複・長すぎる検索語は無視/切り詰め(共有リンクが壊れていても画面は開く)", () => {
    const f = parseFilters(params(`assignee=everyone&priority=high,high,bogus,&overdue=yes&q=${"x".repeat(500)}`));
    expect(f.assignee).toBe("all");
    expect(f.priorities).toEqual(["high"]);
    expect(f.overdueOnly).toBe(false);
    expect(f.q).toHaveLength(100);
  });

  it("書き出すとき、既定の値は載せず、絞り込み以外(task)は残す", () => {
    const next = writeFilters(params("task=12&assignee=me&q=old"), { ...NO_FILTERS, priorities: ["urgent"] });
    expect(next.toString()).toBe("task=12&priority=urgent");
  });

  it("書いて読むと元に戻る(往復)", () => {
    const f = { assignee: "none", priorities: ["low", "high"], overdueOnly: true, q: "木箱 & 椅子" } as const;
    expect(parseFilters(writeFilters(params(""), { ...f, priorities: [...f.priorities] }))).toEqual(f);
  });
});
