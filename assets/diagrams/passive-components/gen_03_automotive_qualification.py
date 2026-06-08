# -*- coding: utf-8 -*-
"""圖三:車規認證與商業化路徑 — kb-diagrams 卡片風。

序列:元件開發 → AEC-Q200 → Tier-1/OEM AVL → PPAP → 量產出貨 → 長期可靠度 → 可量化貢獻。
虛線迴圈:認證未過 / PCN → 改善製程 · 重新認證(回 AEC-Q200)。
"""
from diagram_kit import (svg_head, svg_tail, title_block, card, arrow,
                         loop_arrow, legend_chips, P)

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("QUALIFICATION · 認證≠量產", P["amber"][1],
                     "車規認證與商業化路徑",
                     "AEC-Q200 是門票,不是終點;要走完 AVL → PPAP → 量產 → 長期可靠度才算商業化"))

cw, ch = 372, 188
top_y, bot_y = 262, 648
txs = [80, 502, 924, 1346]
bxs = [1346, 713, 80]

top = [
    ("indigo", "① 元件開發完成",   ["MLCC / 電阻 / 電感", "送認證前準備"]),
    ("indigo", "② AEC-Q200",       ["元件層可靠度認證", "⚠ 是門票,非終點"]),
    ("sky",    "③ Tier-1 / OEM AVL", ["客戶合格廠商名單", "歐系 / 中國 NEV / 模組廠"]),
    ("sky",    "④ PPAP 量產前核准", ["生產件核准程序", "品質系統查核"]),
]
bot = [
    ("amber",  "⑤ 量產出貨",       ["營收驗證", "車用占比 YoY"]),
    ("amber",  "⑥ 長期可靠度",     ["形成替換壁壘", "PCN 風險控管"]),
    ("teal",   "✅ 可量化貢獻",     ["營收 / 毛利可拆分", "車用認證護城河"]),
]
for x, c in zip(txs, top):
    s.append(card(x, top_y, cw, ch, *c))
for x, c in zip(bxs, bot):
    s.append(card(x, bot_y, cw, ch, *c))

midt, midb = top_y + ch / 2, bot_y + ch / 2
for i in range(3):
    s.append(arrow(txs[i] + cw + 6, midt, txs[i + 1] - 8, midt))
s.append(arrow(txs[3] + cw / 2, top_y + ch + 6, txs[3] + cw / 2, bot_y - 8))
s.append(arrow(bxs[0] - 6, midb, bxs[1] + cw + 8, midb))
s.append(arrow(bxs[1] - 6, midb, bxs[2] + cw + 8, midb))
s.append(loop_arrow(bxs[1] + cw / 2, bot_y - 6, txs[1] + cw / 2, top_y + ch + 8,
                    label="認證未過 / PCN → 改善材料·製程 · 重新認證"))

s.append(legend_chips([("indigo", "開發 / 認證"), ("sky", "客戶導入"),
                       ("amber", "量產 / 可靠度"), ("teal", "可量化貢獻")], 70, H - 70))
s.append(svg_tail())
open("03-automotive-qualification.svg", "w", encoding="utf-8").write("".join(s))
print("wrote 03-automotive-qualification.svg")
