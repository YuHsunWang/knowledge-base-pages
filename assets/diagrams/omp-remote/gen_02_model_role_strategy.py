# -*- coding: utf-8 -*-
"""OMP model-role selection."""
from pathlib import Path
import sys

sys.path.insert(0, "/home/user/.claude/skills/synced/f9565756-90c9-438f-a291-8fa2676a13b5_0585d076-22db-425b-8ae9-5732463cfa45/kb-diagrams/scripts")
from diagram_kit import svg_head, svg_tail, title_block, card, arrow, legend_chips, P
import diagram_kit as _dk

_dk.FONT = "Microsoft JhengHei, 微軟正黑體, sans-serif"
W, H = 1800, 1080
s = [svg_head(W, H), title_block("MODEL ROLES · OMP", P["teal"][1],
    "模型角色切換策略", "依任務性質切換 Model Role。")]

s.append(card(70, 480, 300, 145, "indigo", "收到 Coding Task", []))
s.append(card(480, 480, 290, 145, "violet", "任務難度", []))
s.append(arrow(370, 552, 480, 552))
rows = [
    (245, "smol", "低成本快速完成", "小修改 / 搜尋"),
    (440, "default", "主要工作模型", "一般 Coding"),
    (635, "slow", "高推理能力", "架構 / 疑難 Debug"),
    (830, "plan", "產生 Plan", "先規劃再做"),
]
for y, role, result, label in rows:
    s.append(card(945, y, 255, 140, "teal", role, [label]))
    s.append(card(1390, y, 335, 140, "sky", result, []))
    s.append(arrow(770, 552, 945, y + 70))
    s.append(arrow(1200, y + 70, 1390, y + 70))
s.append(legend_chips([("indigo", "工作"), ("violet", "判斷"),
    ("teal", "Model Role"), ("sky", "用途")], 70, 1035))
s.append(svg_tail())
Path(__file__).with_name("02-model-role-strategy.svg").write_text("".join(s), encoding="utf-8")
