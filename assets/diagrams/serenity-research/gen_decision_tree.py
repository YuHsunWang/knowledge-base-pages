# -*- coding: utf-8 -*-
"""Serenity 技術題材投資決策樹 — kb-diagrams 卡片風(4 關卡 + 分流名單)。"""
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, info_box

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("DECISION · 投資決策樹", "#4338ca",
                     "技術題材投資決策樹",
                     "四道關卡:技術為真 → 客戶買單 → 營收反映 → 股價未反映;任一關未過則分流"))

cw, ch = 372, 184
top_y = 270
xs = [80, 502, 924, 1346]
gates = [
    ("① 技術是真的嗎?", ["已量產 / 客戶測試中?", "專利 · 規格 · 測試"]),
    ("② 客戶買單嗎?",   ["design win / 量產訂單?", "大客戶認證 · 生態系"]),
    ("③ 營收會反映嗎?", ["今明年放量 · 高毛利?", "占比 · 毛利 · 產能"]),
    ("④ 股價已反映?",   ["尚未充分反映?", "對照景氣位置"]),
]
for x, (t, lines) in zip(xs, gates):
    s.append(card(x, top_y, cw, ch, "indigo", t, lines))

mid = top_y + ch / 2
for i in range(3):
    s.append(arrow(xs[i] + cw + 6, mid, xs[i + 1] - 8, mid))

# 通過四關 → 潛在機會(置於 gate4 下方)
sy = 600
s.append(card(xs[3], sy, cw, 184, "teal", "✅ 潛在機會",
              ["四關全過 · 尚未充分反映", "可深入研究 / 分批布局"]))
s.append(arrow(xs[3] + cw / 2, top_y + ch + 6, xs[3] + cw / 2, sy - 8))

# 任一關未過 → 分流名單
s.append(info_box(80, sy, 1180, 230, "任一關未過 → 分流名單",
                  ["只有實驗室階段 → ❌ 排除",
                   "只有 sample / 概念 → 👁 觀察名單",
                   "三年後 / 持續燒錢 → ⏳ 等待時程確認",
                   "已過熱 / 故事股 → ⏸ 等回調再評估"],
                  accent="violet"))
s.append(svg_tail())
open("serenity-02-decision-tree.svg", "w", encoding="utf-8").write("".join(s))
print("wrote serenity-02-decision-tree.svg")
