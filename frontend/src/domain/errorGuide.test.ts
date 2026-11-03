import { ApiError } from "../api/client";
import { explainError, guideLines } from "./errorGuide";

describe("explainError(何が起きた / なぜ / 次にどうする)", () => {
  it("接続できないときは、ネットワークの確認を促す", () => {
    const g = explainError(new ApiError(0, "network_error", "サーバーに接続できません。"));
    expect(g.what).toBe("サーバーに接続できません。");
    expect(g.next).toContain("再読み込み");
  });

  it("401 はログインし直し、429 は待つ、5xx はサーバー側の問題と伝える", () => {
    expect(explainError(new ApiError(401, "not_authenticated", "x")).next).toContain("ログインし直して");
    expect(explainError(new ApiError(429, "throttled", "しばらくしてください")).next).toContain("待って");
    const g = explainError(new ApiError(500, "error", "内部情報"));
    expect(g.why).toContain("サーバー側");
    expect(JSON.stringify(g)).not.toContain("内部情報"); // 5xx の本文は画面に出さない
  });

  it("理由はサーバーが返した文をそのまま使う(遷移の拒否)", () => {
    const g = explainError(new ApiError(409, "invalid_transition", "「未着手」から「完了」へは変更できません。"));
    expect(g.why).toBe("「未着手」から「完了」へは変更できません。");
    expect(g.next).toContain("状態を変更");
  });

  it("「完了」に版が要るときは、版の登録を促す", () => {
    const g = explainError(new ApiError(409, "version_required", "「完了」にするには、版が1つ以上必要です。"));
    expect(g.next).toContain("版");
  });

  it("403 は役割の相談を促す。context があれば見出しに使う", () => {
    const g = explainError(new ApiError(403, "permission_denied", "承認はレビュアーだけです。"), "状態を変更できませんでした。");
    expect(g.what).toBe("状態を変更できませんでした。");
    expect(g.next).toContain("レビュアー");
  });

  it("ApiError 以外(想定外の例外)でも、3 行そろう", () => {
    const g = explainError(new TypeError("x"), "ノートを送信できませんでした。");
    expect(g.what).toBe("ノートを送信できませんでした。");
    expect(g.why && g.next).toBeTruthy();
  });

  it("guideLines は、同じ文が重なるときに 1 つにする", () => {
    expect(guideLines({ what: "A", why: "A", next: "B" })).toEqual(["A", "B"]);
  });
});
