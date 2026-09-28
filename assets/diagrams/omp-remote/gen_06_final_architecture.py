# -*- coding: utf-8 -*-
"""Complete remote coding-agent architecture."""
from pathlib import Path
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1120
s = [svg_head(W, H), title_block("ARCHITECTURE · FINAL", P["indigo"][1],
    "OMP 遠端 Coding Agent 最終架構", "遠端控制、Host 工具、模型與通知的整合架構。")]
nodes = [
    (70, 300, 290, 150, "indigo", "其他電腦", ["Chrome / Edge"]),
    (70, 550, 290, 150, "indigo", "手機", ["Safari / Chrome"]),
    (455, 420, 300, 155, "teal", "OMP Collab Relay", []),
    (870, 420, 315, 155, "violet", "私人筆電", ["OMP Host"]),
    (1380, 245, 345, 125, "sky", "Git / Docker", []),
    (1380, 410, 345, 125, "sky", "Database", []),
    (1380, 575, 345, 135, "sky", "Python / Node", ["Project Files"]),
    (870, 780, 315, 160, "amber", "AI Providers", ["Claude / OpenAI"]),
    (1380, 800, 345, 160, "amber", "Gemini / OpenRouter", ["Custom API"]),
    (455, 780, 300, 160, "rose", "Notification", ["ntfy / Telegram"]),
]
for x, y, w, h, phase, title, lines in nodes:
    s.append(card(x, y, w, h, phase, title, lines))
for points in [
    (360, 375, 455, 465), (360, 625, 455, 530),
    (755, 498, 870, 498),
    (1185, 465, 1380, 307), (1185, 495, 1380, 472),
    (1185, 530, 1380, 643),
    (1027, 575, 1027, 780), (1185, 860, 1380, 880),
    (870, 540, 755, 840),
]:
    s.append(arrow(*points))
s.append('<text x="828" y="700" font-size="19" fill="#5b6472" stroke="#f6f7fb" stroke-width="6" paint-order="stroke">agent_end</text>')
s.append('<path d="M455,875 L400,875 L400,625 L360,625" fill="none" stroke="#8a93a6" stroke-width="2.4" marker-end="url(#aFaint)"/>')
s.append('<text x="412" y="755" font-size="19" fill="#5b6472" stroke="#f6f7fb" stroke-width="6" paint-order="stroke">Push</text>')
s.append(legend_chips([("indigo", "遠端裝置"), ("teal", "Relay"),
    ("violet", "Host"), ("sky", "工具"), ("amber", "AI Providers"),
    ("rose", "通知")], 70, 1078))
s.append(svg_tail())
Path(__file__).with_name("06-final-architecture.svg").write_text("".join(s), encoding="utf-8")
