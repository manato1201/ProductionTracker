// 講義(L11・L13)で、本物の React を Node の中で動かすための小さな道具。
// frontend/node_modules の react / react-dom / jsdom を使う(先に `cd frontend && npm ci`)。
import { createRequire } from "node:module";

const require = createRequire(new URL("../../frontend/package.json", import.meta.url));
const { JSDOM } = require("jsdom");
export const React = require("react");
const { createRoot } = require("react-dom/client");

const dom = new JSDOM("<!doctype html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true; // React に「テストの中」だと伝える(状態更新を act でまとめる)

export const h = React.createElement;
export const { act } = React;

/** 時間を進める(タイマー・非同期の完了を待つ)。React の更新を act の中で反映する。 */
export const tick = (ms = 0) => act(async () => { await new Promise((resolve) => setTimeout(resolve, ms)); });

/** 要素を描画して、操作・確認のための道具を返す。 */
export async function mount(element) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(element));
  return {
    container,
    html: () => container.innerHTML,
    text: (selector = "*") => container.querySelector(selector)?.textContent,
    click: (selector) =>
      act(async () => { container.querySelector(selector).dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true })); }),
    key: (selector, key, init = {}) =>
      act(async () => { container.querySelector(selector).dispatchEvent(new dom.window.KeyboardEvent("keydown", { key, bubbles: true, ...init })); }),
    render: (next) => act(async () => root.render(next)),
    unmount: () => act(async () => root.unmount()),
  };
}
