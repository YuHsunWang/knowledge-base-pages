# -*- coding: utf-8 -*-
"""One OMP and one Collab session per project."""
from pathlib import Path
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1080
s = [svg_head(W, H), title_block("MULTI-PROJECT · OMP", P["violet"][1],
    "多專案與 Collab Session 配置", "一個專案對應一個 OMP 與 Collab Session。")]
s.append(card(70, 490, 275, 150, "violet", "私人筆電", []))
s.append(card(1430, 490, 300, 150, "indigo", "公司 Browser / 手機", []))
rows = [
    (240, "OMP: project-api", "Collab Session A"),
    (455, "OMP: project-web", "Collab Session B"),
    (670, "OMP: data-pipeline", "Collab Session C"),
]
for y, project, session in rows:
    s.append(card(475, y, 330, 150, "sky", project, []))
    s.append(card(950, y, 340, 150, "teal", session, []))
    s.append(arrow(345, 565, 475, y + 75))
    s.append(arrow(805, y + 75, 950, y + 75))
    s.append(arrow(1430, 565, 1290, y + 75))
s.append(legend_chips([("violet", "Host"), ("sky", "專案 OMP"),
    ("teal", "Collab Session"), ("indigo", "遠端裝置")], 70, 1030))
s.append(svg_tail())
Path(__file__).with_name("05-multi-project.svg").write_text("".join(s), encoding="utf-8")
