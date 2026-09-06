# -*- coding: utf-8 -*-
"""Prompt Chaining 流程圖 — 水平線性 5 節點卡片風。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, MUTE, INK

W, H = 1800, 840
s = [svg_head(W, H)]
s.append(title_block("PROMPT ENGINEERING", "#0369a1",
                     "Prompt Chaining",
                     "將複雜任務拆解為多個有序步驟，每個 Prompt 職責單一，前一步輸出即為下一步輸入"))

cw, ch = 298, 330
y_card = 270
xs = [36, 390, 744, 1098, 1452]

cols = [
    ("amber",  "原始任務",  ["複雜、多步驟", "難以一次完成"]),
    ("sky",    "Prompt 1", ["拆解與萃取", "提取關鍵資訊"]),
    ("indigo", "Prompt 2", ["分析與推理", "深度處理"]),
    ("violet", "Prompt 3", ["整合生成", "組合成答案"]),
    ("teal",   "最終結果", ["精確、可審核", "品質穩定"]),
]

for x, c in zip(xs, cols):
    s.append(card(x, y_card, cw, ch, *c))

mid_y = y_card + ch // 2
for i in range(4):
    s.append(arrow(xs[i] + cw + 4, mid_y, xs[i + 1] - 7, mid_y))

# Caption
caption_y = y_card + ch + 68
s.append(f'<text x="{W // 2}" y="{caption_y}" font-size="22" '
         f'text-anchor="middle" fill="{MUTE}">每個 Prompt 職責單一，前一步輸出即為下一步輸入</text>')

s.append(legend_chips(
    [("amber", "輸入任務"), ("sky", "拆解"), ("indigo", "分析"), ("violet", "生成"), ("teal", "最終結果")],
    60, H - 55
))
s.append(svg_tail())

out_dir = os.path.dirname(__file__)
svg_path = os.path.join(out_dir, "01-prompt-chaining.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("".join(s))
print(f"wrote {svg_path}")
