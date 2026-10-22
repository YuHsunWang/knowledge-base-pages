#!/usr/bin/env python3
"""Redraw the eight "B" figures from the 2026-10-22 image audit; SVG + PNG.
Diagram Design, profile kb-night (site dark tokens). Same render contract as
passive-components/redraw_20261013.py: subset Noto Sans CJK TC embedded in the
SVG, PNG rendered from it with Chromium at 2x. Run from any cwd.
Deps (not in requirements.txt, which is the site build):
  pip install fonttools playwright && playwright install chromium
Pass the full NotoSansCJKtc-Regular.otf path as argv[1] (glyphs are subset).
Replaces the old light generators: rag/gen_02, prompt-engineering/gen_02,
statistics-ab-testing/gen_01, omp-remote/gen_06, serenity-research/gen_decision_tree.
"""
from pathlib import Path
from html import escape
import base64, io, math, re, sys
from fontTools.ttLib import TTFont
from fontTools import subset
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent            # docs/assets/diagrams
DOCS = ROOT.parent.parent
PAPER = '#111729'; CARD = '#182038'; INK = '#C9CDD6'; MUTED = '#9AA0AD'; SOFT = '#6C7BA0'
RULE = '#2E3D66'; ACCENT = '#7CC0FF'; ORANGE = '#F0A868'
FOCAL = 'rgba(124,192,255,0.10)'; W = 1280
FIGURES = []


def text(x, y, s, size=20, color=INK, weight=400, anchor='start'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(str(s))}</text>')


def rect(x, y, w, h, fill=CARD, stroke=RULE, rx=8, dash=None, sw=1):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def path(d, color=MUTED, dashed=False, marker='arrow', sw=1.6):
    dash = ' stroke-dasharray="6,5"' if dashed else ''
    m = f' marker-end="url(#{marker})"' if marker else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dash}{m}/>'


def arrow(x1, y1, x2, y2, **kw):
    assert x1 == x2 or y1 == y2, 'straight arrows only; use path() with r=8 elbows'
    return path(f'M{x1},{y1} L{x2},{y2}', **kw)


def twidth(s, size):
    return sum(size if ord(c) > 0x2e80 else size * 0.56 for c in s)


def label(cx, line_y, s, size=16, color=MUTED):
    """Masked arrow label 8px above a horizontal connector."""
    w = math.ceil((twidth(s, size) + 16) / 4) * 4
    return rect(cx - w // 2, line_y - 32, w, 24, PAPER, PAPER, 2) + text(cx, line_y - 14, s, size, color, 400, 'middle')


def node(x, y, w, h, title, lines=(), focal=False, center=False, tsize=24, lsize=16):
    s = rect(x, y, w, h, FOCAL if focal else CARD, ACCENT if focal else RULE)
    tx, anc = (x + w // 2, 'middle') if center else (x + 20, 'start')
    s += text(tx, y + 40, title, tsize, ACCENT if focal else INK, 600, anc)
    for i, l in enumerate(lines):
        s += text(tx, y + 76 + i * 28, l, lsize, MUTED, 400, anc)
    return s


class Figure:
    def __init__(self, out, title, subtitle, h, desc):
        self.out = out; self.title = title; self.h = h; self.desc = desc
        self.parts = [rect(0, 0, W, h, PAPER, PAPER, 0), text(40, 64, title, 32, INK, 600), text(40, 104, subtitle, 20, MUTED)]

    def add(self, *s):
        self.parts.extend(s)

    def save(self):
        FIGURES.append(self)


# B1 rag/02: four parallel strategies hang off one bus (old art read as a chain
# and its lines crossed the HyDE card).
f = Figure('rag/02-query-transformation', 'Query Transformation 查詢轉換策略',
           '先改寫使用者的問題，再拿去搜尋；四種策略彼此獨立，可單用也可組合。', 600,
           '使用者問題可經 Multi-Query、HyDE、Step-Back、Decomposition 四種獨立策略轉換後再檢索。')
cards = [('Multi-Query', '多角度重寫', '一問化多問', ['改寫成 3–5 種問法', '各自搜尋後去重合併', '適合問法模糊時']),
         ('HyDE', '假設文件嵌入', '用假答案去搜尋', ['LLM 先寫一個假設答案', '用答案的向量去搜尋', '答案比問題更像文件']),
         ('Step-Back', '先退一步', '先問背景再問細節', ['把問題抽象成廣泛概念', '補上背景再回答細節', '適合要先驗知識的推理']),
         ('Decomposition', '拆解子問題', '複雜問題拆成子問題', ['多跳問題拆成獨立子題', '各自搜尋並回答', '合併子答案成最終答案'])]
cx = [40 + i * 304 + 140 for i in range(4)]
f.add(path('M640,232 V272', marker=None), path(f'M640,272 H{cx[0]+8} Q{cx[0]},272 {cx[0]},280 V312'),
      path(f'M640,272 H{cx[3]-8} Q{cx[3]},272 {cx[3]},280 V312'), arrow(cx[1], 272, cx[1], 312), arrow(cx[2], 272, cx[2], 312))
f.add(node(520, 152, 240, 80, '使用者問題', focal=True, center=True), text(640, 216, 'User Query', 16, MUTED, 400, 'middle'))
for i, (name, zh, tag, ls) in enumerate(cards):
    x = 40 + i * 304
    f.add(rect(x, 312, 280, 240), text(x + 20, 352, name, 24, INK, 600), text(x + 20, 384, zh, 20, MUTED),
          f'<line x1="{x+20}" y1="404" x2="{x+260}" y2="404" stroke="{RULE}"/>', text(x + 20, 440, tag, 20, ACCENT, 600))
    for j, l in enumerate(ls):
        f.add(text(x + 20, 476 + j * 28, l, 16, MUTED))
f.save()

# B2 prompt-engineering/02: same endpoints in both rows, so CoT visibly fills the gap.
f = Figure('prompt-engineering/02-chain-of-thought', 'Chain of Thought（CoT）',
           '讓模型把中間推理步驟寫出來：複雜問題更準，也看得到哪一步錯。', 640,
           '直接回答從問題一步跳到答案；Chain of Thought 經過理解、推導、驗證三步再輸出答案。')
xs = [44 + i * 248 for i in range(5)]
f.add(text(44, 176, '直接回答（Direct Prompting）', 20, MUTED, 600))
f.add(arrow(244, 240, 1036, 240, dashed=True), label(640, 240, '一步跳到答案'))
f.add(node(xs[0], 196, 200, 88, '問題', ['輸入'], center=True), node(xs[4], 196, 200, 88, '答案', ['輸出'], center=True))
f.add(text(44, 320, '問題：答錯了也看不出是哪一步錯，幻覺不容易被發現。', 16, MUTED))
f.add(text(44, 392, 'Chain of Thought（逐步推理）', 20, ACCENT, 600))
for i in range(4):
    f.add(arrow(xs[i] + 200, 456, xs[i + 1], 456, color=ACCENT if i == 3 else MUTED, marker='arrow-accent' if i == 3 else 'arrow'))
steps = [('問題', '輸入'), ('理解問題', '步驟 1'), ('逐步推導', '步驟 2'), ('自我驗證', '步驟 3'), ('答案', '輸出')]
for i, (t, sub) in enumerate(steps):
    f.add(node(xs[i], 412, 200, 88, t, [sub], focal=i == 4, center=True))
f.add(text(44, 536, '好處：推理和數學題的準確率明顯較高；每一步都能檢查、修正。', 16, MUTED))
f.add(f'<line x1="40" y1="576" x2="1240" y2="576" stroke="{RULE}"/>',
      text(44, 608, 'Zero-shot 用法：在提示最後加一句「讓我們一步步思考」。', 16, SOFT))
f.save()

# B3 statistics-ab-testing/01: one-sided z test, alpha 0.05, power 0.80. Leaders
# point at each region so alpha/beta/power labels cannot be confused.
f = Figure('statistics-ab-testing/01-type-i-ii-error', '型一／型二錯誤與檢定力',
           '同一條判定門檻，放進兩個可能的世界，會犯不同的錯。', 696,
           '虛無假設與對立假設兩條分布被同一條臨界值切開：α=0.05 的型一錯誤、β=0.20 的型二錯誤與 0.80 的檢定力。')
CRIT, MU1 = 1.6449, 1.6449 + 0.8416
px = lambda v: 80 + (v + 3.6) * 1120 / 9.6
py = lambda d: 520 - d * 652
pdf = lambda v, m: math.exp(-((v - m) ** 2) / 2) / math.sqrt(2 * math.pi)
def curve(m, a, b, closed=False):
    n = 160
    pts = [(px(a + (b - a) * k / n), py(pdf(a + (b - a) * k / n, m))) for k in range(n + 1)]
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return d + f' L{pts[-1][0]:.1f},520 L{pts[0][0]:.1f},520 Z' if closed else d
f.add(f'<path d="{curve(MU1, CRIT, 6.0, True)}" fill="rgba(124,192,255,0.20)"/>',
      f'<path d="{curve(MU1, -3.6, CRIT, True)}" fill="rgba(154,160,173,0.28)"/>',
      f'<path d="{curve(0, CRIT, 6.0, True)}" fill="{ORANGE}" fill-opacity="0.75"/>',
      f'<path d="{curve(0, -3.6, 6.0)}" fill="none" stroke="{MUTED}" stroke-width="2"/>',
      f'<path d="{curve(MU1, -3.6, 6.0)}" fill="none" stroke="{ACCENT}" stroke-width="2"/>',
      f'<line x1="80" y1="520" x2="1200" y2="520" stroke="{RULE}" stroke-width="1.2"/>')
cx = round(px(CRIT))
f.add(f'<line x1="{cx}" y1="200" x2="{cx}" y2="520" stroke="{INK}" stroke-width="1.6" stroke-dasharray="6,5"/>',
      text(cx, 188, '判定門檻（臨界值）', 16, INK, 600, 'middle'),
      text(round(px(0)), 244, 'H0：沒有差異', 20, MUTED, 600, 'middle'),
      text(round(px(MU1)) + 40, 244, 'H1：真的有差異', 20, ACCENT, 600, 'middle'),
      text(832, 460, '檢定力 1 − β = 0.80', 20, ACCENT, 600, 'middle'))
bx, ax = 652, 740
f.add(path(f'M{bx},488 V552 Q{bx},560 {bx-8},560 H604', color=MUTED, marker=None, sw=1.2),
      text(596, 566, '型二錯誤 β = 0.20', 20, INK, 600, 'end'), text(596, 594, '有效果，卻沒偵測到', 16, MUTED, 400, 'end'),
      path(f'M{ax},508 V552 Q{ax},560 {ax+8},560 H788', color=ORANGE, marker=None, sw=1.2),
      text(796, 566, '型一錯誤 α = 0.05', 20, ORANGE, 600), text(796, 594, '沒效果，卻判定有效', 16, MUTED))
f.add(f'<line x1="40" y1="628" x2="1240" y2="628" stroke="{RULE}"/>',
      text(40, 664, '兩者像蹺蹺板：門檻往右移（α 調嚴），β 就變大。想兩個都壓低，只能增加樣本。', 16, MUTED))
f.save()

# B4 omp-remote/06: left-to-right control path; push returns on its own corridor.
f = Figure('omp-remote/06-final-architecture', 'OMP 遠端 Coding Agent 最終架構',
           '遠端裝置經 Relay 控制筆電上的 Host；Host 呼叫模型，做完再推播到手機。', 664,
           '其他電腦與手機透過 Collab Relay 控制私人筆電上的 OMP Host，Host 呼叫 AI Providers，完成後經通知服務推播回手機。')
f.add(rect(568, 136, 304, 376, 'rgba(201,205,214,0.02)', RULE, 8, '6,5'), rect(584, 128, 104, 20, PAPER, PAPER, 2),
      text(636, 144, '私人筆電', 16, SOFT, 400, 'middle'))
f.add(path('M248,220 H272 Q280,220 280,228 V288 Q280,296 288,296 H312'),
      path('M248,412 H272 Q280,412 280,404 V328 Q280,320 288,320 H312'),
      arrow(504, 308, 588, 308), arrow(852, 232, 968, 232), arrow(852, 428, 968, 428),
      path('M1104,472 V544 Q1104,552 1096,552 H152 Q144,552 144,544 V456', color=ORANGE, dashed=True, marker='arrow-orange'),
      label(912, 428, 'agent_end'), label(420, 552, '完成推播', color=ORANGE))
f.add(node(40, 176, 208, 88, '其他電腦', ['Chrome / Edge']), node(40, 368, 208, 88, '手機', ['Safari / Chrome']),
      node(312, 264, 192, 88, 'Collab Relay', ['遠端控制通道']),
      rect(588, 168, 264, 328, FOCAL, ACCENT), text(608, 208, 'OMP Host', 24, ACCENT, 600))
for i, t in enumerate(['Git / Docker', 'Database', 'Python / Node', 'Project Files']):
    f.add(rect(612, 232 + i * 60, 216, 48, 'rgba(201,205,214,0.05)', SOFT, 6), text(720, 262 + i * 60, t, 16, INK, 400, 'middle'))
f.add(node(968, 176, 272, 112, 'AI Providers', ['Claude / OpenAI', 'Gemini / OpenRouter / Custom']),
      node(968, 384, 272, 88, '通知', ['ntfy / Telegram']))
f.add(f'<line x1="40" y1="600" x2="1240" y2="600" stroke="{RULE}"/>',
      f'<line x1="40" y1="632" x2="88" y2="632" stroke="{MUTED}" stroke-width="1.6"/>', text(100, 638, '指令與呼叫', 16, MUTED),
      f'<line x1="272" y1="632" x2="320" y2="632" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="6,5"/>', text(332, 638, '完成通知', 16, MUTED))
f.save()

# B5 serenity-research/02: a real tree — every failed gate now has its own exit.
f = Figure('serenity-research/serenity-02-decision-tree', '技術題材投資決策樹',
           '四道關卡依序過；任一關沒過，就分到對應的名單。', 984,
           '技術、客戶、營收、股價四道關卡依序判斷，全過為潛在機會，各關未過分別進入排除、觀察、等待時程、等回調名單。')
gates = [('① 技術是真的嗎？', '已量產或客戶測試中', '專利、規格、測試', '排除', '只有實驗室階段'),
         ('② 客戶買單嗎？', 'design win／量產單', '大客戶認證、生態系', '觀察名單', '只有 sample 或概念'),
         ('③ 營收會反映嗎？', '今明年放量、毛利高', '營收占比、毛利、產能', '等待時程確認', '三年後才放量，或持續燒錢'),
         ('④ 股價還沒反映？', '對照景氣位置', '估值、景氣位置', '等回調再評估', '已過熱，或只是故事股')]
for i, (q, sub, check, out, why) in enumerate(gates):
    cy = 232 + i * 168
    nxt = cy + 168 - 56 if i < 3 else 848
    f.add(arrow(560, cy + 56, 560, nxt), rect(568, cy + 64, 32, 24, PAPER, PAPER, 2), text(584, cy + 82, '是', 16, MUTED, 400, 'middle'),
          arrow(720, cy, 848, cy), label(784, cy, '否'))
    f.add(f'<polygon points="560,{cy-56} 720,{cy} 560,{cy+56} 400,{cy}" fill="{CARD}" stroke="{RULE}"/>',
          text(560, cy - 4, q, 20, INK, 600, 'middle'), text(560, cy + 24, sub, 16, MUTED, 400, 'middle'),
          text(368, cy - 4, '要查', 16, SOFT, 400, 'end'), text(368, cy + 24, check, 20, MUTED, 400, 'end'),
          node(848, cy - 44, 392, 88, out, [why]))
f.add(rect(400, 848, 320, 88, FOCAL, ACCENT, 44), text(560, 888, '潛在機會', 24, ACCENT, 600, 'middle'),
      text(560, 916, '四關全過：可深入研究、分批布局', 16, MUTED, 400, 'middle'))
f.save()

# B6 ML confusion matrix: conceptual, so drawn (not plotted); adds the two readings.
f = Figure('../../machine-learning/assets/confusion_matrix', '混淆矩陣：四種結果',
           '對角線是答對；另外兩格是兩種不同的錯。Precision 看欄，Recall 看列。', 768,
           '二元分類的混淆矩陣：TP、FN、FP、TN 四格，Recall 由實際為正的那一列計算，Precision 由預測為正的那一欄計算。')
cells = [(232, 200, 'TP', '真陽性：抓對了', 'focal'), (480, 200, 'FN', '偽陰性：漏抓', 'err'),
         (232, 384, 'FP', '偽陽性：誤報', 'err'), (480, 384, 'TN', '真陰性：正確排除', '')]
f.add(path('M728,208 H736 V368 H728', marker=None, sw=1.2), arrow(736, 288, 832, 288),
      path('M240,576 V584 H464 V576', marker=None, sw=1.2), path('M352,584 V656 Q352,664 360,664 H832'))
for x, y, k, zh, kind in cells:
    color = ACCENT if kind == 'focal' else ORANGE if kind == 'err' else INK
    f.add(rect(x, y, 240, 176, FOCAL if kind == 'focal' else CARD, ACCENT if kind == 'focal' else ORANGE if kind == 'err' else RULE,
               8, '6,5' if kind == 'err' else None),
          text(x + 120, y + 92, k, 40, color, 600, 'middle'), text(x + 120, y + 132, zh, 20, MUTED, 400, 'middle'))
f.add(text(352, 184, '預測：正', 20, MUTED, 600, 'middle'), text(600, 184, '預測：負', 20, MUTED, 600, 'middle'),
      text(216, 296, '實際：正', 20, MUTED, 600, 'end'), text(216, 480, '實際：負', 20, MUTED, 600, 'end'))
for y, t, formula, why in [(224, 'Recall 召回率', 'TP / (TP + FN)', '真的是正的裡面，抓到幾個（看上面那列）'),
                           (600, 'Precision 精確率', 'TP / (TP + FP)', '預測為正的裡面，真的有幾個（看左邊那欄）')]:
    f.add(rect(832, y, 408, 128), text(852, y + 40, t, 24, INK, 600), text(852, y + 76, formula, 20, ACCENT),
          text(852, y + 108, why, 16, MUTED))
f.save()

# B7 ai-agent-harness architecture: snake layout, regression loop on its own lane.
f = Figure('ai-agent-harness/ai-agent-harness-architecture', 'AI Agent Harness：評測閉環架構',
           '規格 → 測試 → 執行 → 觀測 → 評分 → 把關 → 回饋；回饋會變成新的回歸測試。', 616,
           '任務規格、測試案例庫、Agent Runner、Trace、評分器、報告與 Gate、回饋迭代七步，回饋再寫回測試案例庫形成回歸閉環。')
row1 = [('任務規格', ['目標、限制、工具權限', '成功與失敗條件']), ('測試案例庫', ['golden · regression', 'adversarial · shadow']),
        ('Agent Runner', ['固定模型、prompt、tools', '沙盒、成本與時間上限']), ('Trace 觀測', ['tool calls · 狀態變更', '輸入輸出 · 錯誤'])]
for i in range(3):
    f.add(arrow(304 + i * 312, 232, 352 + i * 312, 232))
f.add(arrow(1108, 296, 1108, 440), arrow(976, 504, 772, 504), arrow(508, 504, 304, 504),
      path('M172,440 V376 Q172,368 180,368 H476 Q484,368 484,360 V296', color=ACCENT, dashed=True, marker='arrow-accent'),
      label(328, 368, '回歸閉環', color=ACCENT))
for i, (t, ls) in enumerate(row1):
    f.add(node(40 + i * 312, 168, 264, 128, t, ls))
f.add(node(976, 440, 264, 128, '評分器', ['規則評分 · LLM judge', '人工抽審 · 安全檢查']),
      node(508, 440, 264, 128, '報告與 Gate', ['通過率 · 成本 · 延遲', '擋住退步 · 灰度上線'], focal=True),
      node(40, 440, 264, 128, '回饋迭代', ['改 prompt / tool / memory', '補新的 regression case']))
f.save()

# B8 ai-agent-harness scorecard: one-hue intensity scale instead of traffic lights.
f = Figure('ai-agent-harness/ai-agent-harness-scorecard', 'AI Agent Harness：評分維度矩陣',
           '不同任務類型，該重視的分數不一樣；顏色越深，越要優先測。', 800,
           '七種任務類型對六個評測維度的優先級矩陣，以高、中、低三級表示。')
cols = ['正確性', '可重現性', '工具使用', '安全性', '成本／延遲', '可解釋 Trace']
rows = [('單步問答', '高中低中中中'), ('工具調用', '高高高高中高'), ('RAG／知識查詢', '高中中中中高'), ('多步任務', '高中高高高高'),
        ('程式／資料任務', '高高高高高高'), ('安全／權限', '中高高高中高'), ('長期記憶', '中低中高中高')]
LEVEL = {'高': ('rgba(124,192,255,0.28)', 'rgba(124,192,255,0.60)', INK, None),
         '中': ('rgba(124,192,255,0.08)', RULE, MUTED, None), '低': ('none', SOFT, SOFT, '4,4')}
for j, c in enumerate(cols):
    f.add(text(248 + j * 160 + 76, 184, c, 20, INK, 600, 'middle'))
for i, (name, vals) in enumerate(rows):
    y = 208 + i * 64
    f.add(text(224, y + 36, name, 20, MUTED, 400, 'end'))
    for j, v in enumerate(vals):
        fill, stroke, color, dash = LEVEL[v]
        f.add(rect(248 + j * 160, y, 152, 56, fill, stroke, 6, dash), text(248 + j * 160 + 76, y + 36, v, 20, color, 600, 'middle'))
f.add(f'<line x1="40" y1="688" x2="1240" y2="688" stroke="{RULE}"/>')
for k, (v, t) in enumerate([('高', '必測，可當 gate'), ('中', '抽樣、看趨勢'), ('低', '需要時再補測')]):
    fill, stroke, color, dash = LEVEL[v]
    x = 40 + k * 280
    f.add(rect(x, 708, 40, 24, fill, stroke, 4, dash), text(x + 20, 726, v, 16, color, 600, 'middle'), text(x + 52, 726, t, 16, MUTED))
f.add(text(40, 772, '改 prompt / model / tool / memory / 權限時，都要重跑 regression，並和 baseline 比較。', 16, MUTED))
f.save()

# Render: subset font to used glyphs, embed, write SVG, screenshot PNG.
used = ''.join(sorted(set(re.sub('<[^>]+>', '', ''.join(''.join(f.parts) + f.title + f.desc for f in FIGURES)))))
font = TTFont(sys.argv[1]); opts = subset.Options(); opts.flavor = 'woff'
sub = subset.Subsetter(options=opts); sub.populate(text=used); sub.subset(font); font.flavor = 'woff'
buf = io.BytesIO(); font.save(buf)
cmap = TTFont(io.BytesIO(buf.getvalue())).getBestCmap()
missing = sorted({c for c in used if not c.isspace() and ord(c) not in cmap})
assert not missing, ('glyphs missing from font', ''.join(missing))
fontcss = ("@font-face{font-family:'Noto Sans CJK TC';src:url(data:font/woff;base64," + base64.b64encode(buf.getvalue()).decode()
           + ") format('woff');font-weight:100 900}text{font-family:'Noto Sans CJK TC',sans-serif}")
markers = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="{c}"/></marker>'
                  for i, c in [('arrow', MUTED), ('arrow-accent', ACCENT), ('arrow-orange', ORANGE)])
with sync_playwright() as p:
    browser = p.chromium.launch()
    for f in FIGURES:
        slug = Path(f.out).name
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{f.h}" viewBox="0 0 {W} {f.h}" role="img" '
               f'aria-labelledby="{slug}-title {slug}-desc"><title id="{slug}-title">{escape(f.title)}</title>'
               f'<desc id="{slug}-desc">{escape(f.desc)}</desc><defs><style>{fontcss}</style>{markers}</defs>' + ''.join(f.parts) + '</svg>')
        out = (ROOT / f.out).resolve()
        svgpath = out.with_suffix('.svg')
        svgpath.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
        page = browser.new_page(viewport={'width': W, 'height': f.h}, device_scale_factor=2)
        page.set_content('<!DOCTYPE html><html><body style="margin:0;background:' + PAPER + '">' + svg + '</body></html>')
        page.evaluate("document.fonts.load('20px \"Noto Sans CJK TC\"')")
        assert page.evaluate("document.fonts.check('20px \"Noto Sans CJK TC\"')")
        bad = page.locator('svg').evaluate('''svg=>Array.from(svg.querySelectorAll('text')).map(e=>({t:e.textContent,b:e.getBBox()}))
            .filter(o=>o.b.x<0||o.b.y<0||o.b.x+o.b.width>svg.viewBox.baseVal.width||o.b.y+o.b.height>svg.viewBox.baseVal.height).map(o=>o.t)''')
        assert not bad, (slug, 'text outside canvas', bad)
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
# The confusion matrix lives beside non-diagram ML figures; it ships as PNG only.
(ROOT / '../../machine-learning/assets/confusion_matrix.svg').resolve().unlink()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas.')
