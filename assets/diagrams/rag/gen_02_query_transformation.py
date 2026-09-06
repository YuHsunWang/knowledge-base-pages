# -*- coding: utf-8 -*-
"""RAG Query Transformation 策略圖 generator."""
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, card, arrow, legend_chips, P, FAINT, MUTE, INK, BORDER, CARD
import diagram_kit as _dk
from html import escape

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT

W, H = 1800, 1020
s = [svg_head(W, H)]

# Title block
s.append(f'''
<text x="72" y="78" font-size="22" font-weight="bold" letter-spacing="3" fill="{P["violet"][1]}" font-family="{FONT}">TECHNIQUE · RAG</text>
<text x="70" y="132" font-size="46" font-weight="bold" fill="{INK}" font-family="{FONT}">Query Transformation 查詢轉換策略</text>
<text x="72" y="172" font-size="22" fill="{MUTE}" font-family="{FONT}">將使用者原始問題轉換後再搜尋，提升檢索召回率與準確度</text>
''')

# Center column: User Query → transforms
USER_X, USER_Y = 730, 220
USER_W, USER_H = 340, 100

# User Query box (larger, prominent)
s.append(f'<rect x="{USER_X}" y="{USER_Y}" width="{USER_W}" height="{USER_H}" rx="18" '
         f'fill="{P["violet"][0]}" filter="url(#soft)"/>')
s.append(f'<text x="{USER_X + USER_W//2}" y="{USER_Y + 42}" font-size="26" font-weight="bold" '
         f'text-anchor="middle" fill="white" font-family="{FONT}">使用者問題</text>')
s.append(f'<text x="{USER_X + USER_W//2}" y="{USER_Y + 76}" font-size="19" '
         f'text-anchor="middle" fill="#e8d9ff" font-family="{FONT}">User Query</text>')

# 4 strategy cards: 2x2 grid below
# Row 1: Multi-Query (left), HyDE (right)
# Row 2: Step-Back (left), Query Decomposition (right)
CW, CH = 760, 200
GAPX = 40
GAPY = 32
LEFT_X = 60
RIGHT_X = LEFT_X + CW + GAPX
ROW1_Y = 390
ROW2_Y = ROW1_Y + CH + GAPY

strategies = [
    # (x, y, phase, title, subtitle, lines)
    (LEFT_X,  ROW1_Y, "sky",    "Multi-Query 多角度重寫",
     "一問化多問，增加召回覆蓋率",
     ["原始問題改寫成 3-5 個不同表述", "各自搜尋後去重合併", "適合問法模糊或表達不精確時"]),
    (RIGHT_X, ROW1_Y, "teal",   "HyDE 假設文件嵌入",
     "以假答案代替問題去搜尋",
     ["讓 LLM 先生成一個「假設答案」", "用答案向量搜尋，非問題向量", "答案語意空間與文件更接近"]),
    (LEFT_X,  ROW2_Y, "amber",  "Step-Back Prompting",
     "先問背景，再問細節",
     ["把具體問題退一步成更廣泛的概念", "補充背景上下文後再答細節", "適合需要先驗知識的推理問題"]),
    (RIGHT_X, ROW2_Y, "rose",   "Query Decomposition 拆解",
     "複雜問題拆成子問題",
     ["把多跳問題分解為獨立子問題", "各自搜尋並回答", "合併子答案得到最終答案"]),
]

for (x, y, phase, title, subtitle, lines) in strategies:
    base, dark = P[phase]
    r = 18
    # Card background
    s.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="{r}" '
             f'fill="{CARD}" stroke="{BORDER}" filter="url(#soft)"/>')
    # Top accent bar
    s.append(f'<path d="M{x+r},{y} h{CW-2*r} a{r},{r} 0 0 1 {r},{r} v10 '
             f'h-{CW} v-10 a{r},{r} 0 0 1 {r},-{r} z" fill="{base}"/>')
    # Title
    s.append(f'<text x="{x+26}" y="{y+60}" font-size="26" font-weight="bold" '
             f'fill="{dark}" font-family="{FONT}">{escape(title)}</text>')
    # Subtitle
    s.append(f'<text x="{x+26}" y="{y+92}" font-size="20" font-style="italic" '
             f'fill="{MUTE}" font-family="{FONT}">{escape(subtitle)}</text>')
    # Body lines
    ly = y + 126
    for ln in lines:
        s.append(f'<text x="{x+26}" y="{ly}" font-size="19" fill="{MUTE}" '
                 f'font-family="{FONT}">{escape(ln)}</text>')
        ly += 28

# Arrows from User Query to each card
user_center_x = USER_X + USER_W // 2   # 900
user_bottom_y = USER_Y + USER_H         # 320

def arrow_to_card(cx_card, cy_card, phase):
    base = P[phase][0]
    return (f'<path d="M{user_center_x},{user_bottom_y} '
            f'L{user_center_x},{(user_bottom_y+cy_card)//2} '
            f'L{cx_card},{(user_bottom_y+cy_card)//2} '
            f'L{cx_card},{cy_card}" '
            f'fill="none" stroke="{base}" stroke-width="2.4" stroke-dasharray="8 5" '
            f'marker-end="url(#aFaint)"/>')

# Card centers (top edge)
cards_info = [
    (LEFT_X  + CW//2, ROW1_Y, "sky"),
    (RIGHT_X + CW//2, ROW1_Y, "teal"),
    (LEFT_X  + CW//2, ROW2_Y, "amber"),
    (RIGHT_X + CW//2, ROW2_Y, "rose"),
]
for cx, cy, phase in cards_info:
    s.append(arrow_to_card(cx, cy - 8, phase))

# Legend
s.append(legend_chips([
    ("sky",    "Multi-Query"),
    ("teal",   "HyDE"),
    ("amber",  "Step-Back"),
    ("rose",   "Decomposition"),
], 70, H - 55))

s.append(svg_tail())

out_svg = "/mnt/d/知識庫/docs/ai/assets/diagrams/rag/02-query-transformation.svg"
with open(out_svg, "w", encoding="utf-8") as f:
    f.write("".join(s))
print(f"wrote {out_svg}")
