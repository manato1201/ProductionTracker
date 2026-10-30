#!/usr/bin/env python3
"""Markdown の文書(README・docs/)から、HTML 版を作る。

    python docs/tools/build_html.py            # docs/html/ に HTML を作り直す
    python docs/tools/build_html.py --check    # 作らずに、古くなっていないか・リンク切れが無いかだけ確かめる

- 変換は `markdown-it-py`(CommonMark 準拠。GitHub と同じ見え方になる)。
- mermaid の図は、ブラウザ(Playwright)で**事前に SVG へ描画して埋め込む**。HTML 版は JavaScript なしで読める。
  (描画には `docs/tools/node_modules` の mermaid が要る。`cd docs/tools && npm install`)
- 出力は毎回同じ(日時などを入れない)。直していないのに差分が出たら、再現性が壊れている。
- 全ての HTML に、元の Markdown(と目次の構成)のハッシュを埋め込む。`--check` は、それが古くなっていないかを見る
  (mermaid の描画を使わないので、どの環境でも走る。`backend/tracker/tests/test_docs.py` が呼ぶ)。
- 検査: 相対リンク・画像・見出しへのリンクが切れていないこと、全ての Markdown が目次(GROUPS)に載っていること。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight as pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent.parent
OUT = ROOT / "docs" / "html"
CACHE = TOOLS / ".cache" / "mermaid"
BUILDER_VERSION = "3"  # 見た目や変換を変えたら上げる(HTML のハッシュが変わり、再生成が必要になる)
MERMAID_VERSION = "11.17.2"


# ---------------------------------------------------------------------------
# 目次(読む順)。ここに無い Markdown があるとエラーにする(HTML 版の作り忘れを防ぐ)。
# ---------------------------------------------------------------------------
def lecture_files() -> list[str]:
    files = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs" / "lectures").glob("*.md"))
    files = [f for f in files if not f.endswith("/README.md")]
    return ["docs/lectures/README.md", *files]


def groups() -> list[tuple[str, list[str]]]:
    learning = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs" / "learning").glob("*.md"))
    learning = [f for f in learning if not f.endswith("/README.md")]
    return [
        ("はじめに", ["README.md"]),
        ("講義(基礎から)", lecture_files()),
        ("実践ガイド(保守・拡張)", ["docs/learning/README.md", *learning]),
        (
            "設計・仕様",
            [
                "docs/ui-rules.md", "docs/er.md", "docs/integration.md", "docs/auth.md", "docs/security.md",
                "docs/database.md", "docs/operations.md", "docs/decisions.md", "docs/learning-log.md",
            ],
        ),
        ("図", ["docs/diagrams/README.md"]),
    ]


def all_sources() -> list[str]:
    return [f for _, files in groups() for f in files]


def out_path(src: str) -> Path:
    if src == "README.md":
        return OUT / "README.html"
    rel = Path(src).relative_to("docs")
    return OUT / rel.with_suffix(".html")


# ---------------------------------------------------------------------------
# 見出し ID(GitHub と同じ規則。Markdown 側の `#...` リンクがそのまま使えるように)
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    text = re.sub(r"[`*]", "", text.strip().lower())
    text = re.sub(r"[^\w\s\-぀-鿿]", "", text)
    return re.sub(r"\s", "-", text)


def new_parser() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "highlight": highlight_code}).enable("table").enable("strikethrough")
    md.use(anchors_plugin, min_level=1, max_level=4, slug_func=slugify, permalink=False)
    md.use(tasklists_plugin, enabled=False)
    return md


def highlight_code(code: str, lang: str, attrs: str) -> str:
    lang = (lang or "").strip().split()[0] if lang else ""
    try:
        lexer = get_lexer_by_name({"tsx": "tsx", "ts": "typescript", "sh": "bash", "text": "text"}.get(lang, lang)) if lang else None
    except ClassNotFound:
        lexer = None
    if lexer is None or lang in ("text", ""):
        body = html.escape(code)
    else:
        body = pygments_highlight(code, lexer, HtmlFormatter(nowrap=True))
    cls = f' class="language-{html.escape(lang)}"' if lang else ""
    return f'<pre class="highlight"><code{cls}>{body}</code></pre>\n'


# ---------------------------------------------------------------------------
# mermaid
# ---------------------------------------------------------------------------
MERMAID_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)


def mermaid_hash(code: str) -> str:
    return hashlib.sha256(f"{MERMAID_VERSION}\n{code}".encode()).hexdigest()[:16]


def extract_mermaid(text: str) -> tuple[str, dict[str, str]]:
    blocks: dict[str, str] = {}

    def repl(m: re.Match) -> str:
        code = m.group(1)
        h = mermaid_hash(code)
        blocks[h] = code
        return f"\n\nMERMAIDBLOCK{h}END\n\n"

    return MERMAID_RE.sub(repl, text), blocks


def render_missing_mermaid(blocks: dict[str, str]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    missing = [{"hash": h, "code": c} for h, c in blocks.items() if not (CACHE / f"{h}.svg").exists()]
    if not missing:
        return
    if not (TOOLS / "node_modules" / "mermaid").exists():
        sys.exit("mermaid が入っていません。  cd docs/tools && npm install")
    tmp = CACHE / "_input.json"
    tmp.write_text(json.dumps(missing, ensure_ascii=False), encoding="utf-8")
    try:
        subprocess.run(["node", str(TOOLS / "render_mermaid.mjs"), str(tmp), str(CACHE)], check=True, timeout=600)
    except subprocess.CalledProcessError:
        sys.exit("mermaid の描画に失敗しました(上のエラーを見る)")
    finally:
        tmp.unlink(missing_ok=True)


def figure_for(h: str, render: bool) -> str:
    if not render:
        return f'<figure class="diagram" data-mermaid="{h}"></figure>'
    svg = (CACHE / f"{h}.svg").read_text(encoding="utf-8").strip()
    return f'<figure class="diagram">{svg}</figure>'


# ---------------------------------------------------------------------------
# 文書の変換
# ---------------------------------------------------------------------------
class Doc:
    def __init__(self, src: str):
        self.src = src
        self.path = ROOT / src
        self.text = self.path.read_text(encoding="utf-8")
        self.body_text, self.mermaid = extract_mermaid(self.text)
        self.md = new_parser()
        self.tokens = self.md.parse(self.body_text)
        self.title = self._title()
        self.headings = self._headings()

    def _title(self) -> str:
        for i, t in enumerate(self.tokens):
            if t.type == "heading_open" and t.tag == "h1":
                return self.tokens[i + 1].content.replace("`", "")
        return Path(self.src).stem

    def _headings(self) -> list[tuple[int, str, str]]:
        out = []
        for i, t in enumerate(self.tokens):
            if t.type == "heading_open":
                out.append((int(t.tag[1]), self.tokens[i + 1].content.replace("`", ""), t.attrs.get("id", "")))
        return out


def site_hash(docs: dict[str, Doc]) -> str:
    """目次(どの文書が何という題名で、どの順に並ぶか)のハッシュ。サイドバーが変わると、全ての HTML が古くなる。"""
    payload = json.dumps([(g, [(f, docs[f].title) for f in files]) for g, files in groups()], ensure_ascii=False)
    return hashlib.sha256((BUILDER_VERSION + payload).encode()).hexdigest()[:16]


def doc_hash(doc: Doc, site: str) -> str:
    return hashlib.sha256((site + "\n" + doc.text).encode()).hexdigest()[:20]


LINK_RE = re.compile(r'(<a\s[^>]*?href=|<img\s[^>]*?src=)"([^"]+)"')


def rewrite_links(body: str, doc: Doc, docs: dict[str, Doc], here: Path, errors: list[str]) -> str:
    def repl(m: re.Match) -> str:
        prefix, target = m.group(1), html.unescape(m.group(2))
        if re.match(r"^(https?:|mailto:|data:)", target):
            return m.group(0)
        path_part, _, frag = target.partition("#")
        if not path_part:  # 同じ文書内の見出し
            if frag and unquote(frag) not in {h[2] for h in doc.headings}:
                errors.append(f"{doc.src}: 見出し #{unquote(frag)} が無い")
            return m.group(0)
        resolved = (doc.path.parent / unquote(path_part)).resolve()
        try:
            rel_repo = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            errors.append(f"{doc.src}: リポジトリの外を指している: {target}")
            return m.group(0)
        if not resolved.exists():
            errors.append(f"{doc.src}: リンク先が無い: {target}")
            return m.group(0)
        if rel_repo.endswith(".md") and rel_repo in docs:
            new = os.path.relpath(out_path(rel_repo), here.parent).replace(os.sep, "/")
            if frag and unquote(frag) not in {h[2] for h in docs[rel_repo].headings}:
                errors.append(f"{doc.src}: {rel_repo} に見出し #{unquote(frag)} が無い")
        else:
            new = os.path.relpath(resolved, here.parent).replace(os.sep, "/")
        new = new + (f"#{frag}" if frag else "")
        return f'{prefix}"{html.escape(new)}"'

    return LINK_RE.sub(repl, body)


def toc_html(doc: Doc) -> str:
    items = [(lvl, text, anchor) for lvl, text, anchor in doc.headings if lvl in (2, 3)]
    if len(items) < 3:
        return ""
    lis = "".join(
        f'<li class="lvl{lvl}"><a href="#{html.escape(a)}">{html.escape(t)}</a></li>' for lvl, t, a in items
    )
    return f'<nav class="toc" aria-label="この文書の目次"><h2>目次</h2><ul>{lis}</ul></nav>'


def sidebar_html(current: str, here: Path) -> str:
    parts = []
    for gname, files in groups():
        lis = []
        for f in files:
            href = os.path.relpath(out_path(f), here.parent).replace(os.sep, "/")
            title = DOCS[f].title
            cur = ' aria-current="page" class="current"' if f == current else ""
            lis.append(f'<li><a href="{html.escape(href)}"{cur}>{html.escape(title)}</a></li>')
        parts.append(f'<details open><summary>{html.escape(gname)}</summary><ul>{"".join(lis)}</ul></details>')
    return "".join(parts)


def prev_next_html(current: str, here: Path) -> str:
    for _, files in groups():
        if current in files:
            i = files.index(current)
            def link(f: str, label: str, cls: str) -> str:
                href = os.path.relpath(out_path(f), here.parent).replace(os.sep, "/")
                return f'<a class="{cls}" href="{html.escape(href)}"><span>{label}</span>{html.escape(DOCS[f].title)}</a>'
            prev = link(files[i - 1], "← 前へ", "prev") if i > 0 else "<span></span>"
            nxt = link(files[i + 1], "次へ →", "next") if i < len(files) - 1 else "<span></span>"
            return f'<nav class="pager">{prev}{nxt}</nav>'
    return ""


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-source-sha256" content="{hash}">
<title>{title} — ProductionTracker</title>
<link rel="stylesheet" href="{css}">
<script src="{js}" defer></script>
</head>
<body>
<a class="skip" href="#main">本文へ</a>
<header class="top">
  <a class="brand" href="{index}">ProductionTracker <span>ドキュメント</span></a>
  <button id="theme-toggle" type="button" aria-label="テーマを切り替える">◐</button>
</header>
<div class="layout">
  <aside class="sidebar" aria-label="文書の一覧">{sidebar}</aside>
  <main id="main">
    <p class="source">元の Markdown: <a href="{src_href}"><code>{src}</code></a></p>
    <article class="doc">{body}</article>
    {pager}
  </main>
  {toc}
</div>
</body>
</html>
"""


def build_page(src: str, docs: dict[str, Doc], render: bool, errors: list[str], site: str) -> str:
    doc = docs[src]
    here = out_path(src)
    body = doc.md.renderer.render(doc.tokens, doc.md.options, {})
    for h in doc.mermaid:
        body = re.sub(rf"<p>MERMAIDBLOCK{h}END</p>", lambda _m, h=h: figure_for(h, render), body)
    body = rewrite_links(body, doc, docs, here, errors)
    rel = lambda p: os.path.relpath(p, here.parent).replace(os.sep, "/")  # noqa: E731
    return PAGE.format(
        hash=doc_hash(doc, site),
        title=html.escape(doc.title),
        css=rel(OUT / "assets" / "style.css"),
        js=rel(OUT / "assets" / "theme.js"),
        index=rel(OUT / "index.html"),
        sidebar=sidebar_html(src, here),
        src_href=rel(doc.path),
        src=html.escape(src),
        body=body,
        pager=prev_next_html(src, here),
        toc=toc_html(doc),
    )


DESCRIPTIONS = {
    "README.md": "プロジェクトの概要・起動方法・API・検証結果",
    "docs/lectures/README.md": "基礎から順に学ぶ講義資料。コードは実行して確かめる",
    "docs/learning/README.md": "保守・拡張の手順書。レシピ・テスト・トラブルシューティング",
    "docs/ui-rules.md": "色・状態の見せ方・モーションの決めごと",
    "docs/er.md": "データモデルと制約",
    "docs/integration.md": "取り込み・監視・Publish の API の契約",
    "docs/auth.md": "認証の種類と、Cloudflare Access の使い方",
    "docs/security.md": "OWASP API Top 10 での点検結果",
    "docs/database.md": "SQL の指針での点検結果",
    "docs/operations.md": "バックアップ・復元・更新・公開",
    "docs/decisions.md": "選んだ理由・設計書から外れた点",
    "docs/learning-log.md": "詰まった点と教訓",
    "docs/diagrams/README.md": "図の作り方(SVG は build.py から生成)",
}


def build_index(docs: dict[str, Doc], site: str) -> str:
    here = OUT / "index.html"
    rel = lambda p: os.path.relpath(p, here.parent).replace(os.sep, "/")  # noqa: E731
    sections = []
    for gname, files in groups():
        cards = "".join(
            f'<li><a href="{html.escape(rel(out_path(f)))}"><strong>{html.escape(docs[f].title)}</strong>'
            f'<span>{html.escape(DESCRIPTIONS.get(f, ""))}</span></a></li>'
            for f in files
        )
        sections.append(f"<h2>{html.escape(gname)}</h2><ul class=\"cards\">{cards}</ul>")
    body = "<h1>ProductionTracker ドキュメント</h1><p>制作進行管理アプリ(Django + React)の設計・運用・学習資料の HTML 版です。同じ内容が Markdown(mermaid 記法つき)にもあります。</p>" + "".join(sections)
    digest = hashlib.sha256((site + "index").encode()).hexdigest()[:20]
    return PAGE.format(
        hash=digest, title="ドキュメント", css=rel(OUT / "assets" / "style.css"), js=rel(OUT / "assets" / "theme.js"),
        index=rel(here), sidebar=sidebar_html("", here), src_href=rel(ROOT / "README.md"), src="README.md",
        body=body, pager="", toc="",
    ).replace('<p class="source">元の Markdown: <a href="' + rel(ROOT / "README.md") + '"><code>README.md</code></a></p>', "")


# ---------------------------------------------------------------------------
# 見た目(CSS / JS)
# ---------------------------------------------------------------------------
def style_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="native").get_style_defs('[data-theme="dark"] .highlight')
    auto_dark = HtmlFormatter(style="native").get_style_defs(':root:not([data-theme="light"]) .highlight')
    base = (TOOLS / "assets" / "style.base.css").read_text(encoding="utf-8")
    return f"{base}\n/* --- コードの色(pygments) --- */\n{light}\n@media (prefers-color-scheme: dark) {{\n{auto_dark}\n}}\n{dark}\n"


def write_assets() -> None:
    assets = OUT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "style.css").write_text(style_css(), encoding="utf-8")
    (assets / "theme.js").write_text((TOOLS / "assets" / "theme.js").read_text(encoding="utf-8"), encoding="utf-8")


DOCS: dict[str, Doc] = {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="作らずに、古くなっていないか・リンク切れが無いかだけ確かめる")
    args = ap.parse_args(argv)

    listed = set(all_sources())
    on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "docs").rglob("*.md") if "node_modules" not in p.parts and "html" not in p.relative_to(ROOT / "docs").parts[:1]}
    on_disk.add("README.md")
    problems: list[str] = []
    for f in sorted(on_disk - listed):
        problems.append(f"{f} が目次(build_html.py の groups)に載っていない")
    for f in sorted(listed - on_disk):
        problems.append(f"{f} が目次にあるが、ファイルが無い")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    DOCS.clear()
    DOCS.update({f: Doc(f) for f in all_sources()})
    site = site_hash(DOCS)
    errors: list[str] = []

    if args.check:
        stale = []
        for f in all_sources():
            target = out_path(f)
            expected = f'content="{doc_hash(DOCS[f], site)}"'
            if not target.exists() or expected not in target.read_text(encoding="utf-8")[:600]:
                stale.append(f)
            build_page(f, DOCS, False, errors, site)  # リンク・見出しの検査だけ
        index = OUT / "index.html"
        if not index.exists() or f'content="{hashlib.sha256((site + "index").encode()).hexdigest()[:20]}"' not in index.read_text(encoding="utf-8")[:600]:
            stale.append("index.html")
        for e in errors:
            print("リンク切れ:", e, file=sys.stderr)
        for f in stale:
            print(f"HTML が古い: {f}  →  python docs/tools/build_html.py", file=sys.stderr)
        return 1 if (errors or stale) else 0

    blocks = {h: c for d in DOCS.values() for h, c in d.mermaid.items()}
    render_missing_mermaid(blocks)
    write_assets()
    for f in all_sources():
        target = out_path(f)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_page(f, DOCS, True, errors, site), encoding="utf-8")
    (OUT / "index.html").write_text(build_index(DOCS, site), encoding="utf-8")
    for e in errors:
        print("リンク切れ:", e, file=sys.stderr)
    print(f"{len(DOCS)} 文書 + 目次を {OUT.relative_to(ROOT)}/ に作りました(mermaid の図 {len(blocks)} 枚)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
