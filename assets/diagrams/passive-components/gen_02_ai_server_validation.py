# -*- coding: utf-8 -*-
"""圖二:AI Server 需求驗證流程 — kb-diagrams 卡片風(同 ai-agent-harness 風格)。

正向漏斗:題材 → 品類確認 → 規格驗證 → 供應鏈階段 → 財務驗證 → 可投資結論。
結論為「是」→ 納入 thesis(終點);為「否」→ 虛線迴圈回觀察清單(不外推 EPS)。

    python gen_02_ai_server_validation.py
    # 渲染:用 Edge 無頭或 rsvg-convert 將 svg 轉 png
"""
from diagram_kit import (svg_head, svg_tail, title_block, card, arrow,
                         loop_arrow, legend_chips, P)

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("VERIFICATION · 六格穿透", P["violet"][1],
                     "AI Server 需求驗證流程",
                     "題材不是結論。每個「受益 AI」敘事都要走完品類→規格→供應鏈→財務,才決定能否納入 thesis"))

cw, ch = 372, 188
top_y, bot_y = 262, 648
txs = [80, 502, 924, 1346]      # 上排 →
bxs = [1346, 713, 80]           # 下排 ←

top = [
    ("indigo", "① 題材 / 傳聞",  ["AI server 受益敘事", "需穿透驗證,勿直接外推"]),
    ("indigo", "② 品類確認",     ["MLCC 去耦 · 功率電感 VRM", "鉭容/薄膜容 · 電流感測電阻"]),
    ("sky",    "③ 規格驗證",     ["低 ESL · 高 Isat", "低 DCR · 低 TCR"]),
    ("amber",  "④ 供應鏈階段",   ["未確認 → 送樣 → 進 AVL", "→ 小量量產 → 大量量產"]),
]
bot = [
    ("amber",  "⑤ 財務驗證",     ["營收占比 · 毛利率", "訂單:急單 / 短約 / 長約"]),
    ("violet", "⑥ 可投資結論?",  ["六格是否完整?", "是 → 納入 · 否 → 待確認"]),
    ("teal",   "✅ 納入 thesis",  ["六格完整 = 有依據", "可量化營收 / 毛利貢獻"]),
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
s.append(loop_arrow(bxs[1] + cw / 2, bot_y - 6, txs[0] + cw / 2, top_y + ch + 8,
                    label="未達標 → 標記待確認 · 不外推 EPS · 回觀察清單"))

s.append(legend_chips([("indigo", "題材 / 品類"), ("sky", "規格"),
                       ("amber", "供應鏈 / 財務"), ("violet", "判斷"),
                       ("teal", "可納入結論")], 70, H - 70))
s.append(svg_tail())
open("02-ai-server-validation.svg", "w", encoding="utf-8").write("".join(s))
print("wrote 02-ai-server-validation.svg")
