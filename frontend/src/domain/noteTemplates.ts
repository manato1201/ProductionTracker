/** ノートの定型項目(追補 T2)。押すと入力欄の末尾に見出しを足す。内容は自由に書く。 */
export const NOTE_TEMPLATES = ["見るポイント:", "使うときの注意:"] as const;

/** 末尾が改行でなければ改行を挟み、同じ見出しが既にあれば足さない。 */
export function insertTemplate(body: string, template: string): string {
  if (body.split("\n").some((line) => line.startsWith(template))) return body;
  const sep = body === "" || body.endsWith("\n") ? "" : "\n";
  return `${body}${sep}${template} `;
}
