# -*- coding: utf-8 -*-
"""圖一:被動元件產業鏈全貌 — kb-diagrams 卡片風(五層價值鏈,左→右)。"""
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("VALUE CHAIN · 產業鏈", "#0f766e",
                     "被動元件產業鏈全貌",
                     "上游材料 → 元件製造 → 終端應用 → 台廠曝險 → 追蹤指標"))

cw, ch = 330, 340
y = 320
xs = [43, 389, 735, 1081, 1427]

cols = [
    ("teal",   "上游材料", ["BaTiO₃ 粉體", "Ni / RuO₂ 漿料", "鐵氧體 / 磁粉芯", "NiCr / Cu 合金"]),
    ("sky",    "元件製造", ["MLCC", "晶片電阻", "功率電感", "鉭容 / 薄膜電容"]),
    ("amber",  "終端應用", ["AI Server / HPC", "電動車 EV", "工控 / 能源", "消費電子"]),
    ("violet", "台灣公司", ["國巨 2327", "華新科 2492", "禾伸堂 3026", "大毅 2478", "奇力新"]),
    ("indigo", "追蹤指標", ["月營收 MoM/YoY", "MLCC 現貨報價", "Lead time 週數", "稼動率 / 毛利率", "DSI · AI車用占比"]),
]
for x, c in zip(xs, cols):
    s.append(card(x, y, cw, ch, *c))

mid = y + ch / 2
for i in range(4):
    s.append(arrow(xs[i] + cw + 4, mid, xs[i + 1] - 6, mid))

s.append(legend_chips([("teal", "材料"), ("sky", "元件"), ("amber", "應用"),
                       ("violet", "公司"), ("indigo", "指標")], 70, H - 70))
s.append(svg_tail())
open("01-industry-tree.svg", "w", encoding="utf-8").write("".join(s))
print("wrote 01-industry-tree.svg")
