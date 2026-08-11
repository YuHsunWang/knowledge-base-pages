# -*- coding: utf-8 -*-
"""產生「型一／型二錯誤與檢定力」圖。"""
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
W, H = 1800, 1080


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    # font-family is injected for every <text> by the post-process at the bottom.
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


def hypothesis_text(x, y, index, suffix, size, color):
    # Deliberately plain "H0"/"H1" rather than a true subscript. Two earlier
    # attempts failed under this renderer:
    #   - U+2080/U+2081 (₀ ₁) have no glyph in Microsoft JhengHei → tofu boxes.
    #   - <tspan> subscripts break twice over: cairosvg ignores percentage
    #     font-size, and with text-anchor="middle" it mis-computes the advance
    #     so the shifted tspans overlap the following text.
    # A plain baseline digit is unambiguous and renders correctly.
    return text(x, y, f"H{index}{suffix}", size, color, "bold", "middle")


def curve_points(mean, sigma, base_y, amplitude, x_min, x_max, steps=160):
    points = []
    for index in range(steps + 1):
        x = x_min + (x_max - x_min) * index / steps
        y = base_y - amplitude * math.exp(-0.5 * ((x - mean) / sigma) ** 2)
        points.append((x, y))
    return points


def line_path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def area_path(points, base_y):
    return (f"M{points[0][0]:.1f},{base_y} L" +
            " L".join(f"{x:.1f},{y:.1f}" for x, y in points) +
            f" L{points[-1][0]:.1f},{base_y} Z")


s = [svg_head(W, H)]
s.append(title_block(
    "統計推論", P["violet"][1],
    "型一／型二錯誤與檢定力",
    "同一個判定門檻，會在兩個可能世界裡造成不同結果",
))

plot_left, plot_right = 120, 1680
base_y, amplitude = 760, 390
threshold = 930
h0 = curve_points(690, 235, base_y, amplitude, plot_left, plot_right)
h1 = curve_points(1125, 235, base_y, amplitude, plot_left, plot_right)

s.append(f'<line x1="{plot_left}" y1="{base_y}" x2="{plot_right}" y2="{base_y}" '
         f'stroke="{FAINT}" stroke-width="3"/>')
s.append(f'<path d="{area_path(h0, base_y)}" fill="{P["sky"][0]}" opacity="0.08"/>')
s.append(f'<path d="{area_path(h1, base_y)}" fill="{P["teal"][0]}" opacity="0.07"/>')

# H0 在門檻右側：型一錯誤。
s.append(f'<clipPath id="rightOfThreshold"><rect x="{threshold}" y="300" '
         f'width="{plot_right-threshold}" height="{base_y-300}"/></clipPath>')
s.append(f'<path d="{area_path(h0, base_y)}" fill="{P["rose"][0]}" opacity="0.52" '
         f'clip-path="url(#rightOfThreshold)"/>')

# H1 在門檻左側：型二錯誤；右側則是檢定力。
s.append(f'<clipPath id="leftOfThreshold"><rect x="{plot_left}" y="300" '
         f'width="{threshold-plot_left}" height="{base_y-300}"/></clipPath>')
s.append(f'<path d="{area_path(h1, base_y)}" fill="{P["amber"][0]}" opacity="0.48" '
         f'clip-path="url(#leftOfThreshold)"/>')
s.append(f'<path d="{area_path(h1, base_y)}" fill="{P["teal"][0]}" opacity="0.42" '
         f'clip-path="url(#rightOfThreshold)"/>')

s.append(f'<path d="{line_path(h0)}" fill="none" stroke="{P["sky"][1]}" stroke-width="5"/>')
s.append(f'<path d="{line_path(h1)}" fill="none" stroke="{P["teal"][1]}" stroke-width="5"/>')
s.append(f'<line x1="{threshold}" y1="280" x2="{threshold}" y2="{base_y+14}" '
         f'stroke="{INK}" stroke-width="3" stroke-dasharray="12 9"/>')

s.append(hypothesis_text(610, 330, 0, "：沒有差異", 27, P["sky"][1]))
s.append(hypothesis_text(1230, 330, 1, "：真的有差異", 27, P["teal"][1]))
s.append(text(threshold, 255, "判定門檻（臨界值）", 23, INK, "bold", "middle"))

# Labels sit directly inside or above their corresponding shaded regions.
s.append(text(430, 535, "型二錯誤 β = 0.20", 26, P["amber"][1], "bold"))
s.append(text(430, 570, "有效果卻沒偵測到", 21, MUTE))

# 型一錯誤標籤放進門檻右側的灰色區域內（該區域才是 α），避免壓到虛線門檻。
s.append(text(1105, 690, "型一錯誤 α = 0.05", 26, P["rose"][1], "bold", "middle"))
s.append(text(1105, 722, "沒效果卻判定有效", 21, INK, "normal", "middle"))

s.append(text(1390, 545, "檢定力 Power = 1 - β = 0.80", 25, P["teal"][1], "bold", "middle"))

s.append(f'<rect x="170" y="865" width="1460" height="105" rx="18" fill="#ffffff" '
         f'stroke="#e6e8ef" filter="url(#soft)"/>')
s.append(text(900, 928, "兩者是蹺蹺板：α 調嚴會讓 β 上升。要同時壓低，只能加樣本。",
              27, INK, "bold", "middle"))
s.append(svg_tail())

svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "01-type-i-ii-error.svg"
png_path = out_dir / "01-type-i-ii-error.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
