import { ApiError, readCookie, request, withQuery } from "./client";

describe("withQuery", () => {
  it("空の値は付けない", () => {
    expect(withQuery("/tasks/", { status: "todo", q: "", entity: undefined, page: 2 })).toBe("/tasks/?status=todo&page=2");
    expect(withQuery("/tasks/")).toBe("/tasks/");
  });
});

describe("readCookie", () => {
  it("名前で値を取り出す", () => {
    expect(readCookie("csrftoken", "a=1; csrftoken=xyz; b=2")).toBe("xyz");
    expect(readCookie("missing", "a=1")).toBeNull();
  });
});

describe("request", () => {
  afterEach(() => vi.restoreAllMocks());

  it("統一エラー形式を ApiError にする(409 の理由を画面に出せる)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ code: "invalid_transition", detail: "「未着手」から「完了」へは移行できません。" }), { status: 409 }),
    );
    await expect(request("POST", "/tasks/1/transition/", { to: "done" })).rejects.toMatchObject({
      status: 409,
      code: "invalid_transition",
      detail: "「未着手」から「完了」へは移行できません。",
    });
  });

  it("変更系には CSRF ヘッダを付ける", async () => {
    document.cookie = "csrftoken=tok123";
    const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response("{}", { status: 200 }));
    await request("POST", "/x/", {});
    const init = spy.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>)["X-CSRFToken"]).toBe("tok123");
    await request("GET", "/x/");
    expect(((spy.mock.calls[1][1] as RequestInit).headers as Record<string, string>)["X-CSRFToken"]).toBeUndefined();
  });

  it("接続できないときは network_error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fail"));
    await expect(request("GET", "/x/")).rejects.toBeInstanceOf(ApiError);
  });

  it("JSON でない応答でも落ちない", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("<html>", { status: 502 }));
    await expect(request("GET", "/x/")).rejects.toMatchObject({ status: 502 });
  });
});
