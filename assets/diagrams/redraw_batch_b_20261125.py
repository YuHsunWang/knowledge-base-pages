#!/usr/bin/env python3
"""Redraw nine CVS Radar and OMP Remote figures using Diagram Design kb-night.

Embed subset Noto Sans CJK TC in the SVG and render PNG at 2x with Chromium.
Run from any cwd. Pass the full NotoSansTC-VF.ttf path as argv[1].
Requires fonttools and playwright with Chromium installed.
"""
from pathlib import Path
from html import escape
import base64, io, re, sys
from fontTools.ttLib import TTFont
from fontTools import subset
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent            # docs/assets/diagrams
DOCS = ROOT.parent.parent
PAPER = '#111729'; CARD = '#182038'; INK = '#C9CDD6'; MUTED = '#9AA0AD'; SOFT = '#6C7BA0'
RULE = '#2E3D66'; ACCENT = '#7CC0FF'; ORANGE = '#F0A868'
FOCAL = 'rgba(124,192,255,0.10)'; WARN = 'rgba(240,168,104,0.08)'; W = 1280
FIGURES = []


# Drawing helpers and render contract from leo-satellite/redraw_leo_20261125.py.
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



# Rounded side-to-side routing for fan-outs. The caller supplies separate ports.
def elbow(x1, y1, bend_x, x2, y2):
    dx = 8 if x2 > x1 else -8
    dy = 8 if y2 > y1 else -8
    assert (bend_x - x1) * dx >= 64 and (x2 - bend_x) * dx >= 64
    assert abs(y2 - y1) >= 16
    return path(f'M{x1},{y1} H{bend_x - dx} Q{bend_x},{y1} {bend_x},{y1 + dy} '
                f'V{y2 - dy} Q{bend_x},{y2} {bend_x + dx},{y2} H{x2}')


def arrow_label(cx, y, width, label):
    return (rect(cx - width // 2, y - 36, width, 28, PAPER, 'none', 4)
            + text(cx, y - 16, label, 16, MUTED, anchor='middle'))


def heading(x, y, label):
    return text(x, y, label, 16, MUTED, 600)


# CVS 01: the file handoff separates local work from the public website.
f = Figure('cvs-radar/01-architecture', '商品評價先算好，網站只讀結果',
           '從 PTT 公開討論到貨架前的查詢畫面', 400,
           '本機每天抓取 PTT CVS 板的新心得和留言，交給 AI 辨認商品與情緒，再重算評分並輸出去識別化的商品資料。推送到 main 後部署，瀏覽器只讀預先建好的 JSON 資料。')
f.add(rect(40, 144, 924, 216, PAPER, RULE, dash='6,4'),
      text(60, 184, '本機每天自動更新', 24, INK, 600),
      heading(1032, 184, '公開網站'))
stages = [
    (60, 176, '抓取新心得', ['PTT CVS 板']),
    (280, 176, 'AI 讀討論', ['辨認商品與情緒']),
    (500, 176, '重算評分', []),
    (720, 224, '輸出資料檔', ['只留商品資料']),
]
for (x, width, *_), (next_x, *_) in zip(stages, stages[1:]):
    f.add(arrow(x + width, 272, next_x, 272))
f.add(arrow(944, 272, 1032, 272, color=ACCENT, marker='arrow-accent'),
      arrow_label(988, 272, 72, '資料檔'))
for x, width, title, details in stages:
    f.add(node(x, 212, width, 120, title, details))
f.add(node(1032, 212, 208, 120, '靜態網站',
           ['推送到 main 後部署', '瀏覽器只讀 JSON'], FOCAL, ACCENT, ACCENT))
f.save()


# CVS 02: calculation and the decision to show a score are distinct steps.
f = Figure('cvs-radar/02-scoring', '樣本少就拉回中間，太少就留白',
           '從 PTT 討論算出分數與信心度', 496,
           'AI 判斷作者心得和推噓留言的情緒並排除離題內容。作者和留言等權，每人每商品一票，可疑帳號的影響較小。貝氏收斂把少量評價的分數拉回中間。樣本足夠才顯示綜合評分與信心度，否則標示資料不足。')
f.add(arrow(248, 228, 280, 228), arrow(516, 228, 548, 228), arrow(788, 228, 820, 228),
      arrow(1004, 228, 1072, 228), arrow(912, 308, 912, 364),
      arrow_label(1036, 228, 48, '夠'),
      rect(920, 320, 56, 28, PAPER, 'none', 4), text(928, 340, '太少', 16, MUTED))
f.add(node(40, 156, 208, 144, '作者心得與推噓留言',
           ['AI 逐則判斷情緒', '排除離題留言'], tsize=20),
      node(280, 156, 236, 144, '作者和留言同樣重要',
           ['每人每商品一票', '降低可疑帳號影響'], tsize=20),
      node(548, 156, 240, 144, '貝氏收斂',
           ['樣本少，分數更靠近中間'], tsize=20),
      f'<path d="M912,148 L1004,228 L912,308 L820,228 Z" fill="{CARD}" stroke="{RULE}"/>',
      text(912, 236, '樣本夠多嗎？', 20, INK, 600, 'middle'),
      node(1072, 172, 168, 112, '顯示綜合評分', ['附信心度'], tsize=20),
      node(808, 364, 208, 92, '顯示資料不足', [], FOCAL, ACCENT, ACCENT, tsize=20))
f.save()


# CVS 03: a minimum activity check precedes the private use of the score.
f = Figure('cvs-radar/03-trust', '可疑分只降低留言對評分的影響',
           '帳號要有足夠留言，才從多個線索判斷', 540,
           '先檢查帳號有沒有至少 5 則留言。足夠時才看長期品牌偏好和灌票線索，包括同品牌短時間連發、留言雷同和常給極端評價。可疑分只用於內部降權，公開頁只列商品資料。')
f.add(arrow(228, 252, 272, 252), arrow(488, 252, 568, 252),
      arrow(896, 252, 984, 252), arrow(380, 340, 380, 396),
      arrow_label(528, 252, 56, '有'),
      rect(388, 352, 56, 28, PAPER, 'none', 4), text(396, 372, '不足', 16, MUTED))
f.add(node(40, 184, 188, 136, '逐則讀取留言', ['帳號、時間', '推噓與文字'], tsize=20),
      f'<path d="M380,164 L488,252 L380,340 L272,252 Z" fill="{CARD}" stroke="{RULE}"/>',
      text(380, 260, '至少 5 則留言？', 20, INK, 600, 'middle'),
      node(568, 152, 328, 200, '看長期品牌偏好與灌票線索',
           ['同品牌短時間連發', '內容像套同一個模板', '常給極端評價'], tsize=20, lsize=20),
      node(984, 180, 256, 144, '合成可疑分',
           ['只在內部計分使用', '公開頁只列商品資料'], FOCAL, ACCENT, ACCENT, lsize=20),
      node(252, 396, 256, 104, '略過帳號評分', ['資料少，難以判斷'], tsize=20))
f.save()


# CVS 04: each data field maps to a distinct signal on the shopper's screen.
f = Figure('cvs-radar/04-shopper-mapping', '買不買，分數和評價數一起看',
           '站在貨架前，用手機十秒看懂評價', 608,
           '越推薦的公平分數用越高的分數與對應顏色表示。正向評價比例以短長條呈現，評價則數讓樣本數可見。樣本太少時，看法一致或兩極的欄位顯示資料不足。')
f.add(rect(40, 144, 1200, 424, PAPER, RULE),
      heading(64, 180, '分析欄位'), heading(416, 180, '怎麼用'), heading(804, 180, '手機畫面'))
rows = [
    ('fair_score', '公平分數', '分數越高越推薦'),
    ('正／中／負分布', '算出正向比例', '長條取代無效徽章'),
    ('樣本數', '', '評價太少，先保留判斷'),
    ('consensus', '看法一致或兩極', '樣本太少時'),
]
for i, (field, explanation, reason) in enumerate(rows):
    y = 200 + i * 92
    f.add(path(f'M40,{y} H1240', RULE, marker=None),
          arrow(688, y + 48, 756, y + 48),
          text(64, y + (36 if explanation else 56), field, 24, INK, 600),
          text(416, y + 56, reason, 20))
    if explanation:
        f.add(text(64, y + 64, explanation, 16, MUTED))
# The preview uses the same example values and native UI swatches as before.
for x, color, score in [(804, '#15803d', '綠 89'), (944, '#b45309', '黃 55'), (1084, '#be123c', '紅 32')]:
    f.add(rect(x, 224, 120, 48, CARD, RULE, 4),
          rect(x + 16, 244, 12, 12, color, 'none', 4),
          text(x + 76, 256, score, 20, INK, 600, 'middle'))
positive_share = 72
bar_width = 200
f.add(text(804, 348, f'正向 {positive_share}%', 24, INK, 600),
      rect(1004, 332, bar_width, 16, CARD, RULE, 4),
      rect(1004, 332, bar_width * positive_share // 100, 16, ACCENT, 'none', 4),
      text(804, 440, 'N 則評價', 24, INK, 600),
      text(804, 532, '資料不足', 24, ACCENT, 600))
f.save()


# OMP 01: put the code and tools visibly inside their physical host.
f = Figure('omp-remote/01-overall-architecture', '用瀏覽器操作，程式碼和工具留在筆電',
           'Collab 把瀏覽器操作送到筆電上的工作階段', 660,
           '手機或其他電腦的瀏覽器使用 HTTPS 或 WebSocket 連到 OMP Collab，再由 Collab 轉給私人筆電上的 OMP。程式庫、Docker、資料庫、Python、Node.js 和檔案留在筆電，OMP 另外呼叫模型服務。')
f.add(rect(760, 144, 480, 296, PAPER, RULE, dash='6,4'),
      text(780, 180, '私人筆電', 24, INK, 600))
f.add(arrow(260, 288, 428, 288), arrow(648, 288, 792, 288),
      arrow(972, 288, 1008, 288), arrow(884, 352, 884, 496),
      arrow_label(344, 288, 152, 'HTTPS / WebSocket'),
      arrow_label(704, 288, 96, '轉送操作'),
      rect(892, 448, 104, 28, PAPER, 'none', 4), text(900, 468, '呼叫模型', 16, MUTED))
f.add(node(40, 228, 220, 124, '遠端瀏覽器', ['手機或其他電腦']),
      node(428, 228, 220, 124, 'OMP Collab', ['中繼站 my.omp.sh']),
      node(792, 228, 180, 124, 'OMP 主程式', ['在筆電上執行'], FOCAL, ACCENT, ACCENT),
      node(1008, 208, 208, 184, '本機程式碼與工具',
           ['Git 程式庫、檔案', 'Docker／資料庫', 'Python／Node.js'], tsize=20),
      node(760, 496, 456, 124, '外部模型服務',
           ['Anthropic／OpenAI／Gemini', 'OpenRouter／自訂 API']))
f.save()


# OMP 02: separate planning from execution before choosing a working role.
f = Figure('omp-remote/02-model-role-strategy', '先看要做什麼，再選模型角色',
           '按工作需求取捨速度、成本與推理能力', 640,
           '需要先列計畫時選 plan。直接做時，小修改或搜尋用 smol 快速省成本，日常寫程式用 default，架構或疑難除錯用 slow 深入推理。')
f.add(arrow(356, 336, 448, 336), arrow(224, 424, 224, 488), arrow(688, 336, 1008, 336),
      path('M568,248 V184 Q568,176 576,176 H1008'),
      path('M568,424 V484 Q568,492 576,492 H1008'),
      arrow_label(400, 336, 72, '直接做'),
      rect(232, 436, 40, 28, PAPER, 'none', 4), text(240, 456, '要', 16, MUTED),
      arrow_label(808, 176, 144, '小改動／搜尋'),
      arrow_label(848, 336, 120, '日常寫程式'),
      arrow_label(808, 492, 164, '架構／疑難除錯'))
f.add(f'<path d="M224,248 L356,336 L224,424 L92,336 Z" fill="{CARD}" stroke="{RULE}"/>',
      text(224, 344, '要先擬計畫嗎？', 24, INK, 600, 'middle'),
      f'<path d="M568,248 L688,336 L568,424 L448,336 Z" fill="{FOCAL}" stroke="{ACCENT}"/>',
      text(568, 344, '是哪種工作？', 24, INK, 600, 'middle'),
      node(80, 488, 288, 112, 'plan', ['先拆需求，列實作計畫']),
      node(1008, 120, 232, 112, 'smol', ['快速、低成本']),
      node(1008, 280, 232, 112, 'default', ['日常工作的主力模型']),
      node(1008, 436, 232, 112, 'slow', ['需要深入推理']))
f.save()


# OMP 03: one trace covers either browser without suggesting two requests.
f = Figure('omp-remote/03-collab-sequence', '筆電執行指令，結果陸續回到瀏覽器',
           '手機和其他電腦都透過 Collab 操作', 676,
           '手機或其他電腦的瀏覽器送出指令，Collab 將指令交給私人筆電上的 OMP。OMP 呼叫本機工具，取得結果後透過 Collab 持續回傳到遠端瀏覽器顯示。')
centers = [164, 480, 800, 1116]
for cx in centers:
    f.add(path(f'M{cx},268 V632', SOFT, dashed=True, marker=None))
f.add(rect(796, 376, 8, 168, RULE, MUTED, 0),
      rect(1112, 432, 8, 56, RULE, MUTED, 0))
messages = [
    (164, 480, 320, '送出指令', False, False),
    (480, 796, 376, '轉交指令', False, False),
    (804, 1112, 432, '呼叫工具', False, False),
    (1112, 804, 488, '交回執行結果', True, False),
    (796, 480, 544, '持續回傳結果', False, True),
    (480, 164, 600, '傳回瀏覽器顯示', True, False),
]
for source, target, y, label, reply, focal in messages:
    color, marker = (ACCENT, 'arrow-accent') if focal else (MUTED, 'arrow')
    f.add(arrow(source, y, target, y, color=color, marker=marker, dashed=reply),
          arrow_label((source + target) // 8 * 4, y, 128, label))
for cx, title, details in zip(centers,
                              ['遠端瀏覽器', 'OMP Collab', '私人筆電上的 OMP', '本機工具'],
                              [['手機或其他電腦'], ['中繼站'], [], ['Git／Bash', 'Docker／資料庫']]):
    f.add(node(cx - 124, 140, 248, 128, title, details, tsize=20))
f.save()


# OMP 04: show the trigger, the handoffs and the visible lock-screen result.
f = Figure('omp-remote/04-mobile-push', '手機鎖屏也能收到 OMP 通知',
           '外掛把 OMP 的工作狀態交給通知服務', 384,
           'OMP 結束工作時，外掛透過 HTTPS POST 將通知交給 ntfy，也可加上出錯通知。通知服務將訊息推送到 iPhone 或 Android 的鎖屏。')
stages = [
    (40, 236, 'OMP 發出事件', ['完成（agent_end）', '可加出錯通知（error）']),
    (360, 216, '外掛送出通知', ['OMP Extension', '用 HTTPS POST']),
    (680, 224, '通知服務轉送', ['ntfy']),
    (1024, 216, '手機鎖屏顯示', ['iPhone／Android']),
]
for i, ((x, width, *_), (next_x, *_)) in enumerate(zip(stages, stages[1:])):
    f.add(arrow(x + width, 248, next_x, 248, dashed=i == 0))
for x, width, title, details in stages:
    style = (FOCAL, ACCENT, ACCENT) if x == 1024 else (CARD, RULE, INK)
    f.add(node(x, 176, width, 144, title, details, *style))
f.save()


# OMP 05: containment shows co-location; aligned rows show one-to-one pairing.
f = Figure('omp-remote/05-multi-project', '每個專案各開一個 Collab 工作階段',
           '在手機或其他電腦上，連到要處理的專案', 604,
           '私人筆電在 project-api、project-web 和 data-pipeline 各跑一個 OMP，分別開出 Collab 工作階段 A、B 和 C。遠端瀏覽器可選擇任一工作階段。')
f.add(rect(40, 144, 420, 420, PAPER, RULE, dash='6,4'),
      text(72, 184, '私人筆電上的專案', 24, INK, 600),
      heading(564, 184, 'Collab 工作階段'),
      elbow(1048, 324, 928, 812, 248), arrow(1048, 372, 812, 372),
      elbow(1048, 420, 928, 812, 496))
for i in range(3):
    y = 200 + i * 124
    f.add(arrow(428, y + 48, 564, y + 48))
for i, (project, session) in enumerate([
    ('project-api', '工作階段 A'),
    ('project-web', '工作階段 B'),
    ('data-pipeline', '工作階段 C'),
]):
    y = 200 + i * 124
    f.add(node(72, y, 356, 96, project, ['各啟動一個 OMP']),
          node(564, y, 248, 96, session, []))
f.add(node(1048, 304, 192, 136, '遠端瀏覽器', ['手機或其他電腦', '選擇工作階段'],
           FOCAL, ACCENT, ACCENT))
f.save()


# Render: subset font to used glyphs, embed, write SVG, screenshot PNG.
used = ''.join(sorted(set(re.sub('<[^>]+>', '', ''.join(''.join(f.parts) + f.title + f.desc for f in FIGURES)))))
font = TTFont(sys.argv[1], recalcTimestamp=False); opts = subset.Options(); opts.flavor = 'woff'
sub = subset.Subsetter(options=opts); sub.populate(text=used); sub.subset(font); font.flavor = 'woff'
buf = io.BytesIO(); font.save(buf)
cmap = TTFont(io.BytesIO(buf.getvalue())).getBestCmap()
missing = sorted({c for c in used if not c.isspace() and ord(c) not in cmap})
assert not missing, ('glyphs missing from font', ''.join(missing))
fontcss = ("@font-face{font-family:'Noto Sans CJK TC';src:url(data:font/woff;base64," + base64.b64encode(buf.getvalue()).decode()
           + ") format('woff');font-weight:100 900}text{font-family:'Noto Sans CJK TC',sans-serif}")
markers = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="{c}"/></marker>'
                  for i, c in [('arrow', MUTED), ('arrow-accent', ACCENT), ('arrow-link', ORANGE)])
with sync_playwright() as p:
    browser = p.chromium.launch()
    for f in FIGURES:
        slug = f.out.replace('/', '-')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{f.h}" viewBox="0 0 {W} {f.h}" role="img" '
               f'aria-labelledby="{slug}-title {slug}-desc"><title id="{slug}-title">{escape(f.title)}</title>'
               f'<desc id="{slug}-desc">{escape(f.desc)}</desc><defs><style>{fontcss}</style>{markers}</defs>' + ''.join(f.parts) + '</svg>')
        out = ROOT / f.out
        out.with_suffix('.svg').write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
        page = browser.new_page(viewport={'width': W, 'height': f.h}, device_scale_factor=2)
        page.set_content('<!DOCTYPE html><html><body style="margin:0;background:' + PAPER + '">' + svg + '</body></html>')
        page.evaluate("document.fonts.load('20px \"Noto Sans CJK TC\"')")
        assert page.evaluate("document.fonts.check('20px \"Noto Sans CJK TC\"')")
        # Text must stay inside the canvas and inside the card it starts in.
        bad = page.locator('svg').evaluate('''svg=>{const R=[...svg.querySelectorAll('rect')].slice(1).map(r=>r.getBBox());
            return [...svg.querySelectorAll('text')].map(e=>({t:e.textContent,b:e.getBBox()})).filter(o=>{
              const b=o.b; if(b.x<0||b.y<0||b.x+b.width>svg.viewBox.baseVal.width||b.y+b.height>svg.viewBox.baseVal.height) return true;
              const c=R.find(r=>b.x>=r.x&&b.x<r.x+r.width&&b.y>=r.y&&b.y<r.y+r.height); return c&&(b.x+b.width>c.x+c.width||b.y+b.height>c.y+c.height);}).map(o=>o.t)}''')
        assert not bad, (f.out, 'text overflows canvas or card', bad)
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas and cards.')
