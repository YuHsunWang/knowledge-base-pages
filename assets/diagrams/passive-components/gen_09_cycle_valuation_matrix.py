# -*- coding: utf-8 -*-
"""產生「景氣位置 × 估值判斷矩陣」圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import BORDER, CARD, INK, MUTE, P, svg_head, svg_tail
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1080


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


columns = ["景氣階段", "P/B", "預估 PE 表象", "正確解讀", "動作"]
widths = [210, 210, 300, 590, 300]
rows = [
    (["過熱", "高（紅區）", "看似低（峰值E）", "最危險：用峰值E算便宜是假象", "減碼/避開"], "#fff1f2", "#fecdd3", "#be123c"),
    (["衰退/去庫", "下殺", "飆高（E崩）", "PE 高是 E 崩，不代表貴", "觀察、分批佈局起點"], CARD, BORDER, INK),
    (["築底", "歷史低位", "極高或轉虧", "最佳風險報酬區", "分批買進"], "#f0fdf4", "#bbf7d0", "#15803d"),
    (["復甦初期", "中低->回升", "開始回落", "正常化 PE 合理", "加碼/續抱"], CARD, BORDER, INK),
]

s = [svg_head(W, H)]
s.append(text(70, 112, "景氣位置 × 估值判斷矩陣", 46, INK, "bold"))

x0, y0, header_h, row_h = 70, 220, 72, 126
total_w = sum(widths)
cx = x0
for label, width in zip(columns, widths):
    s.append(f'<rect x="{cx}" y="{y0}" width="{width}" height="{header_h}" '
             f'fill="#eef2ff" stroke="#d9ddff"/>')
    s.append(text(cx + width / 2, y0 + 46, label, 22, P["indigo"][1], "bold", "middle"))
    cx += width

for i, (values, fill, stroke, emphasis) in enumerate(rows):
    y = y0 + header_h + i * row_h
    cx = x0
    for j, (value, width) in enumerate(zip(values, widths)):
        s.append(f'<rect x="{cx}" y="{y}" width="{width}" height="{row_h}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{2 if i in (0, 2) else 1}"/>')
        color = emphasis if i in (0, 2) or j == 0 else INK
        weight = "bold" if i in (0, 2) or j in (0, 4) else "normal"
        size = 21 if j == 3 else 20
        s.append(text(cx + width / 2, y + 72, value, size, color, weight, "middle"))
        cx += width

note_y = y0 + header_h + len(rows) * row_h + 58
s.append(f'<rect x="190" y="{note_y}" width="1420" height="120" rx="20" '
         f'fill="#fff1f2" stroke="#fecdd3" stroke-width="3" filter="url(#soft)"/>')
s.append(f'<circle cx="245" cy="{note_y+60}" r="25" fill="{P["rose"][0]}"/>')
s.append(text(245, note_y + 69, "!", 31, CARD, "bold", "middle"))
s.append(text(285, note_y + 70, "PE 陷阱：景氣高點 EPS 最高、PE 看似最低，那通常是最危險的買點。",
              27, P["rose"][1], "bold"))
s.append(svg_tail())

svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "09-cycle-valuation-matrix.svg"
png_path = out_dir / "09-cycle-valuation-matrix.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
