# -*- coding: utf-8 -*-
"""景氣循環四階段與操作 — kb-diagrams 卡片風(4 卡 + 循環迴圈)。"""
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
from html import escape

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("BUSINESS CYCLE · 景氣循環", P["sky"][1],
                     "景氣循環四階段與操作",
                     "復甦 → 成長 → 榮景 → 衰退 → 周而復始;每個階段對應不同的進出策略"))

cw, ch = 372, 200
y = 330
xs = [80, 502, 924, 1346]
cards = [
    ("teal",  "復甦期 · 積極布局", ["失業率高點反轉", "耐久財需求回升"]),
    ("sky",   "成長期 · 穩健持續", ["企業獲利穩定", "就業持續增長"]),
    ("amber", "榮景期 · 彈性持股", ["透支性消費", "固定投資衝頂"]),
    ("rose",  "衰退期 · 轉守為攻", ["數據全面轉弱", "持有債券 / 美元"]),
]
for x, c in zip(xs, cards):
    s.append(card(x, y, cw, ch, *c))

mid = y + ch / 2
for i in range(3):
    s.append(arrow(xs[i] + cw + 6, mid, xs[i + 1] - 8, mid))

# 循環迴圈:衰退(右) → 下方 → 復甦(左)
yb = y + ch
yd = yb + 120
xd = xs[3] + cw / 2
xa = xs[0] + cw / 2
vio = P["violet"][0]
s.append(f'<path d="M{xd},{yb} L{xd},{yd} L{xa},{yd} L{xa},{yb+10}" fill="none" '
         f'stroke="{vio}" stroke-width="2.6" stroke-dasharray="9 7" marker-end="url(#aViolet)"/>')
s.append(f'<text x="{(xa+xd)/2}" y="{yd+34}" font-size="22" font-weight="bold" '
         f'text-anchor="middle" fill="{P["violet"][1]}">{escape("↻ 衰退期過後回到復甦期 · 景氣周而復始")}</text>')

s.append(legend_chips([("teal", "復甦"), ("sky", "成長"), ("amber", "榮景"), ("rose", "衰退")], 70, H - 60))
s.append(svg_tail())
open("industry-sop-01-business-cycle.svg", "w", encoding="utf-8").write("".join(s))
print("wrote industry-sop-01-business-cycle.svg")
