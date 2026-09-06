# -*- coding: utf-8 -*-
"""Agentic Loop 執行週期圖 — 四節點循環 + 退出路徑（下方）。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from diagram_kit import (svg_head, svg_tail, title_block, card, arrow,
                         info_box, legend_chips, MUTE, INK, FAINT, P, BORDER)
from html import escape

W, H = 1800, 1260
s = [svg_head(W, H)]
s.append(title_block("PROMPT ENGINEERING", "#0f766e",
                     "Loop Engineering（Agentic Loop）",
                     "模型在工具呼叫或自我反思中循環執行，直到達成目標或觸發終止條件"))

# ── 四個主要節點（矩形排列）──────────────────────────────────────────
cw, ch = 310, 210
cx_l, cx_r = 280, 1190
cy_t, cy_b = 260, 560

nodes = {
    "plan":    (cx_l, cy_t),
    "act":     (cx_r, cy_t),
    "observe": (cx_r, cy_b),
    "eval":    (cx_l, cy_b),
}

s.append(card(*nodes["plan"],    cw, ch, "sky",    "① 規劃",  ["選定行動策略", "決定呼叫哪個工具"]))
s.append(card(*nodes["act"],     cw, ch, "indigo", "② 執行",  ["呼叫工具 / API", "生成回應或操作"]))
s.append(card(*nodes["observe"], cw, ch, "amber",  "③ 觀察",  ["讀取工具回傳結果", "解析環境狀態"]))
s.append(card(*nodes["eval"],    cw, ch, "violet", "④ 評估",  ["目標達成？", "錯誤 → 調整策略"]))

# ── 順時針箭頭 ──────────────────────────────────────────────────────
mid_plan_y   = nodes["plan"][1]    + ch // 2
mid_act_y    = nodes["act"][1]     + ch // 2
mid_obs_y    = nodes["observe"][1] + ch // 2
mid_eval_y   = nodes["eval"][1]    + ch // 2

# 規劃 → 執行（上方，水平）
s.append(arrow(nodes["plan"][0] + cw + 5, mid_plan_y,
               nodes["act"][0] - 7,        mid_act_y))

# 執行 → 觀察（右側，垂直）
s.append(arrow(nodes["act"][0] + cw // 2,     nodes["act"][1] + ch + 5,
               nodes["observe"][0] + cw // 2, nodes["observe"][1] - 7))

# 觀察 → 評估（下方，水平，右→左）
s.append(arrow(nodes["observe"][0] - 7,    mid_obs_y,
               nodes["eval"][0] + cw + 5,  mid_eval_y))

# ── 回饋弧：評估 → 規劃（左側 S 曲線）────────────────────────────
loop_x = 130
s.append(
    f'<path d="M{nodes["eval"][0]},{mid_eval_y} '
    f'C{loop_x},{mid_eval_y} '
    f'{loop_x},{mid_plan_y} '
    f'{nodes["plan"][0]},{mid_plan_y}" '
    f'fill="none" stroke="{P["violet"][0]}" stroke-width="2.8" '
    f'stroke-dasharray="10 7" marker-end="url(#aViolet)"/>'
)
label_x = loop_x - 68
label_y = (mid_eval_y + mid_plan_y) // 2
s.append(f'<text x="{label_x}" y="{label_y - 14}" font-size="21" font-weight="bold" '
         f'fill="{P["violet"][1]}" text-anchor="middle">未達成</text>')
s.append(f'<text x="{label_x}" y="{label_y + 14}" font-size="21" '
         f'fill="{P["violet"][1]}" text-anchor="middle">重新規劃</text>')

# ── 退出路徑：評估 → 完成（向下，垂直）────────────────────────────
eval_cx  = nodes["eval"][0] + cw // 2
eval_bot = nodes["eval"][1] + ch

done_w, done_h = 330, 110
done_x = eval_cx - done_w // 2
done_y = eval_bot + 70

s.append(arrow(eval_cx, eval_bot + 5, eval_cx, done_y - 7,
               color=P["teal"][0], width=2.8))

s.append(f'<rect x="{done_x}" y="{done_y}" width="{done_w}" height="{done_h}" rx="18" '
         f'fill="{P["teal"][0]}" opacity="0.18" stroke="{P["teal"][0]}" stroke-width="2" filter="url(#soft)"/>')
s.append(f'<text x="{eval_cx}" y="{done_y + 46}" font-size="27" font-weight="bold" '
         f'text-anchor="middle" fill="{P["teal"][1]}">目標達成</text>')
s.append(f'<text x="{eval_cx}" y="{done_y + 82}" font-size="21" '
         f'text-anchor="middle" fill="{MUTE}">輸出最終結果</text>')

# 「達成」標籤
s.append(f'<text x="{eval_cx - done_w//2 - 55}" y="{eval_bot + 43}" font-size="20" '
         f'font-weight="bold" fill="{P["teal"][1]}" text-anchor="middle">達成</text>')

# ── 中心標籤 ─────────────────────────────────────────────────────
cx_center = (cx_l + cw + cx_r) // 2
cy_center = (cy_t + ch + cy_b) // 2
s.append(f'<text x="{cx_center}" y="{cy_center - 14}" font-size="22" '
         f'text-anchor="middle" fill="{FAINT}">每輪循環</text>')
s.append(f'<text x="{cx_center}" y="{cy_center + 18}" font-size="22" '
         f'text-anchor="middle" fill="{FAINT}">更新狀態與策略</text>')

# ── 說明框 ───────────────────────────────────────────────────────
info_y = done_y + done_h + 50
s.append(info_box(60, info_y, 820, 175, "適用場景", [
    "・程式除錯（反覆執行 → 讀取錯誤 → 修正）",
    "・資料搜尋與彙整（多輪工具呼叫）",
    "・自動化流程（需動態決策的工作）",
], accent="sky"))
s.append(info_box(920, info_y, 820, 175, "終止條件設計（避免無限迴圈）", [
    "・最大迭代次數（max_iterations）",
    "・明確完成訊號（is_done flag）",
    "・成本 / Token 上限",
], accent="violet"))

# ── 圖例 ─────────────────────────────────────────────────────────
s.append(legend_chips([("sky", "規劃"), ("indigo", "執行"), ("amber", "觀察"),
                       ("violet", "評估"), ("teal", "完成")], 70, H - 52))
s.append(svg_tail())

out_dir = os.path.dirname(__file__)
svg_path = os.path.join(out_dir, "03-agentic-loop.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("".join(s))
print(f"wrote {svg_path}")
