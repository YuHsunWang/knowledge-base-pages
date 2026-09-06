# -*- coding: utf-8 -*-
"""產生「偷看導致假陽性膨脹」圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import FAINT, INK, MUTE, P, svg_head, svg_tail, title_block
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1080


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


s = [svg_head(W, H)]
s.append(title_block(
    "實驗紀律", P["rose"][1],
    "偷看導致假陽性膨脹",
    "反覆用同一門檻判定勝負，誤判風險會持續累積",
))

left, right, top, bottom = 235, 1660, 270, 770
max_value = 20.0
bars = [("1 次", 4.6, P["teal"][0]), ("2 次", 8.6, P["amber"][0]),
        ("5 次", 14.5, P["amber"][0]), ("10 次", 19.6, P["rose"][0])]
centers = [430, 780, 1130, 1480]
bar_width = 190

for fraction in (0.25, 0.5, 0.75):
    y = bottom - (bottom - top) * fraction
    s.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
             f'stroke="#e6e8ef" stroke-width="2"/>')
s.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="{FAINT}" stroke-width="3"/>')
s.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{FAINT}" stroke-width="3"/>')

ref_y = bottom - 5.0 / max_value * (bottom - top)
s.append(f'<line x1="{left}" y1="{ref_y:.1f}" x2="{right}" y2="{ref_y:.1f}" '
         f'stroke="{P["indigo"][0]}" stroke-width="4" stroke-dasharray="12 8"/>')
s.append(f'<rect x="245" y="{ref_y-115:.1f}" width="270" height="42" rx="10" '
         f'fill="#eef2ff" stroke="#d9ddff"/>')
s.append(text(380, ref_y - 85, "宣稱的 α = 5%", 22, P["indigo"][1], "bold", "middle"))

for (label, value, color), center in zip(bars, centers):
    y = bottom - value / max_value * (bottom - top)
    height = bottom - y
    s.append(f'<rect x="{center-bar_width/2:.1f}" y="{y:.1f}" width="{bar_width}" '
             f'height="{height:.1f}" rx="16" fill="{color}" opacity="0.88"/>')
    s.append(text(center, y - 20, f"{value}%", 28, color, "bold", "middle"))
    s.append(text(center, bottom + 48, label, 23, INK, "bold", "middle"))

s.append(text(950, 865, "實驗期間檢查次數", 25, INK, "bold", "middle"))
s.append(f'<text x="95" y="525" font-size="25" fill="{INK}" font-weight="bold" '
         f'text-anchor="middle" transform="rotate(-90 95 525)">實際假陽性率</text>')

s.append(f'<rect x="220" y="900" width="1360" height="90" rx="18" fill="#fff7f8" '
         f'stroke="#f4c7c7" filter="url(#soft)"/>')
s.append(text(900, 956, "每天看一次、跑兩週，假陽性率約是宣稱值的四倍。",
              27, P["rose"][1], "bold", "middle"))
s.append(text(1580, 1032, "資料來源：A/A 模擬，3,000 次重複", 18, MUTE, "normal", "end"))

s.append(svg_tail())
svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "03-peeking-false-positive.svg"
png_path = out_dir / "03-peeking-false-positive.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
