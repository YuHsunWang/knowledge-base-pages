# -*- coding: utf-8 -*-
"""RAG 三階段架構圖 generator."""
import sys
sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P, FAINT, MUTE, INK
import diagram_kit as _dk
from html import escape

# Override font to use available CJK font on this system
_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT

W, H = 1800, 1020
s = [svg_head(W, H)]

s.append(title_block(
    "ARCHITECTURE · RAG", P["sky"][1],
    "RAG 三階段架構",
    "離線索引（Indexing）→ 線上檢索（Retrieval）→ 生成回答（Generation）"
))

# ---- Section labels ----
def section_label(x, y, text, color):
    return (f'<rect x="{x}" y="{y-28}" width="180" height="38" rx="10" fill="{color}" opacity="0.15"/>'
            f'<text x="{x+10}" y="{y}" font-size="22" font-weight="bold" fill="{color}" '
            f'font-family="{FONT}">{escape(text)}</text>')

OFF_Y = 290
ON_Y  = 650
CW_OFF = 330
CW_ON  = 280
CH     = 175
GAP_OFF = 28
GAP_ON  = 28

# Offline positions (4 cards)
off_xs = [80, 80+CW_OFF+GAP_OFF, 80+2*(CW_OFF+GAP_OFF), 80+3*(CW_OFF+GAP_OFF)]
# = 80, 438, 796, 1154

# Online positions (5 cards)
on_xs = [80, 80+CW_ON+GAP_ON, 80+2*(CW_ON+GAP_ON), 80+3*(CW_ON+GAP_ON), 80+4*(CW_ON+GAP_ON)]
# = 80, 388, 696, 1004, 1312

# ---- Offline section label ----
s.append(section_label(off_xs[0], OFF_Y - 38, "【離線索引】", P["sky"][1]))

# ---- Offline cards ----
offline_cards = [
    ("sky",   "原始文件",    ["PDF、Word、網頁、資料庫", "任意格式皆可"]),
    ("sky",   "文件分塊",    ["Recursive / Semantic", "chunk_size=512, overlap=50"]),
    ("sky",   "向量化",      ["Embedding Model 轉換", "語意接近→向量相近"]),
    ("teal",  "向量資料庫",  ["Chroma / Qdrant / FAISS", "ANN 相似度索引"]),
]
for x, (phase, title, lines) in zip(off_xs, offline_cards):
    s.append(card(x, OFF_Y, CW_OFF, CH, phase, title, lines))

# ---- Offline arrows ----
off_mid_y = OFF_Y + CH // 2
for i in range(3):
    s.append(arrow(off_xs[i]+CW_OFF+4, off_mid_y, off_xs[i+1]-6, off_mid_y))

# ---- Online section label ----
s.append(section_label(on_xs[0], ON_Y - 38, "【線上查詢】", P["rose"][1]))

# ---- Online cards ----
online_cards = [
    ("rose",   "使用者問題",   ["自然語言提問", "模糊或精確皆可"]),
    ("rose",   "問題向量化",   ["同一 Embedding Model", "對齊索引空間"]),
    ("rose",   "相似度搜尋",   ["ANN 查詢向量資料庫", "取回最相關文件"]),
    ("amber",  "Top-K 文件",   ["K=5~20 候選文件", "可加 Re-ranking"]),
    ("amber",  "Prompt + 生成", ["組合提示詞 + 文件", "LLM 生成最終答案"]),
]
for x, (phase, title, lines) in zip(on_xs, online_cards):
    s.append(card(x, ON_Y, CW_ON, CH, phase, title, lines))

# ---- Online arrows ----
on_mid_y = ON_Y + CH // 2
for i in range(4):
    s.append(arrow(on_xs[i]+CW_ON+4, on_mid_y, on_xs[i+1]-6, on_mid_y))

# ---- Connector: Vector DB → Similarity Search ----
# Vector DB bottom-center
vdb_cx = off_xs[3] + CW_OFF // 2   # 1154 + 165 = 1319
vdb_by = OFF_Y + CH + 6             # 290 + 175 + 6 = 471

# Sim Search top-center
ss_cx  = on_xs[2] + CW_ON // 2     # 696 + 140 = 836
ss_ty  = ON_Y - 8                   # 642

# Draw an L-shaped path: down then left
mid_y = (vdb_by + ss_ty) // 2  # ~557

connector_color = P["teal"][0]
connector_path = (
    f'<path d="M{vdb_cx},{vdb_by} '
    f'L{vdb_cx},{mid_y} '
    f'L{ss_cx},{mid_y} '
    f'L{ss_cx},{ss_ty}" '
    f'fill="none" stroke="{connector_color}" stroke-width="2.8" '
    f'stroke-dasharray="10 6" '
    f'marker-end="url(#aFaint)"/>'
)
s.append(connector_path)

# Label on connector
label_x = (vdb_cx + ss_cx) // 2 + 10
label_y = mid_y - 10
s.append(f'<text x="{label_x}" y="{label_y}" font-size="20" '
         f'font-weight="bold" fill="{P["teal"][1]}" '
         f'font-family="{FONT}">向量索引查詢</text>')

# ---- Legend ----
s.append(legend_chips([
    ("sky",   "索引處理"),
    ("teal",  "向量資料庫"),
    ("rose",  "問題處理"),
    ("amber", "生成回答"),
], 70, H - 55))

s.append(svg_tail())

out_svg = "/mnt/d/知識庫/docs/ai/assets/diagrams/rag/01-rag-pipeline.svg"
with open(out_svg, "w", encoding="utf-8") as f:
    f.write("".join(s))
print(f"wrote {out_svg}")
