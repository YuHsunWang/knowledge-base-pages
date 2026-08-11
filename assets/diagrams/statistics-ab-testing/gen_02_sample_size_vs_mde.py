# -*- coding: utf-8 -*-
"""產生「樣本數與 MDE 的平方反比」圖。"""
import math
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import FAINT, INK, MUTE, P, svg_head, svg_tail, title_block
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1120


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


points = [
    (5.0, 122125), (6.0, 85200), (7.5, 54903),
    (10.0, 31235), (12.5, 20215), (15.0, 14194),
    (20.0, 8159), (25.0, 5333), (30.0, 3781),
]
left, right, top, bottom = 210, 1660, 285, 850
log_min = math.log(3781)
log_max = math.log(122125)


def px(mde):
    return left + (mde - 5.0) / (30.0 - 5.0) * (right - left)


def py(value):
    return bottom - (math.log(value) - log_min) / (log_max - log_min) * (bottom - top)


s = [svg_head(W, H)]
s.append(title_block(
    "樣本數規劃", P["indigo"][1],
    "樣本數與 MDE 的平方反比",
    "基準轉換率 5%，α = 0.05，power = 0.8",
))

# Labelled guide lines make magnitudes readable on the logarithmic scale.
for tick in (5000, 10000, 30000, 100000):
    y = py(tick)
    s.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
             f'stroke="#e6e8ef" stroke-width="2"/>')
    s.append(text(left - 24, y + 7, f"{tick:,}", 19, MUTE, "normal", "end"))
s.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="{FAINT}" stroke-width="3"/>')
s.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{FAINT}" stroke-width="3"/>')

coords = [(px(mde), py(value)) for mde, value in points]
path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in coords)
area = path + f" L{right},{bottom} L{left},{bottom} Z"
s.append(f'<path d="{area}" fill="{P["indigo"][0]}" opacity="0.10"/>')
s.append(f'<path d="{path}" fill="none" stroke="{P["indigo"][0]}" stroke-width="6" '
         f'stroke-linejoin="round" stroke-linecap="round"/>')

for (mde, _), (x, y) in zip(points, coords):
    s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#ffffff" '
             f'stroke="{P["indigo"][0]}" stroke-width="5"/>')

for tick in (5, 10, 15, 20, 25, 30):
    s.append(text(px(tick), bottom + 48, f"+{tick}%", 19, MUTE, "normal", "middle"))

s.append(text(935, 945, "想偵測的相對提升（MDE）", 25, INK, "bold", "middle"))
s.append(f'<text x="82" y="575" font-size="25" fill="{INK}" font-weight="bold" '
         f'text-anchor="middle" transform="rotate(-90 82 575)">每組所需樣本數（對數刻度）</text>')

annotations = {
    5.0: ("+5%（122,125）", 350, 255),
    10.0: ("+10%（31,235）", 600, 445),
    20.0: ("+20%（8,159）", 1180, 675),
}
for index, (mde, _) in enumerate(points):
    if mde not in annotations:
        continue
    value, tx, ty = annotations[mde]
    x, y = coords[index]
    s.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{tx}" y2="{ty+12}" '
             f'stroke="{P["teal"][1]}" stroke-width="3"/>')
    s.append(text(tx, ty, value, 24, P["teal"][1], "bold", "middle"))

# Explicit half-MDE / quadruple-sample comparison.
x5, y5 = coords[0]
x10, y10 = coords[3]
s.append(f'<path d="M{x10:.1f},{y10-32:.1f} C760,310 590,245 {x5+18:.1f},{y5+16:.1f}" '
         f'fill="none" stroke="{P["rose"][0]}" stroke-width="4" stroke-dasharray="10 7" '
         f'marker-end="url(#aFaint)"/>')
s.append(f'<rect x="790" y="225" width="710" height="110" rx="18" fill="#fff7f8" '
         f'stroke="#f4c7c7" filter="url(#soft)"/>')
s.append(text(1145, 275, "MDE 砍半 -> 樣本數約變四倍", 27, P["rose"][1], "bold", "middle"))
s.append(text(1145, 312, "31,235 -> 122,125", 24, P["rose"][1], "bold", "middle"))

s.append(svg_tail())
svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "02-sample-size-vs-mde.svg"
png_path = out_dir / "02-sample-size-vs-mde.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
