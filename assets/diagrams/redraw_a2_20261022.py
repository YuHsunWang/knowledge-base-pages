#!/usr/bin/env python3
"""Five A2 concept diagrams; house helpers and rendering from redraw_b_20261022.py.
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


# All visible wording comes from the four target articles. Repeated agent
# boxes denote illustrative instances, not additional named components.
f = Figure('graphrag/01-build-to-retrieval', '建圖到檢索的四階段',
           'GraphRAG：用知識圖譜做檢索', 664,
           '實體/關係抽取、社群偵測、社群摘要、圖感知檢索；Local Search 從相關實體做局部鄰域擴展，Global Search 沿社群階層做全局導覽。')
xs = [40, 352, 664, 976]
for i in range(3):
    f.add(arrow(xs[i] + 264, 256, xs[i + 1], 256))
f.add(path('M1040,336 V372 Q1040,380 1032,380 H816 Q808,380 808,388 V440'),
      path('M1180,336 V404 Q1180,412 1172,412 H1120 Q1112,412 1112,420 V440'))
for i, (title, lines) in enumerate([
    ('實體/關係抽取', ['用 LLM 從文字抽出', '實體與它們之間的關係', '建成知識圖譜']),
    ('社群偵測', ['Leiden 演算法', '階層式分群', '多層「社群」']),
    ('社群摘要', ['把每個社群自動摘要成報告', '多層的語意脈絡地圖']),
    ('圖感知檢索', ['社群層級脈絡', '動態查詢路由']),
]):
    f.add(node(xs[i], 176, 264, 160, title, lines, focal=i == 3))
f.add(node(680, 440, 256, 168, 'Local Search', ['特定、實體中心', '從相關實體做', '局部鄰域擴展']),
      node(984, 440, 256, 168, 'Global Search', ['廣泛、主題式', '沿社群階層做', '全局導覽']))
f.save()

# Six nodes: central assignment versus sequential handoff.
f = Figure('multi-agent/01-supervisor-pipeline', '主要編排模式',
           'Supervisor（主管）／Sequential Pipeline（管線）', 536,
           'Supervisor 的中央協調者動態指派 worker；Sequential Pipeline 的 agent 分階段接力處理。')
f.add(text(72, 176, 'Supervisor（主管）', 24, INK, 600),
      text(72, 208, '依執行狀態動態指派 worker', 20, MUTED),
      text(660, 176, 'Sequential Pipeline（管線）', 24, INK, 600),
      text(660, 208, 'agent 分階段接力處理', 20, MUTED),
      path('M260,304 V328 Q260,336 252,336 H180 Q172,336 172,344 V392'),
      path('M380,304 V328 Q380,336 388,336 H460 Q468,336 468,344 V392'),
      arrow(812, 344, 868, 344), arrow(1020, 344, 1076, 344))
f.add(node(200, 232, 240, 72, '中央協調者', focal=True, center=True),
      node(72, 392, 200, 72, 'worker', center=True),
      node(368, 392, 200, 72, 'worker', center=True))
for x in [660, 868, 1076]:
    f.add(node(x, 304, 152, 80, 'agent', center=True))
f.save()

# Nine nodes across three sketches; no invented coordinator in Mesh or Swarm.
f = Figure('multi-agent/02-mesh-event-swarm', '主要編排模式',
           'Peer-to-Peer Mesh（網狀）／Event-Driven（事件驅動）／Swarm（蜂群）', 568,
           'Mesh 的 agent 經訊息匯流排互通；Event-Driven 的 agent 對事件流反應；Swarm 無中央協調，靠局部互動與 handoff。')
f.add(text(64, 176, 'Peer-to-Peer Mesh（網狀）', 24, INK, 600),
      text(472, 176, 'Event-Driven（事件驅動）', 24, INK, 600),
      text(896, 176, 'Swarm（蜂群）', 24, INK, 600),
      path('M128,280 V336 Q128,344 136,344 H184 Q192,344 192,352 V392'),
      path('M280,392 V360 Q280,352 288,352 H336 Q344,352 344,344 V280'),
      arrow(552, 288, 552, 392), arrow(752, 288, 752, 392),
      arrow(1016, 248, 1104, 248), label(1060, 248, 'handoff'),
      path('M1164,280 V344 Q1164,352 1156,352 H1068 Q1060,352 1060,360 V392'),
      path('M1028,392 V344 Q1028,336 1020,336 H964 Q956,336 956,328 V280'))
for x in [64, 280]:
    f.add(node(x, 216, 128, 64, 'agent', center=True))
f.add(node(128, 392, 216, 64, '訊息匯流排', center=True, tsize=20),
      node(488, 216, 328, 72, '事件流', center=True))
for x in [488, 688]:
    f.add(node(x, 392, 128, 64, 'agent', center=True))
for x, y, w in [(896, 216, 120), (1104, 216, 120), (996, 392, 128)]:
    f.add(node(x, y, w, 64, 'agent', center=True))
f.add(text(64, 512, 'agent 經訊息匯流排直接互通', 20, MUTED),
      text(488, 512, 'agent 對事件流反應', 20, MUTED),
      text(896, 512, '無中央協調，靠局部互動', 20, MUTED))
f.save()

# Two independent 1:1 connections cross the Host/Server trust boundary.
f = Figure('mcp/01-host-client-server', '三方角色',
           'Host／Client／Server', 664,
           'Host 內有兩個 Client，各與單一 Server 維持 1:1 連線；Host 與 Server 之間是信任邊界，工具輸出是不可信輸入。')
f.add(rect(40, 168, 536, 416, PAPER, RULE, 8, '6,5'),
      text(64, 212, 'Host', 24, INK, 600),
      text(64, 244, '跑 LLM、決定要連哪些 server 的應用', 20, MUTED),
      path('M752,212 V584', color=SOFT, dashed=True, marker=None),
      text(752, 176, '信任邊界', 24, INK, 600, 'middle'),
      arrow(536, 320, 856, 320), label(696, 320, '1:1 連線'),
      arrow(856, 384, 536, 384), label(696, 384, '工具輸出'),
      arrow(536, 480, 856, 480), label(696, 480, '1:1 連線'),
      arrow(856, 544, 536, 544), label(696, 544, '工具輸出'))
# Paired directions have 64px separation so label masks clear both strokes.
for y in [288, 448]:
    f.add(node(80, y, 456, 120, 'Client', ['Host 內部，與單一 server 維持 1:1 連線']))
    f.add(node(856, y, 384, 120, 'Server', ['暴露能力（工具/資料/提示）']))
f.add(text(64, 628, '工具輸出 = 不可信輸入', 20, MUTED))
f.save()

# The numbered layer description is post-LN. Do not silently draw pre-LN.
# Two short local bypasses use separate side ports and r=8 elbows.
f = Figure('transformer/01-post-ln-layer', '一層 Transformer 長什麼樣',
           '原始論文把 LayerNorm 放在殘差之後（post-LN）', 920,
           '輸入經 Multi-head self-attention，加回輸入後做 LayerNorm，再經前饋網路 FFN，加回該子層輸入後再做 LayerNorm。')
f.add(text(436, 176, '輸入', 20, INK, 600, 'middle'),
      arrow(436, 192, 436, 232),
      arrow(436, 312, 436, 368),
      arrow(436, 416, 436, 456),
      arrow(436, 528, 436, 568),
      arrow(436, 664, 436, 712),
      arrow(436, 760, 436, 800),
      path('M436,208 H204 Q196,208 196,216 V384 Q196,392 204,392 H412'),
      path('M436,548 H204 Q196,548 196,556 V728 Q196,736 204,736 H412'),
      '<g data-label="true">' + rect(212, 328, 112, 32, PAPER, PAPER, 0) + text(220, 352, '殘差連接', 20, MUTED) + '</g>',
      '<g data-label="true">' + rect(212, 672, 112, 32, PAPER, PAPER, 0) + text(220, 696, '殘差連接', 20, MUTED) + '</g>')
for y in [368, 712]:
    f.add('<g data-node="true">' + rect(412, y, 48, 48) + text(436, y + 32, '+', 24, INK, 600, 'middle') + '</g>')
f.add(node(268, 232, 336, 80, 'Multi-head self-attention', center=True, tsize=20),
      node(268, 456, 336, 72, 'LayerNorm', focal=True, center=True),
      node(268, 568, 336, 96, '前饋網路（FFN）', ['每個詞各自過兩層全連接'], center=True),
      node(268, 800, 336, 72, 'LayerNorm', focal=True, center=True),
      text(696, 288, '詞與詞之間交換資訊', 24, INK, 600),
      text(696, 616, '每個詞自己消化', 24, INK, 600),
      text(696, 652, '中間通常放大成 4 倍寬', 20, MUTED))
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
