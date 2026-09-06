# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
import diagram_kit as _dk
_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P

from pathlib import Path

import cairosvg
from PIL import Image


W, H = 1900, 610
OUT = Path(__file__).resolve().parent
SVG = OUT / "02-scoring.svg"
PNG = OUT / "02-scoring.png"

s = [svg_head(W, H)]
s.append(title_block(
    "CVS-RADAR · SCORING",
    P["amber"][1],
    "綜合評分怎麼來",
    "把散落的推文，變成兼顧公平、樣本與時效的分數",
))

cw, ch, y = 265, 175, 300
xs = [70, 370, 670, 970, 1270, 1570]
cards = [
    ("sky", "原始訊號", ["作者心得", "推文推噓"]),
    ("teal", "LLM 判讀", ["逐則情緒", "離題不計分"]),
    ("teal", "作者留言等權", ["心得不被洗掉", "群眾不被壓過"]),
    ("amber", "公平校正", ["每人只算一票", "舊討論逐漸淡出"]),
    ("amber", "貝氏收斂", ["樣本少就靠回中間", "少數極端不失真"]),
]
for x, data in zip(xs[:-1], cards):
    s.append(card(x, y, cw, ch, *data))
for a, b in zip(xs, xs[1:]):
    s.append(arrow(a + cw + 4, y + ch // 2, b - 8, y + ch // 2))

final_x, final_w = xs[-1], 260
s.append(
    f'<rect x="{final_x}" y="{y-12}" width="{final_w}" height="{ch+24}" rx="24" '
    f'fill="#fff7ed" stroke="{P["amber"][0]}" stroke-width="3" filter="url(#soft)"/>'
    f'<path d="M{final_x+24},{y-12} h{final_w-48} a24,24 0 0 1 24,24 v8 h-{final_w} v-8 '
    f'a24,24 0 0 1 24,-24 z" fill="{P["amber"][0]}"/>'
    f'<text x="{final_x+final_w/2}" y="{y+70}" font-size="32" font-weight="bold" '
    f'text-anchor="middle" fill="{P["amber"][1]}">綜合評分</text>'
    f'<text x="{final_x+final_w/2}" y="{y+112}" font-size="32" font-weight="bold" '
    f'text-anchor="middle" fill="{P["amber"][1]}">+ 信心度</text>'
)

s.append(legend_chips([
    ("sky", "原始訊號"),
    ("teal", "語意判讀"),
    ("amber", "公平校正"),
], 70, H - 58))
s.append(svg_tail())

SVG.write_text("".join(s), encoding="utf-8")
cairosvg.svg2png(url=str(SVG), write_to=str(PNG), output_width=W * 2)
print(f"{PNG.name} {Image.open(PNG).size}")
