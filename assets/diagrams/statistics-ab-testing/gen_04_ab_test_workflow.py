# -*- coding: utf-8 -*-
"""產生「A/B 測試流程與把關點」圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import BORDER, FAINT, INK, MUTE, P, arrow, card, svg_head, svg_tail, title_block
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1500


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


s = [svg_head(W, H)]
s.append(title_block(
    "實驗流程", P["teal"][1],
    "A/B 測試流程與把關點",
    "把決策規則先凍結，再用 SRM 與護欄指標守住實驗品質",
))

card_x, card_w, card_h = 90, 1010, 132
steps = [
    (225, "sky", "1. 定義假設與指標", ["主要指標只能一個；護欄指標 3–5 個"]),
    (405, "indigo", "2. 事前登記", ["凍結假設、MDE、樣本數、決策規則"]),
    (585, "violet", "3. 隨機分派", ["分派單位＝分析單位；用穩定 hash"]),
    (1005, "amber", "4. 跑滿不偷看", ["跑到預定樣本數才分析"]),
    (1245, "teal", "5. 分析與決策", ["看信賴區間下界，不只看 p 值"]),
]

for y, phase, title, lines in steps:
    s.append(card(card_x, y, card_w, card_h, phase, title, lines))

# Main vertical flow through the first three steps.
s.append(arrow(595, 365, 595, 395))
s.append(arrow(595, 545, 595, 575))

# SRM diamond gate between random assignment and full run.
gate_cx, gate_cy = 595, 840
s.append(arrow(595, 725, 595, 780))
s.append(f'<path d="M{gate_cx},{gate_cy-62} L{gate_cx+180},{gate_cy} '
         f'L{gate_cx},{gate_cy+62} L{gate_cx-180},{gate_cy} Z" '
         f'fill="#f5f3ff" stroke="{P["violet"][0]}" stroke-width="4" filter="url(#soft)"/>')
s.append(text(gate_cx, gate_cy - 4, "SRM 檢查", 26, P["violet"][1], "bold", "middle"))
s.append(text(gate_cx, gate_cy + 32, "（開跑 24 小時內）", 21, MUTE, "normal", "middle"))

# Pass branch reaches step four.
s.append(f'<path d="M595,902 L595,977" fill="none" stroke="{P["teal"][0]}" '
         f'stroke-width="4" marker-end="url(#aFaint)"/>')
s.append(text(625, 950, "通過", 21, P["teal"][1], "bold"))

# Failure branch ends in a red terminal box.
s.append(f'<path d="M775,840 L1185,840" fill="none" stroke="{P["rose"][0]}" '
         f'stroke-width="4" marker-end="url(#aFaint)"/>')
s.append(text(955, 818, "不通過", 21, P["rose"][1], "bold", "middle"))
s.append(f'<rect x="1215" y="772" width="500" height="136" rx="18" fill="#fdeaea" '
         f'stroke="#f4c7c7" stroke-width="3" filter="url(#soft)"/>')
s.append(text(1465, 828, "停止實驗，", 25, P["rose"][1], "bold", "middle"))
s.append(text(1465, 866, "找分派/記錄的 bug", 25, P["rose"][1], "bold", "middle"))

# Step four warning note; it is advisory, not another decision branch.
s.append(f'<rect x="1170" y="1010" width="545" height="122" rx="18" fill="#fef5e1" '
         f'stroke="#f4dca6" stroke-width="3" filter="url(#soft)"/>')
s.append(text(1198, 1054, "中途只看護欄指標，", 22, P["amber"][1], "bold"))
s.append(text(1198, 1092, "用來止損不用來宣告勝利", 22, P["amber"][1], "bold"))
s.append(f'<line x1="1100" y1="1071" x2="1158" y2="1071" stroke="{P["amber"][0]}" '
         f'stroke-width="4" stroke-dasharray="9 7"/>')

s.append(arrow(595, 1145, 595, 1235))
s.append(svg_tail())

svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "04-ab-test-workflow.svg"
png_path = out_dir / "04-ab-test-workflow.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
