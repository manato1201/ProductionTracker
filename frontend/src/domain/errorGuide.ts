import { ApiError } from "../api/client";

/**
 * エラーの書き方の型(使いやすさの提案 UX4): 「何が起きた / なぜ / 次にどうする」の 3 行。
 * 理由(why)は、サーバーが返した文(`detail`)があればそれを使う。次の一手(next)は、状態コードとエラーコードから決める。
 */
export interface ErrorGuide {
  what: string;
  why: string;
  next: string;
}

const CONTACT = "続くときは、管理者に伝えてください。";

/** `context` は「何をしようとしたか」(例: 「ノートを送信できませんでした。」)。分かっているときは、既定の見出しの代わりに使う。 */
export function explainError(e: unknown, context?: string): ErrorGuide {
  if (!(e instanceof ApiError)) {
    return { what: context ?? "操作できませんでした。", why: "予期しない問題が起きました。", next: `もう一度試してください。${CONTACT}` };
  }
  const { status, code, detail } = e;
  if (status === 0) {
    return { what: "サーバーに接続できません。", why: "ネットワークが切れているか、サーバーが止まっている可能性があります。", next: "接続を確かめて、画面を再読み込みしてください。" };
  }
  if (status === 401) {
    return { what: "ログインが切れました。", why: "一定時間がたつと、ログインは自動で切れます。", next: "ログインし直してください。" };
  }
  if (status === 429) {
    return { what: "操作が短い間に多すぎます。", why: detail, next: "少し待ってから、もう一度試してください。" };
  }
  if (status >= 500) {
    return { what: "サーバーで問題が起きました。", why: "入力の誤りではなく、サーバー側の問題です。", next: `しばらくしてから、再読み込みしてください。${CONTACT}` };
  }
  const what = (fallback: string) => context ?? fallback;
  if (status === 403) {
    return { what: what("この操作はできません。"), why: detail, next: "この操作に必要な役割は、プロジェクトのレビュアーに相談してください。" };
  }
  if (status === 404) {
    return { what: what("見つかりません。"), why: detail, next: "一覧に戻って、探し直してください。他の人が消した可能性もあります。" };
  }
  if (code === "invalid_transition") {
    return { what: what("状態を変更できません。"), why: detail, next: "「状態を変更」のメニューで、いまの状態から進める先を選んでください。" };
  }
  if (code === "version_required") {
    return { what: what("状態を変更できません。"), why: detail, next: "先に「版」を登録してから、もう一度「完了」にしてください。" };
  }
  if (code === "rule_violation") {
    return { what: what("状態を変更できません。"), why: detail, next: "条件を満たしてから、もう一度試してください。" };
  }
  if (code === "idempotency_conflict") {
    return { what: what("同じ要求が、別の内容で送られています。"), why: detail, next: "画面を再読み込みして、やり直してください。" };
  }
  return { what: what("入力を確認してください。"), why: detail, next: "入力を直して、もう一度送信してください。" };
}

/** トースト用の文字列(行ごとに改行)。同じ文が重なるときは省く。 */
export function guideLines(guide: ErrorGuide): string[] {
  return [guide.what, guide.why, guide.next].filter((line, i, all) => line && all.indexOf(line) === i);
}
