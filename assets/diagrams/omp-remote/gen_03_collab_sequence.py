# -*- coding: utf-8 -*-
"""Collab prompt, tool, and result sequence."""
from pathlib import Path
from html import escape
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1080
s = [svg_head(W, H), title_block("SEQUENCE · COLLAB", P["teal"][1],
    "Collab 資料與控制流程", "Tools 在 Host 執行，結果傳回遠端瀏覽器。")]
actors = [
    (70, 270, "indigo", "手機", []),
    (410, 270, "indigo", "其他電腦", []),
    (750, 270, "teal", "OMP Collab Relay", []),
    (1090, 270, "violet", "私人筆電 OMP Host", []),
    (1430, 270, "sky", "Git / Bash", ["Docker / DB"]),
]
for x, y, phase, title, lines in actors:
    s.append(card(x, y, 300, 135, phase, title, lines))
centers = [220, 560, 900, 1240, 1580]
for x in centers:
    s.append(f'<line x1="{x}" y1="405" x2="{x}" y2="985" stroke="#d1d8e4" stroke-width="2" stroke-dasharray="6 7"/>')
flows = [
    (220, 900, 470, "Prompt"),
    (560, 900, 535, "Prompt"),
    (900, 1240, 600, "Session Input"),
    (1240, 1580, 665, "Tool / Shell"),
    (1580, 1240, 730, "執行結果"),
    (1240, 900, 795, "Streaming Result"),
    (900, 220, 860, "顯示結果"),
    (900, 560, 925, "顯示結果"),
]
for x1, x2, y, label in flows:
    end = x2 - 9 if x2 > x1 else x2 + 9
    s.append(arrow(x1, y, end, y))
    s.append(f'<text x="{(x1+x2)/2}" y="{y-13}" text-anchor="middle" font-size="20" fill="#5b6472">{escape(label)}</text>')
s.append(legend_chips([("indigo", "遠端裝置"), ("teal", "Relay"),
    ("violet", "Host"), ("sky", "工具")], 70, 1030))
s.append(svg_tail())
Path(__file__).with_name("03-collab-sequence.svg").write_text("".join(s), encoding="utf-8")
