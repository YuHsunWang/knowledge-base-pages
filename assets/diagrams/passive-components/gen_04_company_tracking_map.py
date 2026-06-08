# -*- coding: utf-8 -*-
"""圖四:台灣公司研究追蹤地圖 — kb-diagrams 卡片風(5 公司卡 + 共同檢查順序)。"""
from diagram_kit import svg_head, svg_tail, title_block, card, info_box

W, H = 1800, 1050
s = [svg_head(W, H)]
s.append(title_block("COMPANY MAP · 公司地圖", "#6d28d9",
                     "台灣公司研究追蹤地圖",
                     "五家研究問題不同,但檢查順序一致:品類→規格→客戶階段→營收占比→毛利率→紅旗"))

cw, ch = 540, 232
top_y, bot_y = 290, 556
txs = [60, 630, 1200]
bxs = [345, 915]

top = [
    ("violet", "國巨 2327 · 平台型", ["曝險:MLCC+電阻+鉭容+電感+感測",
                                      "問題:KEMET整合 · 事業部毛利 · AI拆分",
                                      "⚠ 槓桿 · 標準品ASP · AI敘事不透明"]),
    ("sky", "華新科 2492 · 景氣純度計", ["曝險:MLCC+電阻,景氣純度高",
                                        "問題:MLCC ASP止跌? · 車規/AI AVL",
                                        "⚠ 景氣被過度外推 · 業外損益"]),
    ("amber", "禾伸堂 3026 · 製造+代理", ["曝險:自有 MLCC + 代理日系",
                                         "問題:製造 vs 代理毛利拆分 · 通路領先",
                                         "⚠ 代理線變動 · 通路庫存堆積"]),
]
bot = [
    ("teal", "大毅 2478 · 電阻專業", ["曝險:厚膜/薄膜 · 電流感測 · 抗硫化",
                                     "問題:高階占比? · 車用/AI power 認證",
                                     "⚠ 標準品商品化 · 敘事停留送樣"]),
    ("indigo", "奇力新 · 電感磁性", ["曝險:功率電感 · RF · 磁珠 · CMC",
                                    "問題:AI VRM量產? · 車用認證 · 整合效益",
                                    "⚠ 透明度下降 · 順絡競爭"]),
]
for x, c in zip(txs, top):
    s.append(card(x, top_y, cw, ch, *c))
for x, c in zip(bxs, bot):
    s.append(card(x, bot_y, cw, ch, *c))

s.append(info_box(300, 852, 1200, 118, "共同檢查順序(五家一致)",
                  ["品類 → 規格 → 客戶階段 → 營收占比 → 毛利率 → 紅旗",
                   "用同一把尺比較五家;差異在各自的研究問題與紅旗"],
                  accent="violet"))
s.append(svg_tail())
open("04-company-tracking-map.svg", "w", encoding="utf-8").write("".join(s))
print("wrote 04-company-tracking-map.svg")
