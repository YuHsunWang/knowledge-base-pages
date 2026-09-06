# -*- coding: utf-8 -*-
"""產生「目標價的三段拆解」圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import BORDER, CARD, FAINT, INK, MUTE, P, svg_head, svg_tail
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1180


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


steps = [
    {
        "number": "1", "phase": "sky", "title": "建立 EPS 基礎",
        "lines": ["落後 / 當年年化 / 正常化 三種並列", "再做品質調整", "業外、非控制權益", "併購併表、股本稀釋"],
    },
    {
        "number": "2", "phase": "violet", "title": "選估值錨與倍數",
        "lines": ["逐家分流", "國巨 EV/EBITDA+SOTP", "華新科 P/B band", "禾伸堂分部估值", "大毅轉型後正常化 EPS"],
    },
    {
        "number": "3", "phase": "teal", "title": "情境化與反推",
        "lines": ["三情境目標價矩陣", "用股價反推隱含假設", "寫下失效條件"],
    },
]

s = [svg_head(W, H)]
s.append(text(70, 112, "目標價的三段拆解", 46, INK, "bold"))

card_y, card_w, card_h = 230, 490, 400
xs = [70, 655, 1240]
for x, step in zip(xs, steps):
    base, dark = P[step["phase"]]
    s.append(f'<rect x="{x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="22" '
             f'fill="{CARD}" stroke="{BORDER}" filter="url(#soft)"/>')
    s.append(f'<path d="M{x+22},{card_y} h{card_w-44} a22,22 0 0 1 22,22 v8 '
             f'h-{card_w} v-8 a22,22 0 0 1 22,-22 z" fill="{base}"/>')
    s.append(f'<circle cx="{x+58}" cy="{card_y+84}" r="30" fill="{base}"/>')
    s.append(text(x + 58, card_y + 94, step["number"], 29, CARD, "bold", "middle"))
    s.append(text(x + 105, card_y + 94, step["title"], 28, dark, "bold"))
    yy = card_y + 160
    for line in step["lines"]:
        s.append(f'<circle cx="{x+42}" cy="{yy-7}" r="4.5" fill="{base}"/>')
        s.append(text(x + 58, yy, line, 20, MUTE))
        yy += 47

for x1, x2 in ((560, 655), (1145, 1240)):
    s.append(f'<line x1="{x1+12}" y1="430" x2="{x2-18}" y2="430" stroke="{FAINT}" '
             f'stroke-width="5" marker-end="url(#aFaint)"/>')

# Three scenario outputs show a range rather than a single point estimate.
scenario_y = 700
scenario = [
    ("空方", 280, "#fee2e2", "#be123c"),
    ("基準", 390, "#fef3c7", "#b45309"),
    ("多方", 500, "#dcfce7", "#15803d"),
]
bar_x = 295
for i, (label, width, fill, color) in enumerate(scenario):
    y = scenario_y + i * 72
    s.append(text(bar_x - 34, y + 38, label, 22, color, "bold", "end"))
    s.append(f'<rect x="{bar_x}" y="{y}" width="{width}" height="52" rx="14" '
             f'fill="{fill}" stroke="{color}" stroke-opacity="0.45"/>')

warning_x, warning_y, warning_w, warning_h = 900, 704, 800, 190
s.append(f'<rect x="{warning_x}" y="{warning_y}" width="{warning_w}" height="{warning_h}" rx="20" '
         f'fill="#fff1f2" stroke="#fecdd3" stroke-width="3" filter="url(#soft)"/>')
s.append(f'<circle cx="{warning_x+58}" cy="{warning_y+62}" r="26" fill="{P["rose"][0]}"/>')
s.append(text(warning_x + 58, warning_y + 71, "!", 31, CARD, "bold", "middle"))
s.append(text(warning_x + 104, warning_y + 58, "最常見的錯：用景氣高點的 EPS，", 25, P["rose"][1], "bold"))
s.append(text(warning_x + 104, warning_y + 103, "再給景氣高點的倍數 -", 25, P["rose"][1], "bold"))
s.append(text(warning_x + 104, warning_y + 148, "目標價被放大兩次。", 25, P["rose"][1], "bold"))
s.append(text(W / 2, 1060, "週期股的目標價不是一個數字，是一組帶條件的情境。",
              29, INK, "bold", "middle"))
s.append(svg_tail())

svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "10-target-price-scenarios.svg"
png_path = out_dir / "10-target-price-scenarios.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
