"""構成図を SVG で描く小さな部品(標準ライブラリのみ)。

参考にした見せ方: グループ枠 + アイコンタイル + ラベル付きの矢印 + 番号付きの手順。
図の中身は build.py に書く。ここは「どう描くか」だけを持つ。
"""

from __future__ import annotations

from html import escape

FONT = "'Hiragino Sans','Noto Sans JP','Yu Gothic UI',system-ui,sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"

INK = "#1b2230"
MUTED = "#5b6678"
LINE = "#c9d1de"
BLUE = "#0b6bf0"
RED = "#c0392b"

# グループ枠の配色: (線, 地, 見出し文字)
PALETTE = {
    "blue": ("#4a90e2", "#f3f7fd", "#1f5fb8"),
    "orange": ("#e08a3c", "#fcf6ef", "#a85a10"),
    "green": ("#3da86a", "#f2faf5", "#1d7a47"),
    "purple": ("#8a6fd6", "#f6f3fd", "#5b43a8"),
    "gray": ("#9aa5b8", "#f4f6f9", "#4d586b"),
    "red": ("#d9675a", "#fdf4f2", "#a8352a"),
}


def text_width(s: str, size: float) -> float:
    """文字幅の見積もり(全角は 1.0em、半角は 0.58em)。"""
    return sum(size * (1.0 if ord(c) > 0x2E80 else 0.58) for c in s)


def _glyph(name: str, ink: str = INK) -> str:
    """アイコン(中心 0,0、約 40x40 の範囲)。ロゴは使わず、意味が分かる単純な図形にする。"""
    s = f'fill="none" stroke="{ink}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
    g = {
        "person": f'<circle cx="0" cy="-8" r="7" {s}/><path d="M-15 17 C-15 5 15 5 15 17" {s}/>',
        "monitor": f'<rect x="-18" y="-15" width="36" height="24" rx="3" {s}/><path d="M-8 17 H8 M0 9 V17" {s}/>',
        "database": (
            f'<ellipse cx="0" cy="-11" rx="14" ry="5.5" {s}/><path d="M-14 -11 V11 C-14 17 14 17 14 11 V-11" {s}/>'
            f'<path d="M-14 0 C-14 6 14 6 14 0" {s}/>'
        ),
        "gear": (
            f'<circle cx="0" cy="0" r="6" {s}/>'
            + "".join(
                f'<path d="M0 -11 V-16" transform="rotate({a})" {s}/>' for a in range(0, 360, 45)
            )
            + f'<circle cx="0" cy="0" r="11" {s}/>'
        ),
        "shield": f'<path d="M0 -17 L15 -11 V2 C15 11 7 16 0 19 C-7 16 -15 11 -15 2 V-11 Z" {s}/><path d="M-6 1 L-1 6 L7 -4" {s}/>',
        "terminal": f'<rect x="-18" y="-14" width="36" height="28" rx="3" {s}/><path d="M-11 -5 L-5 0 L-11 5 M0 6 H9" {s}/>',
        "pulse": f'<path d="M-19 2 H-10 L-6 -10 L0 14 L5 -4 L8 2 H19" {s}/>',
        "bug": (
            f'<ellipse cx="0" cy="3" rx="8" ry="11" {s}/><path d="M-5 -9 C-5 -15 5 -15 5 -9 M-8 0 H-16 M8 0 H16 M-8 8 H-15 '
            f'M8 8 H15 M-7 -4 L-14 -9 M7 -4 L14 -9" {s}/>'
        ),
        "cloud": f'<path d="M-12 12 H11 C18 12 19 2 12 1 C13 -9 0 -13 -5 -5 C-12 -6 -17 4 -12 12 Z" {s}/>',
        "file": f'<path d="M-11 -17 H4 L12 -9 V17 H-11 Z M4 -17 V-9 H12" {s}/><path d="M-5 2 H6 M-5 8 H6" {s}/>',
        "braces": f'<path d="M-6 -16 C-12 -16 -9 -4 -14 0 C-9 4 -12 16 -6 16 M6 -16 C12 -16 9 -4 14 0 C9 4 12 16 6 16" {s}/>',
        "layers": f'<path d="M0 -15 L17 -6 L0 3 L-17 -6 Z M-17 2 L0 11 L17 2 M-17 9 L0 18 L17 9" {s}/>',
        "box": f'<path d="M0 -17 L16 -9 V9 L0 17 L-16 9 V-9 Z M-16 -9 L0 -1 L16 -9 M0 -1 V17" {s}/>',
        "kanban": (
            f'<rect x="-18" y="-15" width="10" height="30" rx="2" {s}/><rect x="-5" y="-15" width="10" height="20" rx="2" {s}/>'
            f'<rect x="8" y="-15" width="10" height="26" rx="2" {s}/>'
        ),
        "palette": (
            f'<path d="M0 -17 C-12 -17 -19 -9 -19 0 C-19 10 -10 17 -2 17 C4 17 4 11 8 11 H12 C17 11 19 8 19 3 C19 -9 11 -17 0 -17 Z" {s}/>'
            f'<circle cx="-8" cy="-4" r="2" fill="{ink}"/><circle cx="-1" cy="-9" r="2" fill="{ink}"/><circle cx="7" cy="-6" r="2" fill="{ink}"/>'
        ),
        "plug": f'<path d="M-6 -17 V-6 M6 -17 V-6 M-11 -6 H11 V2 C11 9 6 12 0 12 C-6 12 -11 9 -11 2 Z M0 12 V18" {s}/>',
        "lock": f'<rect x="-13" y="-4" width="26" height="20" rx="3" {s}/><path d="M-8 -4 V-9 C-8 -19 8 -19 8 -9 V-4" {s}/>',
        "check": f'<circle cx="0" cy="0" r="16" {s}/><path d="M-7 1 L-2 6 L8 -5" {s}/>',
        "list": f'<path d="M-14 -10 H14 M-14 0 H14 M-14 10 H14" {s}/><circle cx="-18" cy="-10" r="0.1" {s}/>',
        "link": f'<path d="M-3 5 L5 -3 M-7 -1 L-12 4 C-16 8 -10 14 -5 10 L-2 7 M7 1 L12 -4 C16 -8 10 -14 5 -10 L2 -7" {s}/>',
    }
    return g[name]


class Diagram:
    def __init__(self, width: int, height: int, title: str | None = None, grid: bool = True):
        self.w, self.h = width, height
        self.parts: list[str] = []
        self.top: list[str] = []  # 矢印のラベルと番号は最後(最前面)に描く
        self.title = title
        self.grid = grid

    # --- 部品 ---------------------------------------------------------------
    def group(self, x, y, w, h, title, subtitle="", color="blue", dashed=False):
        line, fill, ink = PALETTE[color]
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{line}" stroke-width="1.6"{dash}/>'
        )
        label_w = text_width(title, 14) + 24
        self.parts.append(f'<rect x="{x + 18}" y="{y - 12}" width="{label_w}" height="24" fill="#fff" rx="4"/>')
        self.parts.append(
            f'<text x="{x + 30}" y="{y + 5}" font-size="14" font-weight="700" fill="{ink}" font-family="{FONT}">{escape(title)}</text>'
        )
        if subtitle:
            self.parts.append(
                f'<text x="{x + 30}" y="{y + 28}" font-size="11.5" fill="{MUTED}" font-family="{MONO}">{escape(subtitle)}</text>'
            )

    def tile(self, cx, cy, title, subtitle="", icon="gear", dashed=False, accent=INK, size=64):
        """アイコンタイル + 題名 + 等幅の副題(参考画像と同じ構成)。(cx, cy) はタイル中心。"""
        x, y = cx - size / 2, cy - size / 2
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12" fill="#fff" stroke="{LINE}" stroke-width="1.6"{dash}/>'
        )
        self.parts.append(f'<g transform="translate({cx},{cy}) scale({size / 64 * 0.9})">{_glyph(icon, accent)}</g>')
        ty = cy + size / 2 + 20
        self.parts.append(
            f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}" '
            f'font-family="{FONT}" paint-order="stroke" stroke="#fff" stroke-width="4">{escape(title)}</text>'
        )
        for i, line in enumerate(subtitle.split("\n") if subtitle else []):
            self.parts.append(
                f'<text x="{cx}" y="{ty + 17 + i * 15}" text-anchor="middle" font-size="11" fill="{MUTED}" '
                f'font-family="{MONO if line.isascii() else FONT}" paint-order="stroke" stroke="#fff" stroke-width="4">{escape(line)}</text>'
            )

    def box(self, x, y, w, h, title, lines=(), color="blue", mono=True):
        """モジュールの箱(コード構成図向け)。"""
        line, fill, ink = PALETTE[color]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#fff" stroke="{line}" stroke-width="1.6"/>')
        self.parts.append(
            f'<text x="{x + 14}" y="{y + 23}" font-size="13.5" font-weight="700" fill="{ink}" font-family="{MONO if mono else FONT}">{escape(title)}</text>'
        )
        for i, ln in enumerate(lines):
            self.parts.append(
                f'<text x="{x + 14}" y="{y + 43 + i * 17}" font-size="12" fill="{MUTED}" font-family="{FONT}">{escape(ln)}</text>'
            )

    def edge(self, points, label="", color=BLUE, dashed=False, arrow=True, both=False, label_at=0.5, label_color=None):
        """折れ線の矢印。points = [(x, y), ...]。ラベルは線の上に白地で載せる。"""
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        pts = " ".join(f"{x},{y}" for x, y in points)
        mid = "url(#arrow-%s)" % color.lstrip("#")
        start = "url(#arrow-start-%s)" % color.lstrip("#") if both else ""
        self.parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"{dash} stroke-linejoin="round"'
            + (f' marker-end="{mid}"' if arrow else "")
            + (f' marker-start="{start}"' if both else "")
            + "/>"
        )
        if label:
            x, y = self._point_on(points, label_at)
            w = text_width(label, 12) + 14
            self.top.append(f'<rect x="{x - w / 2}" y="{y - 11}" width="{w}" height="22" rx="4" fill="#fff" fill-opacity="0.95"/>')
            self.top.append(
                f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="12" fill="{label_color or color}" '
                f'font-family="{MONO if label.isascii() else FONT}">{escape(label)}</text>'
            )

    @staticmethod
    def _point_on(points, t):
        segs = [(points[i], points[i + 1]) for i in range(len(points) - 1)]
        lens = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in segs]
        target = sum(lens) * t
        for (a, b), ln in zip(segs, lens):
            if target <= ln or (a, b) == segs[-1]:
                f = 0 if ln == 0 else target / ln
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            target -= ln
        return points[0]

    def step(self, n, x, y, color=BLUE):
        """番号付きの丸(手順)。"""
        self.top.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{color}"/>')
        self.top.append(
            f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="13" font-weight="700" fill="#fff" font-family="{FONT}">{n}</text>'
        )

    def note(self, x, y, text, color=MUTED, size=12.5, anchor="start", bold=False, mono=False):
        for i, line in enumerate(text.split("\n")):
            self.top.append(
                f'<text x="{x}" y="{y + i * (size + 5)}" text-anchor="{anchor}" font-size="{size}" fill="{color}" '
                f'font-weight="{700 if bold else 400}" font-family="{MONO if mono else FONT}">{escape(line)}</text>'
            )

    def pill(self, x, y, text, color=BLUE, w=None):
        w = w or text_width(text, 12.5) + 22
        self.top.append(f'<rect x="{x}" y="{y}" width="{w}" height="26" rx="13" fill="#fff" stroke="{color}" stroke-width="1.6"/>')
        self.top.append(
            f'<text x="{x + w / 2}" y="{y + 17.5}" text-anchor="middle" font-size="12.5" font-weight="600" fill="{color}" font-family="{FONT}">{escape(text)}</text>'
        )

    # --- 出力 ---------------------------------------------------------------
    def svg(self) -> str:
        colors = sorted({BLUE, RED, MUTED, "#8a94a6", "#3da86a", "#e08a3c"})  # 順序を固定(生成のたびに差分が出ないように)
        defs = "".join(
            f'<marker id="arrow-{c.lstrip("#")}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 Z" fill="{c}"/></marker>'
            f'<marker id="arrow-start-{c.lstrip("#")}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
            f'<path d="M10 0 L0 5 L10 10 Z" fill="{c}"/></marker>'
            for c in colors
        )
        grid = (
            '<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0 H0 V24" fill="none" stroke="#e8edf5" stroke-width="1"/></pattern>'
            if self.grid
            else ""
        )
        bg = f'<rect width="{self.w}" height="{self.h}" fill="#f9fbfe"/>' + (
            f'<rect width="{self.w}" height="{self.h}" fill="url(#grid)"/>' if self.grid else ""
        )
        title = (
            f'<text x="28" y="40" font-size="20" font-weight="800" fill="{INK}" font-family="{FONT}">{escape(self.title)}</text>'
            if self.title
            else ""
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img"'
            + (f' aria-label="{escape(self.title)}"' if self.title else "")
            + f"><defs>{defs}{grid}</defs>{bg}{title}"
            + "".join(self.parts)
            + "".join(self.top)
            + "</svg>\n"
        )
