# -*- coding: utf-8 -*-
"""OMP remote-control architecture."""
from pathlib import Path
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1120
s = [svg_head(W, H), title_block("ARCHITECTURE · OMP", P["indigo"][1],
    "OMP 遠端控制整體架構", "遠端裝置控制 Session；工具與程式碼保留在 Host。")]

nodes = [
    (70, 275, 290, 150, "indigo", "其他電腦", ["Chrome / Edge"]),
    (70, 515, 290, 150, "indigo", "手機", ["Safari / Chrome"]),
    (460, 395, 300, 165, "teal", "OMP Collab", ["my.omp.sh"]),
    (870, 395, 310, 165, "violet", "私人筆電", ["OMP Host"]),
    (1390, 220, 330, 125, "sky", "Git Repository", []),
    (1390, 380, 330, 125, "sky", "Docker / DB", []),
    (1390, 540, 330, 125, "sky", "Python / Node.js", []),
    (1390, 700, 330, 125, "sky", "Local Files", []),
    (870, 755, 310, 125, "amber", "AI Model Providers", []),
    (1390, 835, 330, 110, "amber", "Anthropic / OpenAI", []),
    (1390, 955, 330, 130, "amber", "Gemini / OpenRouter", ["Custom API"]),
]
for x, y, w, h, phase, title, lines in nodes:
    s.append(card(x, y, w, h, phase, title, lines))

for points in [
    (360, 350, 460, 445), (360, 590, 460, 510),
    (760, 478, 870, 478),
    (1180, 430, 1390, 283), (1180, 460, 1390, 443),
    (1180, 495, 1390, 603), (1180, 525, 1390, 763),
    (1025, 560, 1025, 755),
    (1180, 805, 1390, 890), (1180, 835, 1390, 1020),
]:
    s.append(arrow(*points))
s.append('<text x="377" y="340" font-size="18" fill="#5b6472">HTTPS / WebSocket</text>')
s.append('<text x="377" y="600" font-size="18" fill="#5b6472">HTTPS / WebSocket</text>')
s.append(legend_chips([("indigo", "遠端裝置"), ("teal", "Relay"),
    ("violet", "Host"), ("sky", "工具"), ("amber", "AI Providers")], 70, 1098))
s.append(svg_tail())
Path(__file__).with_name("01-overall-architecture.svg").write_text("".join(s), encoding="utf-8")
