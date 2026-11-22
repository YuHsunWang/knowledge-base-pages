#!/usr/bin/env python3
"""Four A3 concept diagrams; house helpers and rendering copied from redraw_a2_20261022.py.
Run with the NotoSansCJKtc-Regular.otf path as argv[1].
Dependencies: fonttools, playwright, and Playwright Chromium.
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
    return '<g data-label="true">' + rect(cx - math.ceil(w / 8) * 4, line_y - 32, w, 24, PAPER, PAPER, 2) + text(cx, line_y - 16, s, size, color, 400, 'middle') + '</g>'


def node(x, y, w, h, title, lines=(), focal=False, center=False, tsize=24, lsize=16):
    s = rect(x, y, w, h, FOCAL if focal else CARD, ACCENT if focal else RULE)
    tx, anc = (x + w // 2, 'middle') if center else (x + 20, 'start')
    s += text(tx, y + 40, title, tsize, ACCENT if focal else INK, 600, anc)
    for i, l in enumerate(lines):
        s += text(tx, y + 76 + i * 28, l, lsize, MUTED, 400, anc)
    return f'<g data-node="true">{s}</g>'


class Figure:
    def __init__(self, out, title, subtitle, h, desc):
        self.out = out; self.title = title; self.h = h; self.desc = desc
        self.parts = [rect(0, 0, W, h, PAPER, PAPER, 0), text(40, 64, title, 32, INK, 600), text(40, 104, subtitle, 20, MUTED)]

    def add(self, *s):
        self.parts.extend(s)

    def save(self):
        FIGURES.append(self)


# Labels quoted from the three articles. RAG is split to respect nine nodes.
f = Figure('agentic-rag/01-naive-advanced', 'RAG 架構光譜',
           'Naive RAG／Advanced RAG', 584,
           'Naive RAG：query embed、向量搜尋、生成；Advanced RAG：query 轉換、混合檢索、重排、合成。')
f.add(text(40, 176, 'Naive RAG', 24, INK, 600))
for x in [408, 824]:
    f.add(arrow(x, 264, x + 48, 264))
for x, title in zip([40, 456, 872], ['query embed', '向量搜尋', '生成']):
    f.add(node(x, 216, 368, 96, title, center=True))
f.add(text(40, 384, 'Advanced RAG', 24, INK, 600))
for x in [304, 616, 928]:
    f.add(arrow(x, 464, x + 48, 464))
for x, title in zip([40, 352, 664, 976], ['query 轉換', '混合檢索', '重排', '合成']):
    f.add(node(x, 416, 264, 96, title, center=True))
f.save()

f = Figure('agentic-rag/02-adaptive-agentic-graph', 'RAG 架構光譜',
           'Adaptive RAG／Agentic RAG／GraphRAG', 912,
           'Adaptive RAG 依複雜度路由；Agentic RAG 評估足夠性，不足再檢索，有信心後合成；GraphRAG 經實體抽取、知識圖、社群偵測與圖遍歷。')
f.add(arrow(452, 280, 452, 360), arrow(1040, 280, 1040, 360),
      arrow(452, 432, 452, 480), arrow(452, 552, 452, 600),
      arrow(452, 672, 452, 768),
      path('M300,636 H232 Q224,636 224,628 V524 Q224,516 232,516 H300',
           color=ACCENT, marker='arrow-accent'))
# Opaque labels beside vertical arrows.
for x, y, title, w in [(468, 312, 'agentic', 80), (1056, 312, 'graph', 64),
                       (468, 728, '對答案有信心', 128)]:
    f.add('<g data-label="true">' + rect(x, y - 20, w, 28, PAPER, PAPER, 2)
          + text(x + 8, y, title, 16, MUTED) + '</g>')
f.add('<g data-label="true">' + rect(104, 564, 108, 32, PAPER, PAPER, 2)
      + text(112, 588, '不足再檢索', 16, MUTED) + '</g>')
f.add(node(40, 168, 1200, 112, '複雜度分類器把 query 路由到對的管線',
           ['簡單問題走便宜管線、複雜問題才動用昂貴的 agentic / graph']))
f.add(text(300, 344, 'Agentic RAG', 20, INK, 600),
      text(840, 344, 'GraphRAG', 20, INK, 600))
for y, title in [(360, 'agent 規劃'), (480, '檢索'), (600, '評估足夠性'), (768, '合成')]:
    f.add(node(300, y, 304, 72, title, focal=title == '評估足夠性', center=True))
for y1, y2 in [(432, 480), (552, 600), (672, 768)]:
    f.add(arrow(1040, y1, 1040, y2))
for y, title in [(360, '實體抽取'), (480, '知識圖'), (600, '社群偵測'), (768, '圖遍歷')]:
    f.add(node(840, y, 400, 72, title, center=True))
f.save()

# Seven compensating layers. Risk routing and rollback stay in source layers.
f = Figure('claude-code-review/01-seven-layers', '七層檢查',
           '每一層都會漏，但很少東西能穿過全部。最後一層是快速退回。', 1152,
           '七層檢查由自我驗證到快速退回；第 5 層按風險核准：低不用人、中一人、高兩人；敏感路徑及 CI workflow 一定要有人。')
f.add(arrow(52, 168, 52, 1112))
layers = [
    ('第 1 層：給別人看之前，自己先驗證',
     ['測試、build、或拿設計稿比對的截圖', '用全新的 context 審一次 diff']),
    ('第 2 層：每個 PR 都有 AI 審查',
     ['意見先給其他 agent 驗證，才給人看', '每條意見都要回應。']),
    ('第 3 層：可以擋住合併的安全審查',
     ['bug 審查或安全審查只要還有一條沒處理，PR 就不能合併。']),
    ('第 4 層：會擋人的自動檢查',
     ['lint、型別檢查、各平台的測試、build', '這個改動怎麼測的？要怎麼退回？']),
    ('第 5 層：看風險決定要幾個人核准',
     ['低 → 不用人，自動審查和安全檢查都綠就好　／　中 → 一個人　／　高 → 兩個人',
      'code owner 標成敏感的路徑、任何 CI workflow 檔，一定要有人。']),
    ('第 6 層：merge queue、開關、慢慢上線',
     ['merge queue（合併排隊）／feature flag（功能開關）',
      '分階段發布：公開版本先進 latest 頻道，stable 頻道晚一步跟上。']),
    ('第 7 層：快速發現、快速退回',
     ['開關不用重新部署就能關。／每週輪班的 on-call（值班）',
      '事故檢討時會問：這個問題應該由哪一層抓到？']),
]
for i, (title, lines) in enumerate(layers):
    f.add(node(80, 168 + i * 136, 1160, 128, title, lines, focal=i in [4, 6]))
f.save()

# Three ownership lanes and nine nodes. Questions can reach the human early.
f = Figure('pr-bottleneck/01-agent-human-swimlane', '先讓它能動，再審查讓它變好',
           'AI 審查，跟寫程式的 agent 分開／讓人工審查又快又少', 1176,
           '寫程式 agent 找程式碼、改程式碼、跑檢查除錯；審查 agent 讀 diff、對照規範並直接 commit 修正，有疑問才留言；人工依合併風險決定細審程度。')
f.add(text(40, 176, '寫程式 agent（滿載）', 20, INK, 600),
      text(456, 176, '審查 agent（輕載，子 agent）', 20, INK, 600),
      text(872, 176, '人工審查', 24, INK, 600),
      path('M432,200 V1128', color=RULE, marker=None),
      path('M848,200 V1128', color=RULE, marker=None),
      arrow(224, 344, 224, 456), arrow(408, 512, 456, 512),
      arrow(596, 568, 596, 624), arrow(596, 736, 596, 792),
      arrow(736, 680, 872, 680), label(804, 680, '真有疑問才留言'), arrow(1056, 736, 1056, 792),
      arrow(736, 832, 872, 832),
      arrow(956, 920, 956, 984), arrow(1156, 920, 1156, 984))
f.add(node(40, 232, 368, 112, '找程式碼', ['改程式碼']),
      node(40, 456, 368, 112, '跑檢查除錯', ['測試、lint、型別檢查']),
      node(456, 456, 280, 112, '讀 diff', ['少量探索']),
      node(456, 624, 280, 112, 'coding-standards.md', ['對照 coding-standards.md 修正'], tsize=20),
      node(456, 792, 280, 80, '直接 commit 修正'),
      node(872, 624, 368, 112, '人工審查', focal=True),
      node(872, 792, 368, 128, '合併風險', ['是哪一種門', '出事時影響範圍（blast radius）多大'], focal=True),
      node(872, 984, 168, 140, '單向門', ['退不回來', '這些要細審']),
      node(1072, 984, 168, 140, '雙向門', ['可以輕鬆退回', '稍微看過就好']))
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
        out.parent.mkdir(parents=True, exist_ok=True)
        svgpath = out.with_suffix('.svg')
        svgpath.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
        page = browser.new_page(viewport={'width': W, 'height': f.h}, device_scale_factor=2)
        page.set_content('<!DOCTYPE html><html><body style="margin:0;background:' + PAPER + '">' + svg + '</body></html>')
        page.evaluate("document.fonts.load('20px \"Noto Sans CJK TC\"')")
        assert page.evaluate("document.fonts.check('20px \"Noto Sans CJK TC\"')")
        bad = page.locator('svg').evaluate('''svg=>Array.from(svg.querySelectorAll('text')).map(e=>({t:e.textContent,b:e.getBBox()}))
            .filter(o=>o.b.x<0||o.b.y<0||o.b.x+o.b.width>svg.viewBox.baseVal.width||o.b.y+o.b.height>svg.viewBox.baseVal.height).map(o=>o.t)''')
        assert not bad, (slug, 'text outside canvas', bad)
        bad_nodes = page.locator('svg').evaluate("""svg=>Array.from(svg.querySelectorAll('g[data-node]')).flatMap(g=>{
            const r=g.querySelector('rect').getBBox();
            return Array.from(g.querySelectorAll('text')).filter(t=>{
                const b=t.getBBox();return b.x<r.x+8||b.y<r.y+4||b.x+b.width>r.x+r.width-8||b.y+b.height>r.y+r.height-4;
            }).map(t=>t.textContent);
        })""")
        assert not bad_nodes, (slug, 'text outside node', bad_nodes)
        bad_masks = page.locator('svg').evaluate("""svg=>{
            const boxes=Array.from(svg.querySelectorAll('g[data-node]>rect')).map(e=>e.getBBox());
            return Array.from(svg.querySelectorAll('g[data-label]')).filter(g=>{
                const a=g.querySelector('rect').getBBox();
                return boxes.some(b=>Math.min(a.x+a.width,b.x+b.width)>Math.max(a.x,b.x)&&Math.min(a.y+a.height,b.y+b.height)>Math.max(a.y,b.y));
            }).map(g=>g.textContent);
        }""")
        assert not bad_masks, (slug, 'label mask overlaps node', bad_masks)
        overlaps = page.locator('svg').evaluate("""svg=>{
            const ts=Array.from(svg.querySelectorAll('text')).map(e=>({t:e.textContent,b:e.getBBox()}));
            return ts.flatMap((a,i)=>ts.slice(i+1).filter(c=>Math.min(a.b.x+a.b.width,c.b.x+c.b.width)>Math.max(a.b.x,c.b.x)&&Math.min(a.b.y+a.b.height,c.b.y+c.b.height)>Math.max(a.b.y,c.b.y)).map(c=>[a.t,c.t]));
        }""")
        assert not overlaps, (slug, 'overlapping text', overlaps)
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas and nodes.')
