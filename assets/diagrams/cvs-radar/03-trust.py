# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
import diagram_kit as _dk
_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P

from pathlib import Path

import cairosvg
from PIL import Image


W, H = 1780, 900
OUT = Path(__file__).resolve().parent
SVG = OUT / "03-trust.svg"
PNG = OUT / "03-trust.png"

s = [svg_head(W, H)]
s.append(title_block(
    "CVS-RADAR · TRUST",
    P["rose"][1],
    "可信度與假評論處理",
    "以弱訊號累積可疑分，只做內部降權，不公開點名",
))

cw, ch = 275, 165
y = 360
x0, x1, x2, x3, x4 = 80, 430, 780, 1110, 1430

s.append(card(x0, y, cw, ch, "sky", "每則留言", ["帳號、時間", "推噓與文字"]))
s.append(card(x1, y, cw, ch, "amber", "活動量門檻", ["先檢查樣本厚度", "避免精確假象"]))
s.append(card(x2, y, cw, ch, "teal", "帳號品牌偏好輪廓", ["看長期趨勢", "不看單句定罪"]))
s.append(card(x3, y, cw, ch, "teal", "弱訊號", ["貼文樣板化", "短時爆量"]))
s.append(card(x4, y, cw, ch, "rose", "可疑分", ["累積風險", "進入權重"]))

for a, b in [(x0, x1), (x1, x2), (x2, x3), (x3, x4)]:
    s.append(arrow(a + cw + 4, y + ch // 2, b - 8, y + ch // 2))

low_x, low_y = 430, 650
s.append(card(low_x, low_y, cw, 145, "sky", "不予評分", ["低於門檻", "不產生可疑分"]))
s.append(arrow(x1 + cw / 2, y + ch + 10, low_x + cw / 2, low_y - 10, dash="8 7"))
s.append(f'<text x="{x1+cw/2+24}" y="{low_y-30}" font-size="21" font-weight="bold" fill="{P["sky"][1]}">低於門檻</text>')
s.append(f'<text x="{x1+cw+22}" y="{y+75}" font-size="21" font-weight="bold" fill="{P["teal"][1]}">達標</text>')

out_x, out_y, out_w, out_h = 1110, 650, 595, 145
s.append(
    f'<rect x="{out_x}" y="{out_y}" width="{out_w}" height="{out_h}" rx="22" '
    f'fill="#fff1f2" stroke="{P["rose"][0]}" stroke-width="3" filter="url(#soft)"/>'
    f'<text x="{out_x+32}" y="{out_y+58}" font-size="29" font-weight="bold" fill="{P["rose"][1]}">內部降權</text>'
    f'<text x="{out_x+32}" y="{out_y+100}" font-size="24" font-weight="bold" fill="{P["rose"][1]}">不對外標記個別帳號</text>'
)
s.append(arrow(x4 + cw / 2, y + ch + 10, out_x + out_w / 2, out_y - 10, color=P["rose"][0], width=2.8))

s.append(legend_chips([
    ("sky", "輸入 / 門檻外"),
    ("amber", "評分前檢查"),
    ("teal", "偏好與弱訊號"),
    ("rose", "降權結果"),
], 70, H - 58))
s.append(svg_tail())

SVG.write_text("".join(s), encoding="utf-8")
cairosvg.svg2png(url=str(SVG), write_to=str(PNG), output_width=W * 2)
print(f"{PNG.name} {Image.open(PNG).size}")
