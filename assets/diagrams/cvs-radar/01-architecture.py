# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
import diagram_kit as _dk
_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P, MUTE

from pathlib import Path

import cairosvg
from PIL import Image


W, H = 1870, 790
OUT = Path(__file__).resolve().parent
SVG = OUT / "01-architecture.svg"
PNG = OUT / "01-architecture.png"

s = [svg_head(W, H)]
s.append(title_block(
    "CVS-RADAR · ARCHITECTURE",
    P["sky"][1],
    "系統架構",
    "從 PTT 公開討論到靜態網站的批次管線",
))

cw, ch, y = 300, 205, 355
xs = [65, 425, 785, 1145, 1505]
mid = ch // 2

cards = [
    ("sky", "爬取", ["PTT CVS 板", "每日增量抓取"]),
    ("teal", "LLM 標記", ["情緒 · 商品名", "摘句 · 代表留言", "結果存指紋快取"]),
    ("amber", "評分", ["每人一票 · 排除自推", "貝氏收斂 · 時間衰減"]),
    ("rose", "資料建置", ["商品層級欄位", "去識別化快照"]),
    ("violet", "靜態網站", ["Next.js 靜態匯出", "Vercel + Pages"]),
]
for x, data in zip(xs, cards):
    s.append(card(x, y, cw, ch, *data))
for a, b in zip(xs, xs[1:]):
    s.append(arrow(a + cw + 6, y + mid, b - 10, y + mid))


def bracket(x1, x2, y_base, label, color):
    """Horizontal bracket above a group of cards, with a centred label."""
    drop = 18
    return (
        f'<path d="M{x1},{y_base} v{drop} h{x2 - x1} v-{drop}" fill="none" '
        f'stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>'
        f'<text x="{(x1 + x2) / 2}" y="{y_base - 14}" font-size="24" font-weight="bold" '
        f'text-anchor="middle" fill="{color}">{label}</text>'
    )


s.append(bracket(xs[0], xs[3] + cw, y - 42, "本機排程每日重算", P["teal"][1]))
s.append(bracket(xs[4], xs[4] + cw, y - 42, "push main 觸發部署", P["violet"][1]))

s.append(
    f'<text x="65" y="{y + ch + 76}" font-size="23" fill="{MUTE}">'
    f'瀏覽器只讀一份靜態 JSON：所有語意判讀與統計都在發佈前算完，站上沒有後端。</text>'
)

s.append(legend_chips([
    ("sky", "資料來源"),
    ("teal", "語意標記"),
    ("amber", "評分"),
    ("rose", "輸出"),
    ("violet", "前端"),
], 65, H - 58))
s.append(svg_tail())

SVG.write_text("".join(s), encoding="utf-8")
cairosvg.svg2png(url=str(SVG), write_to=str(PNG), output_width=W * 2)
print(f"{PNG.name} {Image.open(PNG).size}")
