#!/usr/bin/env python3
"""Redraw the backend, DA-to-DE, and MCMC diagrams with the kb-night profile.

Embed a subset of Noto Sans CJK TC in the SVGs and render the PNGs at 2x with
Chromium. Requires fonttools, playwright, and its Chromium browser.
Run from any cwd, passing the full font path as argv[1], for example:
  python redraw_batch_a_20261125.py /mnt/c/Windows/Fonts/NotoSansTC-VF.ttf
"""
from pathlib import Path
from html import escape, unescape
import base64, io, re, sys
from fontTools.ttLib import TTFont
from fontTools import subset
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
DOCS = ROOT.parent.parent
PAPER = '#111729'; CARD = '#182038'; INK = '#C9CDD6'; MUTED = '#9AA0AD'; SOFT = '#6C7BA0'
RULE = '#2E3D66'; ACCENT = '#7CC0FF'; ORANGE = '#F0A868'
FOCAL = 'rgba(124,192,255,0.10)'; WARN = 'rgba(240,168,104,0.08)'; W = 1280
FIGURES = []


# Diagram primitives and typography follow leo-satellite/redraw_leo_20261125.py.
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


def node(x, y, w, h, title, lines=(), fill=CARD, stroke=RULE, tcolor=INK, dash=None, tsize=24, lsize=16):
    s = rect(x, y, w, h, fill, stroke, dash=dash) + text(x + 20, y + 40, title, tsize, tcolor, 600)
    for i, l in enumerate(lines):
        s += text(x + 20, y + 76 + i * 28, l, lsize, MUTED)
    return s


def legend(y, items):
    """Bottom strip: hairline, LEGEND eyebrow, swatch + label every 200px."""
    s = f'<line x1="40" y1="{y}" x2="1240" y2="{y}" stroke="{RULE}"/>' + text(40, y + 36, 'LEGEND', 12, SOFT, 600)
    for i, (fill, stroke, dash, t) in enumerate(items):
        x = 160 + i * 200
        s += rect(x, y + 20, 24, 20, fill, stroke, 4, dash) + text(x + 36, y + 36, t, 16, MUTED)
    return s


class Figure:
    def __init__(self, out, title, subtitle, h, desc):
        self.out = out; self.title = title; self.h = h; self.desc = desc
        self.parts = [rect(0, 0, W, h, PAPER, PAPER, 0), text(40, 64, title, 32, INK, 600), text(40, 104, subtitle, 20, MUTED)]

    def add(self, *s):
        self.parts.extend(s)

    def save(self):
        FIGURES.append(self)


def edge_label(x, y, w, label):
    """Opaque mask placed 8px away from the connector."""
    return rect(x, y, w, 32, PAPER, 'none', 4) + text(x + w // 2, y + 20, label, 16, INK, 400, 'middle')


def line_key(x, y, label, **kw):
    return arrow(x, y + 32, x + 40, y + 32, **kw) + text(x + 52, y + 36, label, 16, MUTED)


def section_label(x, y, label):
    return text(x, y, label, 16, MUTED, 600)


def decision(cx, cy, half_width, half_height, label, focal=False, detail=''):
    fill, stroke, color = (FOCAL, ACCENT, ACCENT) if focal else (CARD, RULE, INK)
    shape = (f'<polygon points="{cx},{cy - half_height} {cx + half_width},{cy} '
             f'{cx},{cy + half_height} {cx - half_width},{cy}" fill="{fill}" stroke="{stroke}"/>')
    label_y = cy if detail else cy + 8
    return (shape + text(cx, label_y, label, 20, color, 600, 'middle')
            + (text(cx, cy + 24, detail, 16, MUTED, 400, 'middle') if detail else ''))


def terminal(x, y, w, h, label, detail='', focal=False):
    fill, stroke, color = (FOCAL, ACCENT, ACCENT) if focal else (CARD, RULE, INK)
    cx, cy = x + w // 2, y + h // 2
    label_y = cy if detail else cy + 8
    return (rect(x, y, w, h, fill, stroke, 20) + text(cx, label_y, label, 20, color, 600, 'middle')
            + (text(cx, cy + 24, detail, 16, MUTED, 400, 'middle') if detail else ''))


# Deployment: compare the host address with the address inside Compose.
f = Figure('backend-series/docker-compose', '本機連 app，app 用服務名稱找資料庫',
           'Compose 自動建立容器網路。', 476,
           '本機的 curl 或瀏覽器用 127.0.0.1:8000 呼叫 app。'
           '在 Compose 網路內，app 用 postgres:5432 連資料庫。資料留在 pgdata 資料卷。')
f.add(rect(40, 148, 1200, 300, 'none'),
      rect(56, 132, 100, 32, PAPER, 'none', 4), section_label(68, 152, '你的電腦'),
      rect(432, 192, 776, 148, 'none', SOFT, dash='8,4'),
      rect(448, 176, 184, 32, PAPER, 'none', 4), section_label(460, 196, 'Compose 容器網路'))
f.add(arrow(272, 280, 456, 280),
      arrow(680, 280, 924, 280, color=ACCENT, marker='arrow-accent'),
      arrow(1048, 324, 1048, 360))
f.add(edge_label(284, 240, 136, '127.0.0.1:8000'),
      edge_label(728, 240, 148, 'postgres:5432'))
f.add(node(72, 236, 200, 88, '發出請求', ['curl 或瀏覽器']),
      node(456, 236, 224, 88, '應用程式', ['app 容器']),
      node(924, 236, 248, 88, '資料庫', ['postgres 容器']),
      node(924, 360, 248, 76, '資料卷 pgdata', tsize=20),
      text(944, 420, '保存資料庫檔案', 16, MUTED))
f.save()


# Flowchart: each of the four checks has its own early exit.
f = Figure('backend-series/fastapi-request-flow', 'FastAPI 在哪一步失敗，就在哪一步回錯',
           '以需要 API 金鑰的請求為例。', 784,
           'FastAPI 先按 HTTP 方法與路徑找路由，再檢查 API 金鑰、驗證輸入、執行業務規則。'
           '失敗就停在當步，分別回 404、401、422、404 或 409；通過則回傳 JSON，狀態碼 200 或 201。')
checks = [
    ('找得到路由？', '按 HTTP 方法與路徑找', '有', '無', '404 找不到路由', ''),
    ('金鑰正確？', '', '正確', '缺少或錯誤', '401 金鑰缺少或不符', ''),
    ('輸入合格？', '', '合格', '不合格', '422 欄位或型別不符', ''),
    ('通過業務規則？', '服務層處理', '通過', '未通過', '404 資料不存在', '409 資料重複'),
]
ys = range(196, 581, 128)
for y, (_, _, onward, failure, _, _) in zip(ys, checks):
    f.add(arrow(324, y + 48, 324, y + 80),
          arrow(576, y, 848, y, dashed=True),
          edge_label(332, y + 48, 64, onward),
          edge_label(652, y - 40, 120, failure))
for y, (label, detail, _, _, error, other_error) in zip(ys, checks):
    f.add(decision(324, y, 252, 48, label, focal=y == 324, detail=detail),
          terminal(848, y - 40, 360, 80, error, other_error))
f.add(terminal(72, 660, 504, 88, '回傳結果', 'JSON 格式，200／201'))
f.save()


# Architecture: move content across three stores, then compare pairs on separate rails.
f = Figure('backend-series/git-three-areas', 'Git 的 diff 指令取決於你要比較哪兩區',
           '箭頭表示移動內容，圓點標出比較的兩區。', 524,
           'git add 把工作目錄的內容放進暫存區，git commit 把暫存區存成新提交。'
           'git diff 比工作目錄與暫存區，git diff --staged 比暫存區與 HEAD，git diff HEAD 比工作目錄與 HEAD。')
f.add(arrow(492, 188, 612, 188), arrow(836, 188, 956, 188),
      edge_label(512, 148, 80, 'git add'), edge_label(848, 148, 96, 'git commit'))
f.add(node(268, 136, 224, 104, '工作目錄', ['正在修改的檔案']),
      node(612, 136, 224, 104, '暫存區', ['下次要提交的內容'], FOCAL, ACCENT, ACCENT),
      node(956, 136, 224, 104, '目前提交', ['HEAD 指向的版本']))
f.add(section_label(40, 280, '比較指令'))
comparisons = [
    (332, 'git diff', 380, 724),
    (400, 'git diff --staged', 724, 1068),
    (468, 'git diff HEAD', 380, 1068),
]
for x in (380, 724, 1068):
    end = 432 if x == 724 else 492
    f.add(path(f'M{x},240 V{end}', SOFT, dashed=True, marker=None, sw=0.8))
for y, command, left, right in comparisons:
    f.add(f'<line x1="40" y1="{y - 32}" x2="1196" y2="{y - 32}" stroke="{RULE}"/>',
          text(40, y + 8, command, 20, INK, 600),
          arrow(left, y, right, y, marker=None, sw=2),
          f'<circle cx="{left}" cy="{y}" r="8" fill="{MUTED}"/>',
          f'<circle cx="{right}" cy="{y}" r="8" fill="{MUTED}"/>')
f.save()


# Architecture: distinguish request handling from the path that saves the analysis.
f = Figure('backend-series/overview', '後端把履歷與職缺的比對結果存成快照',
           '以建立申請紀錄為例。', 548,
           '用戶端帶 Bearer API key，經 Render 的 HTTPS 代理進入 FastAPI，由服務層處理請求，'
           '透過資料存取層與 PostgreSQL 讀寫。服務層呼叫技能比對，將分數與技能差異存為 JSONB 分析快照。')
f.add(rect(232, 140, 1024, 368, 'none', SOFT, dash='8,4'),
      rect(248, 124, 152, 32, PAPER, 'none', 4), section_label(260, 144, 'Render 託管範圍'))
main = [
    ('用戶端', ['Bearer API key', '存取憑證']),
    ('Render 代理', ['接收 HTTPS']),
    ('FastAPI', ['找路由、驗輸入', 'Pydantic']),
    ('服務層', ['處理業務規則', 'AssistantService']),
    ('存取資料', ['SQLAlchemy']),
    ('PostgreSQL', ['資料庫']),
]
xs = range(40, 1061, 204)
for x in xs[:-1]:
    f.add(arrow(x + 180, 232, x + 204, 232))
f.add(arrow(740, 292, 740, 368), arrow(832, 420, 1060, 420), arrow(1148, 368, 1148, 292),
      edge_label(748, 312, 56, '呼叫'),
      edge_label(872, 380, 148, '分數與技能差異'),
      edge_label(1156, 312, 56, '存入'))
for x, (title, details) in zip(xs, main):
    f.add(node(x, 172, 180, 120, title, details, tsize=20))
f.add(node(652, 368, 180, 112, '比對技能', ['履歷與職缺'], tsize=20),
      node(1060, 368, 180, 112, '分析快照', ['JSONB 格式', '保存當次結果'],
           FOCAL, ACCENT, ACCENT, tsize=20))
f.save()


def entity(x, y, w, title, fields, focal=False):
    fill, stroke, title_color = (FOCAL, ACCENT, ACCENT) if focal else (CARD, RULE, INK)
    return (rect(x, y, w, 80 + 24 * len(fields), fill, stroke)
            + text(x + 20, y + 36, title, 24, title_color, 600)
            + f'<line x1="{x}" y1="{y + 52}" x2="{x + w}" y2="{y + 52}" stroke="{RULE}"/>'
            + ''.join(text(x + 20, y + 80 + 24 * i, field, 16, MUTED) for i, field in enumerate(fields)))



# ER: keep cardinalities and deletion rules; the article has the column definitions.
f = Figure('backend-series/postgres-er', '申請紀錄把履歷和職缺連起來',
           '1 是一筆，N 是多筆。', 752,
           '一位使用者可有多份履歷、職缺與申請紀錄。每筆申請連到一份履歷和一個職缺，'
           '所以履歷與職缺可以多對多。經歷隨履歷刪除，其餘關係有相依資料就禁止刪除。')
f.add(path('M464,196 H212 Q204,196 204,204 V344', marker=None),
      path('M816,196 H1068 Q1076,196 1076,204 V344', marker=None),
      arrow(640, 248, 640, 344, marker=None),
      arrow(368, 400, 464, 400, marker=None), arrow(816, 400, 912, 400, marker=None),
      arrow(204, 448, 204, 564, dashed=True, marker=None))
for x, y, cardinality in [
    (428, 156, '1'), (828, 156, '1'), (212, 304, 'N'), (1084, 304, 'N'),
    (648, 248, '1'), (648, 304, 'N'), (380, 360, '1'), (428, 360, 'N'),
    (828, 360, 'N'), (876, 360, '1'), (212, 448, '1'), (212, 524, 'N'),
]:
    f.add(edge_label(x, y, 24, cardinality))
f.add(edge_label(212, 488, 172, '隨履歷一起刪除'))
f.add(entity(464, 144, 352, '使用者', ['users']),
      entity(40, 344, 328, '履歷', ['resumes']),
      entity(912, 344, 328, '職缺', ['job_descriptions']),
      entity(464, 344, 352, '申請紀錄', ['applications', '狀態、比對分數', 'JSONB 分析快照'], focal=True),
      entity(40, 564, 328, '工作經歷', ['resume_experiences']))
f.add(f'<line x1="40" y1="688" x2="1240" y2="688" stroke="{RULE}"/>',
      line_key(40, 688, '有相依資料就不能刪（RESTRICT）', marker=None),
      line_key(480, 688, '隨履歷一起刪（CASCADE）', dashed=True, marker=None))
f.save()


# Flowchart: three decision gates route failures away from the traffic switch.
f = Figure('backend-series/render-deploy-flow', 'Render 等新版全數過關才切換流量',
           '改表風險最高，舊版仍要能用。', 468,
           'git push 後，Render 建置 Docker 映像、在部署前更新資料庫、啟動新容器並用 GET /ready 檢查。'
           '三個關卡都通過才切到新版；失敗時舊版繼續服務。改資料表期間舊版仍在服務，變更要與舊版相容。')
for x in range(140, 941, 200):
    f.add(arrow(x + 80, 228, x + 120, 228))
for x in (340, 540, 940):
    f.add(arrow(x, 292, x, 364, dashed=True),
          edge_label(x + 8, 308, 48, '失敗'),
          edge_label(x + 80, 188, 40, '通過'))
f.add(terminal(60, 184, 160, 88, '推上 GitHub', 'git push'),
      decision(340, 228, 80, 64, '建置成功？', detail='打包成映像'),
      decision(540, 228, 80, 64, '改表成功？', focal=True, detail='更新資料表'),
      node(660, 184, 160, 88, '啟動新容器', tsize=20),
      decision(940, 228, 80, 64, '就緒了嗎？', detail='GET /ready'),
      terminal(1060, 184, 160, 88, '新版接流量'),
      terminal(236, 364, 808, 76, '新版不上線，舊版繼續服務'))
f.save()


def roadmap_step(x, y, w, h, lines):
    """Center the original metaphors and their technical sublabels."""
    first = y + h // 8 * 4 + 8 - 12 * (len(lines) - 1)
    return rect(x, y, w, h) + ''.join(
        text(x + w // 2, first + 24 * i, line, 16, MUTED if line.startswith('(') else INK,
             400 if line.startswith('(') else 600, 'middle')
        for i, line in enumerate(lines)
    )



# Flowchart: four milestones lead to a three-way choice driven by actual needs.
f = Figure('da-to-de-roadmap/roadmap', '先做出資料管線，遇到瓶頸再學進階工具',
           '從資料分析師走向資料工程師。', 904,
           '先補基礎工具、學建模、做第一條資料管線，再上雲並加入自動檢查。'
           '資料量太大時學 Spark，需要即時處理時學 Kafka，這兩條路接到 Lakehouse。'
           '目前都不需要時，先加強現有管線的建模與品質，直接準備作品集與面試。')
stages = [
    ('0  補基礎工具', ['SQL 查資料、Python 接流程', '用終端機、Git 存檔可回復']),
    ('1  學資料建模', ['決定每筆資料怎麼記']),
    ('2  做第一條資料管線', ['先存原始資料，再整理']),
    ('3  上雲並自動檢查', ['Docker 封裝、雲端倉儲']),
]
xs = range(40, 977, 312)
for x in xs[:-1]:
    f.add(arrow(x + 264, 188, x + 312, 188))
f.add(path('M1108,240 V268 Q1108,276 1100,276 H648 Q640,276 640,284 V324'))
f.add(path('M400,380 H224 Q216,380 216,388 V496'),
      arrow(640, 436, 640, 496),
      path('M880,380 H1052 Q1060,380 1060,388 V832 Q1060,840 1052,840 H912'))
f.add(path('M216,592 V616 Q216,624 224,624 H536 Q544,624 544,632 V656'),
      arrow(640, 592, 640, 656), arrow(640, 752, 640, 800))
f.add(edge_label(224, 416, 116, '資料量太大'),
      edge_label(648, 448, 104, '需要即時'),
      edge_label(1068, 416, 140, '目前都不需要'),
      edge_label(1068, 444, 172, '先加強建模與品質'))
for x, (title, details) in zip(xs, stages):
    f.add(node(x, 128, 264, 112, title, details, tsize=20))
f.add(decision(640, 380, 240, 56, '4  資料量太大，或需要即時？', focal=True),
      node(40, 496, 352, 96, 'Spark', ['分工處理大量資料'], tsize=20),
      node(464, 496, 352, 96, 'Kafka', ['即時處理接連進來的資料'], tsize=20),
      node(456, 656, 368, 96, 'Lakehouse / Iceberg', ['集中存放與管理資料'], tsize=20),
      terminal(368, 800, 544, 80, '整理作品集，準備面試'))
f.save()


# Flowchart: initialize once, then return to the proposal until the run is complete.
f = Figure('mcmc-portfolio/mcmc-iteration-flow', 'MCMC 每輪留下樣本，跑滿設定次數才輸出',
           'Metropolis-Hastings（MH）取樣。n_iter 是設定輪數。', 784,
           '初始化使用者參數與族群超參數。每輪提出新值、計算接受比值並用 Metropolis-Hastings 決定是否換值，'
           '再更新族群設定、做預測並保存後驗樣本。未達 n_iter 就回到提議，跑完才輸出參數分布和收斂診斷。')
f.add(arrow(324, 212, 432, 212), arrow(760, 212, 884, 212), arrow(1060, 280, 1060, 388),
      arrow(884, 456, 760, 456), arrow(432, 456, 324, 456), arrow(184, 520, 184, 620),
      arrow(324, 688, 432, 688), arrow(760, 688, 884, 688),
      path('M596,632 V580 Q596,572 588,572 H384 Q376,572 376,564 V464 '
           'a8,8 0 0,1 0,-16 V332 Q376,324 384,324 H588 Q596,324 596,316 V280', dashed=True))
f.add(edge_label(384, 528, 100, '還沒跑完'), edge_label(792, 648, 60, '跑完'))
f.add(node(44, 148, 280, 132, '設定起始值', ['個人 a_u · s_u · C_switch', '族群 θ · Σ · σ'], tsize=20),
      node(432, 148, 328, 132, '試一組新參數', ['從使用者目前值隨機試新值'], tsize=20),
      node(884, 148, 352, 132, '算接受比值', ['資料與事前假設的比值', '修正提議機率'], tsize=20),
      node(884, 388, 352, 132, '抽籤決定是否換值', ['MH 機率 α = min(1, r)', '接受就換，拒絕就留'],
           FOCAL, ACCENT, ACCENT, tsize=20),
      node(432, 388, 328, 132, '更新族群設定', ['θ_a · Σ_a', 'θ_switch · σ_switch'], tsize=20),
      node(44, 388, 280, 132, '預測下一個類別', ['計算訓練準確率'], tsize=20),
      node(44, 620, 280, 132, '留存後驗樣本', ['看到資料後的參數樣本', '接受率、取樣軌跡'], tsize=20),
      decision(596, 688, 164, 56, '已跑完 n_iter 次？'),
      terminal(884, 632, 352, 112, '輸出參數分布', '收斂診斷、接受率與軌跡'))
f.save()

# Render: subset font to used glyphs, embed, write SVG, screenshot PNG.
visible = unescape(re.sub('<[^>]+>', '', ''.join(part for f in FIGURES for part in f.parts)))
accessible = ''.join(f.title + f.desc for f in FIGURES)
used = ''.join(sorted(set(visible + accessible)))
# Keep the source font timestamp so a clean rerun writes identical SVGs.
font = TTFont(sys.argv[1], recalcTimestamp=False); opts = subset.Options(); opts.flavor = 'woff'
sub = subset.Subsetter(options=opts); sub.populate(text=used); sub.subset(font); font.flavor = 'woff'
buf = io.BytesIO(); font.save(buf)
cmap = TTFont(io.BytesIO(buf.getvalue())).getBestCmap()
missing = sorted({c for c in used if not c.isspace() and ord(c) not in cmap})
assert not missing, ('glyphs missing from font', ''.join(missing))
fontcss = ("@font-face{font-family:'Noto Sans CJK TC';src:url(data:font/woff;base64," + base64.b64encode(buf.getvalue()).decode()
           + ") format('woff');font-weight:100 900}text{font-family:'Noto Sans CJK TC',sans-serif}")
markers = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="{c}"/></marker>'
                  for i, c in [('arrow', MUTED), ('arrow-accent', ACCENT)])
with sync_playwright() as p:
    browser = p.chromium.launch()
    for f in FIGURES:
        slug = f.out.replace('/', '-')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{f.h}" viewBox="0 0 {W} {f.h}" role="img" '
               f'aria-labelledby="{slug}-title {slug}-desc"><title id="{slug}-title">{escape(f.title)}</title>'
               f'<desc id="{slug}-desc">{escape(f.desc)}</desc><defs><style>{fontcss}</style>{markers}</defs>' + ''.join(f.parts) + '</svg>')
        out = ROOT / f.out
        out.with_suffix('.svg').write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg, encoding='utf-8')
        page = browser.new_page(viewport={'width': W, 'height': f.h}, device_scale_factor=2)
        page.set_content('<!DOCTYPE html><html><body style="margin:0;background:' + PAPER + '">' + svg + '</body></html>')
        page.evaluate("document.fonts.load('20px \"Noto Sans CJK TC\"')")
        assert page.evaluate("document.fonts.check('20px \"Noto Sans CJK TC\"')")
        # Text must stay inside the canvas and inside the card it starts in.
        bad = page.locator('svg').evaluate('''svg=>{const R=[...svg.querySelectorAll('rect')].slice(1).map(r=>r.getBBox());
            return [...svg.querySelectorAll('text')].filter(e=>{
              const b=e.getBBox(), x=e.x.baseVal.getItem(0).value, y=e.y.baseVal.getItem(0).value;
              if(b.x<0||b.y<0||b.x+b.width>svg.viewBox.baseVal.width||b.y+b.height>svg.viewBox.baseVal.height) return true;
              const c=R.findLast(r=>x>=r.x&&x<r.x+r.width&&y>=r.y&&y<r.y+r.height);
              return c&&(b.x<c.x||b.y<c.y||b.x+b.width>c.x+c.width||b.y+b.height>c.y+c.height);
            }).map(e=>e.textContent)}''')
        assert not bad, (f.out, 'text overflows canvas or card', bad)
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas and cards.')
