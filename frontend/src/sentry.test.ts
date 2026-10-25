import { scrubEvent } from "./sentry";

it("認証情報・クッキー・本文を取り除く", () => {
  const event = {
    request: {
      headers: { Authorization: "Token abc", "X-CSRFToken": "t", Accept: "*/*" },
      cookies: { sessionid: "1" },
      data: "secret",
    },
  } as never;
  const out = JSON.stringify(scrubEvent(event));
  expect(out).not.toContain("Token abc");
  expect(out).not.toContain("sessionid");
  expect(out).not.toContain("secret");
  expect(out).toContain("*/*");
});
