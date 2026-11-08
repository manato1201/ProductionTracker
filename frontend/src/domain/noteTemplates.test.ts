import { insertTemplate } from "./noteTemplates";

describe("insertTemplate", () => {
  it("空の入力欄には見出しだけを足す", () => {
    expect(insertTemplate("", "見るポイント:")).toBe("見るポイント: ");
  });
  it("本文の後ろでは改行を挟む", () => {
    expect(insertTemplate("よろしく", "見るポイント:")).toBe("よろしく\n見るポイント: ");
    expect(insertTemplate("よろしく\n", "見るポイント:")).toBe("よろしく\n見るポイント: ");
  });
  it("同じ見出しが既にあれば足さない", () => {
    const body = "見るポイント: 影";
    expect(insertTemplate(body, "見るポイント:")).toBe(body);
  });
});
