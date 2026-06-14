# -*- coding: utf-8 -*-
"""
mcmc_iteration_flow.py — Bayesian MCMC iteration flow (serpentine + feedback loop).

Replaces the plain mermaid flowchart on the mcmc-portfolio project page.
Colour encodes the phase (see legend). Re-edit and re-render:

    python3 mcmc_iteration_flow.py
    rsvg-convert mcmc-iteration-flow.svg -o mcmc-iteration-flow.png
"""
import diagram_kit
# Primary family must be one fontconfig can resolve on the render host so CJK
# glyphs are not dropped (cairosvg lacks per-glyph fallback). Noto/JhengHei are
# both fine; keep the Noto fallbacks for hosts that have them.
diagram_kit.FONT = "Microsoft JhengHei, Noto Sans CJK TC, Noto Sans CJK SC, sans-serif"
from diagram_kit import (svg_head, svg_tail, title_block, card, arrow,
                         loop_arrow, legend_chips, P, FAINT)

W, H = 1800, 1120
s = [svg_head(W, H)]
s.append(title_block("MCMC · 迭代閉環", P["indigo"][1],
                     "貝氏 MCMC 迭代流程",
                     "Metropolis-Hastings 取樣：初始化 → 提議 → 接受/拒絕 → 更新 → 預測 → 儲存,每次迭代回到提議步驟"))

cw, ch = 372, 188
top_y, bot_y = 280, 600
txs = [80, 502, 924, 1346]      # top row, flows →
bxs = [1346, 713, 80]           # bottom row, flows ← (right to left)

top = [
    ("indigo", "初始化參數",     ["使用者 a_u · s_u · C_switch", "族群超參數 θ · Σ · σ"]),
    ("sky",    "提出使用者參數", ["log-normal random walk", "s_u = 1 + z_u (z_u > 0)"]),
    ("sky",    "計算接受比值",   ["似然比 · 先驗比", "proposal 修正項"]),
    ("amber",  "MH 接受 / 拒絕", ["α = min(1, r)", "接受則替換,否則保留"]),
]
bot = [
    ("amber",  "更新族群超參數", ["θ_a · Σ_a", "θ_switch · σ_switch"]),
    ("violet", "預測與評估",     ["預測下一個類別", "計算訓練準確率"]),
    ("violet", "儲存後驗樣本",   ["參數樣本 · 接受率", "收斂 trace"]),
]
for x, c in zip(txs, top):
    s.append(card(x, top_y, cw, ch, *c))
for x, c in zip(bxs, bot):
    s.append(card(x, bot_y, cw, ch, *c))

midt, midb = top_y + ch / 2, bot_y + ch / 2
for i in range(3):                                              # top horizontals →
    s.append(arrow(txs[i] + cw + 6, midt, txs[i + 1] - 8, midt))
s.append(arrow(txs[3] + cw / 2, top_y + ch + 6, txs[3] + cw / 2, bot_y - 8))  # right ↓
s.append(arrow(bxs[0] - 6, midb, bxs[1] + cw + 8, midb))       # bottom ← 1
s.append(arrow(bxs[1] - 6, midb, bxs[2] + cw + 8, midb))       # bottom ← 2

# feedback loop: 儲存 → 提出參數 (every iteration)
s.append(loop_arrow(bxs[2] + cw / 2, bot_y - 6, txs[1] + cw / 2, top_y + ch + 8,
                    label="每次迭代 · MCMC loop"))

# terminal: after n_iter, exit to convergence diagnostics
tx, ty, tw, th = 600, 902, 600, 158
s.append(card(tx, ty, tw, th, "teal", "收斂診斷與後驗",
              ["n_iter 次迭代後輸出 · trace · 接受率 · 參數分布"]))
s.append(arrow(bxs[2] + cw / 2, bot_y + ch + 6, tx + 4, ty + th / 2,
               color=P["teal"][1], width=2.6))
s.append(f'<text x="{bxs[2]+cw/2+18}" y="{bot_y+ch+72}" font-size="20" '
         f'font-weight="bold" fill="{P["teal"][1]}">n_iter 次後</text>')

s.append(legend_chips([("indigo", "初始化"), ("sky", "取樣提議"),
                       ("amber", "MH 決策 / 更新"), ("violet", "預測 / 儲存"),
                       ("teal", "輸出")], 70, H - 48))
s.append(svg_tail())
open("mcmc-iteration-flow.svg", "w", encoding="utf-8").write("".join(s))
print("wrote mcmc-iteration-flow.svg")
