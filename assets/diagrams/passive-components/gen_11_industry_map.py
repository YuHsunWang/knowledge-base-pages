# -*- coding: utf-8 -*-
"""產生「台股被動元件產業地圖」旗艦圖。"""
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, "/home/user/.claude/plugins/marketplaces/local/plugins/kb-diagrams/skills/kb-diagrams/scripts")
import diagram_kit as _dk
import cairosvg

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
FONT = _dk.FONT
W, H = 2000, 1400

UP = "#f59e0b"
UP_DARK = "#b45309"
MID = "#3b82f6"
MID_DARK = "#1d4ed8"
DOWN = "#14b8a6"
DOWN_DARK = "#0f766e"
ROSE = "#e11d48"
INK = "#172033"
MUTE = "#667085"
CARD = "#ffffff"
HIGHLIGHTS = {"國巨(2327)", "華新科(2492)", "禾伸堂(3026)", "大毅(2478)"}


def text(x, y, value, size=20, color=INK, weight="normal", anchor="start", opacity=None):
    opacity_attr = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{opacity_attr}>{escape(value)}</text>')


def estimate_width(value, size):
    """Conservative width estimate for mixed Traditional Chinese and ASCII."""
    return sum(size if ord(ch) > 127 else size * 0.57 for ch in value)


def company_lines(x, y, rows, size=20, line_gap=31, gap=18):
    """Render pre-wrapped company rows, preserving entry-level highlights."""
    out = []
    for row_index, row in enumerate(rows):
        cursor = x
        baseline = y + row_index * line_gap
        for company in row:
            color = ROSE if company in HIGHLIGHTS else INK
            weight = "bold" if company in HIGHLIGHTS else "normal"
            out.append(text(cursor, baseline, company, size, color, weight))
            cursor += estimate_width(company, size) + gap
    return "".join(out)


def band_tab(y, h, label, color):
    return (f'<rect x="30" y="{y}" width="132" height="{h}" rx="22" fill="{color}"/>'
            + text(96, y + h / 2 + 11, label, 28, CARD, "bold", "middle"))


def card_height(rows, description="", line_gap=31):
    """Height that fits the content, so short cards do not leave dead space."""
    body_top = 120 if description else 91
    return body_top + max(0, len(rows) - 1) * line_gap + 34


def category_card(x, y, w, h, color, dark, title, rows, description="", body_size=20):
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" '
        f'stroke="#e7eaf0" filter="url(#cardShadow)"/>',
        f'<path d="M{x+18},{y} h{w-36} a18,18 0 0 1 18,18 v4 h-{w} v-4 '
        f'a18,18 0 0 1 18,-18 z" fill="{color}"/>',
        text(x + 24, y + 54, title, 24, dark, "bold"),
    ]
    body_y = y + 91
    if description:
        out.append(text(x + 24, y + 84, description, 17, MUTE))
        body_y = y + 120
    out.append(company_lines(x + 24, body_y, rows, body_size))
    return "".join(out)


def demand_card(x, y, w, label):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="66" rx="14" '
            f'fill="#ecfdf8" stroke="#5eead4" stroke-width="2"/>'
            + text(x + w / 2, y + 42, label, 21, DOWN_DARK, "bold", "middle"))


s = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="darkBg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0f172a"/>
    <stop offset="1" stop-color="#1e1b4b"/>
  </linearGradient>
  <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="150%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="8" result="blur"/>
    <feOffset in="blur" dx="0" dy="7" result="offsetBlur"/>
    <feFlood flood-color="#020617" flood-opacity="0.30" result="shadowColor"/>
    <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
    <feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect x="0" y="0" width="{W}" height="{H}" rx="28" fill="url(#darkBg)"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="27" fill="none" stroke="#ffffff" stroke-opacity="0.10"/>
''']

# Header and legend.
s.append(text(W / 2, 72, "台股被動元件產業地圖", 46, CARD, "bold", "middle"))
s.append(text(W / 2, 116, "上游材料 8 家・中游製造 26 家・下游通路 5 家（去重後 37 家）",
              22, CARD, "normal", "middle", 0.70))
s.append(f'<rect x="785" y="136" width="430" height="36" rx="18" fill="#ffffff" fill-opacity="0.10"/>')
s.append(f'<circle cx="817" cy="154" r="7" fill="{ROSE}"/>')
s.append(text(837, 161, "玫瑰色：系列深度覆蓋公司", 18, CARD, "bold", opacity=0.88))

# Layout runs top-down from a cursor. Card heights follow their content so that a
# short card (e.g. 材料與設備通路, one company) does not leave half the box empty.
PAD = 14
cursor = 190

# ---- Upstream band ----
up_cards = [
    (190, "電阻器材料", "氧化鋁陶瓷基板、導電漿墨", [["鑫科(3663)", "艾華(6204)"], ["勤凱(4760)"]]),
    (638, "電容器材料", "化成鋁箔、介面瓷粉", [["信昌電(6173)", "立敦(6175)"], ["九豪(6127)"]]),
    (1086, "電感器材料", "鐵氧體、導電漿墨", [["越峰(8121)", "勤凱(4760)"]]),
    (1534, "材料與設備通路", "", [["崇越(5434)"]]),
]
up_card_h = max(card_height(rows, desc) for _, _, desc, rows in up_cards)
s.append(band_tab(cursor, up_card_h + 2 * PAD, "上游", UP))
for x, title_value, description, rows in up_cards:
    s.append(category_card(x, cursor + PAD, 416, up_card_h, UP, UP_DARK,
                           title_value, rows, description))
cursor += up_card_h + 2 * PAD + 34

# ---- Midstream band: two rows of manufacturing cards plus the delisting note ----
mid_row1 = [
    (190, "晶片電阻", [["國巨(2327)", "華新科(2492)", "大毅(2478)"],
                       ["興勤(2428)", "光頡(3624)", "雷科(6207)"],
                       ["天二(6834)", "台達電(2308)"]]),
    (785, "陶瓷電容 MLCC", [["國巨(2327)", "華新科(2492)"], ["禾伸堂(3026)"]]),
    (1380, "鋁質電解電容", [["立隆電(2472)", "凱美(2375)", "鈺邦(6449)"],
                            ["環科(2413)", "堡達(3537)", "華容(5328)"]]),
]
mid_row2 = [
    (190, "電感／磁性元件", [["臺慶科(3357)", "鈞寶(6155)", "千如(3236)"],
                             ["新聿科(7912)", "敦吉(2459)", "台達電(2308)"],
                             ["佳邦(6284)"]]),
    (785, "保護元件", [["聚鼎(6224)", "興勤(2428)", "佳邦(6284)"]]),
    (1380, "石英／振盪元件", [["晶技(3042)", "希華(2484)"],
                              ["台嘉碩(3221)", "加高(8182)"]]),
]
row1_h = max(card_height(rows) for _, _, rows in mid_row1)
row2_h = max(card_height(rows) for _, _, rows in mid_row2)
NOTE_H, ROW_GAP = 43, 20
mid_h = PAD + row1_h + ROW_GAP + row2_h + ROW_GAP + NOTE_H + PAD
s.append(band_tab(cursor, mid_h, "中游", MID))
row1_y = cursor + PAD
for x, title_value, rows in mid_row1:
    s.append(category_card(x, row1_y, 570, row1_h, MID, MID_DARK, title_value, rows))
row2_y = row1_y + row1_h + ROW_GAP
for x, title_value, rows in mid_row2:
    s.append(category_card(x, row2_y, 570, row2_h, MID, MID_DARK, title_value, rows))
note_y = row2_y + row2_h + ROW_GAP
s.append(f'<rect x="190" y="{note_y}" width="1760" height="{NOTE_H}" rx="12" '
         f'fill="#dbeafe" fill-opacity="0.18" stroke="#93c5fd" stroke-opacity="0.38"/>')
s.append(text(1070, note_y + 28,
              "奇力新(2456) 已於 2022 年下市併入國巨，磁性元件併入其產品線。",
              17, "#dbeafe", "normal", "middle"))
cursor += mid_h + 34

# ---- Downstream band: demand segments are flat tinted cards; 通路 is a company card ----
down_rows = [["禾伸堂(3026)", "蜜望實(8043)", "日電貿(3090)"], ["敦吉(2459)", "增你強(3028)"]]
down_card_h = card_height(down_rows)
down_h = down_card_h + 2 * PAD
s.append(band_tab(cursor, down_h, "下游", DOWN))
s.append(text(190, cursor + PAD + 26, "終端應用（需求領域）", 19, "#99f6e4", "bold"))
demand_y = cursor + PAD + 46
demand_labels = ["AI 伺服器", "車用電子", "工控與能源", "消費電子（手機・PC）"]
for i, label in enumerate(demand_labels):
    s.append(demand_card(190 + i * 290, demand_y, 270, label))
s.append(text(190, demand_y + 108,
              "被動元件的需求來自這四個終端，其中 AI 伺服器與車用是目前的成長主軸。",
              17, "#99f6e4", "normal", opacity=0.85))
s.append(category_card(1350, cursor + PAD, 600, down_card_h, DOWN, DOWN_DARK, "通路",
                       down_rows, body_size=20))
cursor += down_h + 26

# Bottom source caption, anchored to the layout cursor rather than a fixed y.
s.append(f'<rect x="30" y="{cursor}" width="1940" height="54" rx="14" fill="#ffffff" fill-opacity="0.08"/>')
s.append(text(W / 2, cursor + 33,
              "分類與代號整理自 TPEX 產業價值鏈平台與公司公開資料，並以 TWSE／TPEx 上市櫃基本資料核對代號。部分公司跨多個品類，故各列合計大於去重家數。",
              16, CARD, "normal", "middle", 0.70))
s.append("</svg>")

# Shrink the canvas to the height the layout actually consumed, so the dark background
# does not extend past the content. H is only an upper bound while building.
H_FINAL = cursor + 54 + 30
svg = "".join(s)
svg = svg.replace(f'height="{H}"', f'height="{H_FINAL}"')
svg = svg.replace(f'viewBox="0 0 {W} {H}"', f'viewBox="0 0 {W} {H_FINAL}"')
svg = svg.replace(f'height="{H - 2}"', f'height="{H_FINAL - 2}"')
svg = svg.replace("<text ", f'<text font-family="{FONT}" ')
out_dir = Path(__file__).resolve().parent
svg_path = out_dir / "11-industry-map.svg"
png_path = out_dir / "11-industry-map.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W)
print(f"wrote {svg_path}")
print(f"wrote {png_path}")
