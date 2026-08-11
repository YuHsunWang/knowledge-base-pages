# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
import diagram_kit as _dk
_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P

from html import escape
from pathlib import Path

import cairosvg
from PIL import Image


W, H = 1660, 1030
OUT = Path(__file__).resolve().parent
SVG = OUT / "04-shopper-mapping.svg"
PNG = OUT / "04-shopper-mapping.png"
FONT = _dk.FONT


def shelf_signal(x, y, w, h, title, body, accent, fill="#ffffff"):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" '
        f'stroke="{accent}" stroke-width="2.6" filter="url(#soft)"/>'
        f'<text x="{x+28}" y="{y+55}" font-size="28" font-weight="bold" fill="{accent}" '
        f'font-family="{FONT}">{escape(title)}</text>'
        f'<text x="{x+28}" y="{y+98}" font-size="22" fill="#5b6472" '
        f'font-family="{FONT}">{escape(body)}</text>'
    )


s = [svg_head(W, H)]
s.append(title_block(
    "CVS-RADAR · SHOPPER UI",
    P["violet"][1],
    "後端欄位到貨架訊號",
    "把分析輸出翻成手機上能十秒看懂的判斷線索",
))

left_x, right_x = 90, 690
cw, ch = 360, 145
ys = [260, 440, 620, 800]

rows = [
    ("amber", "fair_score", ["公正分數", "越高越推薦"], "分數顏色", "綠 89 / 黃 55 / 紅 32"),
    ("teal", "正 / 中 / 負分布", ["正向比例", "替代無效徽章"], "正向 72%", "迷你長條"),
    ("sky", "樣本數", ["聲量透明", "避免過度解讀"], "N 則評價", "顯示資料厚度"),
    ("rose", "consensus", ["一致 / 兩極", "樣本太少時"], "資料不足", "fallback"),
]

for y, (phase, backend, lines, title, body) in zip(ys, rows):
    s.append(card(left_x, y, cw, ch, phase, backend, lines))
    s.append(arrow(left_x + cw + 8, y + ch // 2, right_x - 12, y + ch // 2))
    if backend == "fair_score":
        chip_w, chip_h, gap = 145, 92, 22
        colors = [
            ("#e7f6ec", "#15803d", "綠 89"),
            ("#fef5e1", "#b45309", "黃 55"),
            ("#fdeaea", "#be123c", "紅 32"),
        ]
        s.append(f'<text x="{right_x}" y="{y+35}" font-size="28" font-weight="bold" fill="{P["amber"][1]}">{title}</text>')
        for i, (fill, fg, label) in enumerate(colors):
            x = right_x + i * (chip_w + gap)
            s.append(f'<rect x="{x}" y="{y+55}" width="{chip_w}" height="{chip_h}" rx="18" fill="{fill}" stroke="{fg}" stroke-width="2.4"/>')
            s.append(f'<text x="{x+chip_w/2}" y="{y+113}" font-size="30" font-weight="bold" text-anchor="middle" fill="{fg}">{label}</text>')
    elif backend == "正 / 中 / 負分布":
        s.append(shelf_signal(right_x, y, 510, ch, title, body, P["teal"][1], "#f0fdfa"))
        bar_x, bar_y = right_x + 250, y + 88
        s.append(f'<rect x="{bar_x}" y="{bar_y}" width="210" height="18" rx="9" fill="#dbe4ee"/>')
        s.append(f'<rect x="{bar_x}" y="{bar_y}" width="151" height="18" rx="9" fill="{P["teal"][0]}"/>')
    elif backend == "樣本數":
        s.append(shelf_signal(right_x, y, 510, ch, title, body, P["sky"][1], "#f0f9ff"))
    else:
        s.append(shelf_signal(right_x, y, 510, ch, title, body, P["rose"][1], "#fff1f2"))

s.append(legend_chips([
    ("amber", "分數語意"),
    ("teal", "分布訊號"),
    ("sky", "樣本厚度"),
    ("rose", "不確定揭露"),
], 70, H - 58))
s.append(svg_tail())

SVG.write_text("".join(s), encoding="utf-8")
cairosvg.svg2png(url=str(SVG), write_to=str(PNG), output_width=W * 2)
print(f"{PNG.name} {Image.open(PNG).size}")
