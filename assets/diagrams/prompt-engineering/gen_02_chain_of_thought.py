# -*- coding: utf-8 -*-
"""Chain of Thought 推理模式對比圖 — 左：直接回答，右：CoT 逐步推理。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, info_box, MUTE, INK, FAINT, P, BORDER, CARD
from html import escape

W, H = 1800, 1180
s = [svg_head(W, H)]
s.append(title_block("PROMPT ENGINEERING", "#6d28d9",
                     "Chain of Thought（CoT）",
                     "引導模型顯示中間推理步驟，大幅提升複雜問題的準確率"))

# ── 左欄：直接回答 ──────────────────────────────────────────────────
col_w = 760
lx = 60
rx = 980
top_y = 230

# 左標題 badge
s.append(f'<rect x="{lx}" y="{top_y}" width="{col_w}" height="52" rx="14" '
         f'fill="{P["rose"][0]}" opacity="0.15" stroke="{P["rose"][0]}" stroke-opacity="0.4"/>')
s.append(f'<text x="{lx + col_w//2}" y="{top_y + 33}" font-size="24" font-weight="bold" '
         f'text-anchor="middle" fill="{P["rose"][1]}">❌ 直接回答（Direct Prompting）</text>')

# 左流程：問題 → 答案（兩個卡片）
s.append(card(lx + 130, top_y + 80,  500, 130, "rose", "問題",  ["輸入給模型"]))
s.append(arrow(lx + 130 + 250, top_y + 80 + 130 + 4,
               lx + 130 + 250, top_y + 80 + 130 + 70))
s.append(card(lx + 130, top_y + 80 + 130 + 80, 500, 130, "rose", "答案",  ["直接輸出，無推理過程"]))

# 左說明框
info_y = top_y + 80 + 130 + 80 + 130 + 40
s.append(info_box(lx + 20, info_y, col_w - 40, 190, "問題所在", [
    "・複雜問題容易出錯",
    "・無法追蹤推理步驟",
    "・幻覺難以被察覺",
], accent="rose"))

# ── 右欄：Chain of Thought ─────────────────────────────────────────
s.append(f'<rect x="{rx}" y="{top_y}" width="{col_w}" height="52" rx="14" '
         f'fill="{P["teal"][0]}" opacity="0.15" stroke="{P["teal"][0]}" stroke-opacity="0.4"/>')
s.append(f'<text x="{rx + col_w//2}" y="{top_y + 33}" font-size="24" font-weight="bold" '
         f'text-anchor="middle" fill="{P["teal"][1]}">✓ Chain of Thought Prompting</text>')

# 右流程：問題 → 步驟1 → 步驟2 → 步驟3 → 答案
step_h = 100
step_w = 500
sx = rx + (col_w - step_w) // 2
gap = 130
step_ys = [top_y + 80 + i * gap for i in range(5)]

s.append(card(sx, step_ys[0], step_w, step_h, "sky",    "問題",        ["輸入給模型"]))
s.append(card(sx, step_ys[1], step_w, step_h, "indigo", "步驟 1：理解問題", ["拆解已知條件"]))
s.append(card(sx, step_ys[2], step_w, step_h, "indigo", "步驟 2：推導過程", ["逐步計算 / 推理"]))
s.append(card(sx, step_ys[3], step_w, step_h, "indigo", "步驟 3：驗證",    ["自我檢查結果"]))
s.append(card(sx, step_ys[4], step_w, step_h, "teal",   "最終答案",       ["可追蹤、可審核"]))

mid_x = sx + step_w // 2
for i in range(4):
    s.append(arrow(mid_x, step_ys[i] + step_h + 4, mid_x, step_ys[i + 1] - 7))

# 右說明框
r_info_y = step_ys[4] + step_h + 30
s.append(info_box(rx + 20, r_info_y, col_w - 40, 190, "CoT 的優勢", [
    "・準確率顯著提升（尤其推理/數學）",
    "・推理過程可被審核與修正",
    "・Zero-shot：加「讓我們一步步思考」",
], accent="teal"))

# 分隔線
div_x = W // 2
s.append(f'<line x1="{div_x}" y1="{top_y}" x2="{div_x}" y2="{H - 60}" '
         f'stroke="{FAINT}" stroke-width="1.5" stroke-dasharray="8 6"/>')

s.append(svg_tail())

out_dir = os.path.dirname(__file__)
svg_path = os.path.join(out_dir, "02-chain-of-thought.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("".join(s))
print(f"wrote {svg_path}")
