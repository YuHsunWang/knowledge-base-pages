# -*- coding: utf-8 -*-
"""Mobile push notification path."""
from pathlib import Path
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1020
s = [svg_head(W, H), title_block("NOTIFICATION · OMP", P["rose"][1],
    "手機 Push Notification 流程", "Agent 事件經 Extension 與通知服務送達手機。")]
nodes = [
    (70, 400, 315, "violet", "OMP Agent", []),
    (515, 400, 315, "sky", "OMP Extension", []),
    (960, 400, 315, "rose", "ntfy / Telegram", ["Pushover"]),
    (1405, 400, 315, "indigo", "iPhone / Android", ["Push"]),
]
for x, y, w, phase, title, lines in nodes:
    s.append(card(x, y, w, 175, phase, title, lines))
for x1, x2 in [(385, 515), (830, 960), (1275, 1405)]:
    s.append(arrow(x1, 488, x2, 488))
s.append('<text x="450" y="365" text-anchor="middle" font-size="19" fill="#5b6472">agent_end / error</text>')
s.append('<text x="895" y="365" text-anchor="middle" font-size="19" fill="#5b6472">HTTPS POST</text>')
s.append(legend_chips([("violet", "Host / Agent"), ("sky", "Extension"),
    ("rose", "通知服務"), ("indigo", "手機")], 70, 970))
s.append(svg_tail())
Path(__file__).with_name("04-mobile-push.svg").write_text("".join(s), encoding="utf-8")
