# -*- coding: utf-8 -*-
"""Serenity 供應鏈定位:從趨勢到終端 — kb-diagrams 卡片風(線性 5 節點)。"""
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("VALUE CHAIN · 供應鏈定位", "#6d28d9",
                     "供應鏈定位:從趨勢到終端",
                     "選定產業趨勢後,沿上游→中游→下游→終端拆解,找出最難被取代的環節"))

cw, ch = 330, 300
y = 340
xs = [43, 389, 735, 1081, 1427]
cols = [
    ("violet", "選定產業趨勢", ["從結構性趨勢切入", "AI · EV · 能源…"]),
    ("teal",   "上游",         ["原料 · 材料", "關鍵零組件"]),
    ("sky",    "中游",         ["設計 · 製造", "代工 · 設備"]),
    ("amber",  "下游",         ["封裝 · 組裝", "模組 · 整合"]),
    ("rose",   "終端客戶",     ["雲端大廠 · 車廠", "工業"]),
]
for x, c in zip(xs, cols):
    s.append(card(x, y, cw, ch, *c))

mid = y + ch / 2
for i in range(4):
    s.append(arrow(xs[i] + cw + 4, mid, xs[i + 1] - 6, mid))

s.append(legend_chips([("violet", "趨勢"), ("teal", "上游"), ("sky", "中游"),
                       ("amber", "下游"), ("rose", "終端")], 70, H - 70))
s.append(svg_tail())
open("serenity-01-supply-chain.svg", "w", encoding="utf-8").write("".join(s))
print("wrote serenity-01-supply-chain.svg")
