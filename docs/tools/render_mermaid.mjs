// mermaid の図を SVG にする。  使い方: node render_mermaid.mjs <入力 JSON> <出力ディレクトリ>
//   入力 JSON: [{"hash": "...", "code": "flowchart LR ..."}, ...]
//   出力: <出力ディレクトリ>/<hash>.svg(同じ入力は毎回同じ SVG になる)
// ブラウザは Playwright の Chromium を使う(HTML 版を JavaScript なしで読めるよう、事前に描画しておく)。
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const [inputPath, outDir] = process.argv.slice(2);
const items = JSON.parse(fs.readFileSync(inputPath, "utf8"));
fs.mkdirSync(outDir, { recursive: true });

const FONT = "'Hiragino Sans','Noto Sans JP','Yu Gothic UI',system-ui,sans-serif";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
await page.setContent(`<html><body style="font-family:${FONT}"><div id="root"></div></body></html>`);
await page.addScriptTag({ path: path.join(here, "node_modules/mermaid/dist/mermaid.min.js") });
await page.evaluate((font) => {
  window.mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "neutral",
    fontFamily: font,
    flowchart: { htmlLabels: false, curve: "basis", useMaxWidth: true },
    sequence: { useMaxWidth: true, wrap: true },
    er: { useMaxWidth: true },
    state: { useMaxWidth: true },
  });
}, FONT);

let failed = 0;
for (const { hash, code } of items) {
  const result = await page.evaluate(async ({ hash, code }) => {
    try {
      const { svg } = await window.mermaid.render(`m${hash}`, code);
      return { svg };
    } catch (e) {
      return { error: String(e && e.message ? e.message : e) };
    }
  }, { hash, code });
  if (result.error) {
    failed++;
    console.error(`mermaid の構文エラー (${hash}):\n${result.error}\n--- コード ---\n${code}\n`);
    continue;
  }
  fs.writeFileSync(path.join(outDir, `${hash}.svg`), result.svg + "\n", "utf8");
}
await browser.close();
process.exit(failed ? 1 : 0);
