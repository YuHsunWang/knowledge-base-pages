# -*- coding: utf-8 -*-
"""產生「被動元件景氣循環五階段」圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
from diagram_kit import BORDER, CARD, FAINT, INK, MUTE, P, svg_head, svg_tail
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 1800, 1200


def text(x, y, value, size=22, color=INK, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


stages = [
    {
        "title": "1. 過熱 Overbooking", "base": "#ef4444", "dark": "#b91c1c", "tint": "#fff1f2",
        "signals": ["現貨溢價 >10%", "Lead time 拉長至 20 週以上", "客戶 double order",
                    "稼動率 90-95%", "新 Capex 公告"],
        "quote": ["「需求強勁，產能供不應求，", "ASP 調升。」"],
    },
    {
        "title": "2. 轉折 Inventory Peak", "base": P["amber"][0], "dark": P["amber"][1], "tint": "#fffbeb",
        "signals": ["現貨溢價縮小", "代理庫存轉增", "Lead time 開始縮短",
                    "終端季節性不如預期"],
        "quote": ["「庫存健康，但需持續", "觀察通路端。」"],
    },
    {
        "title": "3. 衰退 Destocking", "base": "#64748b", "dark": "#475569", "tint": "#f1f5f9",
        "signals": ["月營收 MoM 連續下滑", "月營收 YoY 轉負", "毛利率快速下墜", "稼動率跌破 70%",
                    "現貨跌破合約價"],
        "quote": ["「客戶積極去化庫存，", "能見度低，短期保守。」"],
    },
    {
        "title": "4. 築底 Bottoming", "base": P["sky"][0], "dark": P["sky"][1], "tint": "#f0f9ff",
        "signals": ["月營收 MoM 跌幅收斂", "代理商庫存天數探底", "稼動率止跌未拉升",
                    "Lead time 趨穩"],
        "quote": ["「底部訊號出現，但復甦", "時間點不確定。」"],
    },
    {
        "title": "5. 復甦 Early Recovery", "base": "#22c55e", "dark": "#15803d", "tint": "#f0fdf4",
        "signals": ["急單出現", "月營收連 2-3 月正成長", "ASP 止跌",
                    "稼動率回升至 75-80%", "Capex 重啟"],
        "quote": ["「需求回溫，庫存調整", "接近尾聲。」"],
    },
]

s = [svg_head(W, H)]
s.append(text(70, 112, "被動元件景氣循環五階段", 46, INK, "bold"))

card_y, card_w, card_h, gap = 245, 312, 575, 30
xs = [60 + i * (card_w + gap) for i in range(5)]
for x, stage in zip(xs, stages):
    s.append(f'<rect x="{x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="20" '
             f'fill="{CARD}" stroke="{BORDER}" filter="url(#soft)"/>')
    s.append(f'<path d="M{x+20},{card_y} h{card_w-40} a20,20 0 0 1 20,20 v8 '
             f'h-{card_w} v-8 a20,20 0 0 1 20,-20 z" fill="{stage["base"]}"/>')
    s.append(text(x + 22, card_y + 72, stage["title"], 23, stage["dark"], "bold"))
    s.append(text(x + 22, card_y + 119, "訊號：", 20, INK, "bold"))
    yy = card_y + 158
    for signal in stage["signals"]:
        s.append(f'<circle cx="{x+28}" cy="{yy-7}" r="4.5" fill="{stage["base"]}"/>')
        s.append(text(x + 42, yy, signal, 18, MUTE))
        yy += 37
    quote_y = card_y + 402
    s.append(f'<rect x="{x+18}" y="{quote_y}" width="{card_w-36}" height="142" rx="14" '
             f'fill="{stage["tint"]}" stroke="{stage["base"]}" stroke-opacity="0.35"/>')
    s.append(text(x + 34, quote_y + 34, "法說語氣：", 18, stage["dark"], "bold"))
    for i, line in enumerate(stage["quote"]):
        s.append(text(x + 34, quote_y + 72 + i * 30, line, 17, INK))

# Forward direction and the return path make the five cards a closed cycle.
flow_y = 882
for i in range(4):
    s.append(f'<line x1="{xs[i]+card_w-6}" y1="{flow_y}" x2="{xs[i+1]+6}" y2="{flow_y}" '
             f'stroke="{FAINT}" stroke-width="4" marker-end="url(#aFaint)"/>')
s.append(f'<path d="M{xs[4]+card_w/2},{flow_y} L{xs[4]+card_w/2},995 '
         f'L{xs[0]+card_w/2},995 L{xs[0]+card_w/2},{flow_y}" fill="none" '
         f'stroke="{P["violet"][0]}" stroke-width="4" stroke-dasharray="12 8" marker-end="url(#aViolet)"/>')
s.append(text(W / 2, 980, "循環", 24, P["violet"][1], "bold", "middle"))
s.append(text(W / 2, 1100, "被動元件景氣通常落後電子供應鏈 1-2 個季度，且因牛鞭效應而放大。",
              27, INK, "bold", "middle"))
s.append(svg_tail())

svg = "".join(s).replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "08-inventory-cycle-stages.svg"
png_path = out_dir / "08-inventory-cycle-stages.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
