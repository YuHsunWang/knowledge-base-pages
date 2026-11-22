#!/usr/bin/env python3
"""Four A4 concept diagrams; house helpers and rendering copied from redraw_a3_20261022.py.
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


# Article labels only. Each figure stays within the nine-node budget.
f = Figure('nested-cv/01-inner-outer-isolation', 'Nested CV',
           '超參數選擇 ≠ 模型性能估計', 752,
           '外層 CV 評估性能；每折的訓練集內做內層 CV 選超參數，Test set 隔離於調參之外，只用於評估。')
f.add(rect(40, 152, 1200, 560, PAPER, RULE),
      text(72, 200, '外層 CV（評估性能）', 24, INK, 600),
      rect(72, 236, 736, 392, CARD, RULE),
      text(96, 276, '訓練集', 24, INK, 600))
f.add(arrow(440, 384, 504, 384),
      arrow(1056, 452, 1056, 532),
      path('M640,452 V572 Q640,580 648,580 H904'))
f.add(node(104, 316, 336, 136, '內層 CV（選超參數）',
           ['GridSearchCV', '內層超參數搜索'], focal=True),
      node(504, 316, 272, 136, '模型', ['超參數選擇']),
      node(904, 316, 304, 136, 'Test set', ['test 只碰一次。', '碰了就不能再調。']),
      node(904, 532, 304, 96, '評估性能', ['roc_auc'], focal=True),
      text(72, 680, '每折都跑一次完整的內層超參數搜索', 20, MUTED))
f.save()

# Seven stages, exactly the sequence in the architecture fence.
f = Figure('wave-counter/01-ohlcv-to-report', '波數分類 / 情境判斷器',
           '相對信心，不是統計機率。', 1104,
           'OHLCV 資料經 Pivot 偵測、候選波形產生、規則評分、多因子評分及 Softmax，輸出 JSON / Markdown / PNG 報告。')
for i in range(6):
    f.add(arrow(640, 248 + i * 136, 640, 288 + i * 136))
stages = [
    ('OHLCV 資料', []),
    ('Pivot 偵測', ['ZigZag / ATR ZigZag / Fractal']),
    ('候選波形產生', ['Impulse / ABC / in-progress wave']),
    ('規則評分', ['hard rules + soft heuristics']),
    ('Fibonacci / Channel / Momentum / Multi-timeframe scoring', []),
    ('Softmax 轉為相對信心', []),
    ('JSON / Markdown / PNG 報告', []),
]
for i, (title, lines) in enumerate(stages):
    f.add(node(240, 152 + i * 136, 800, 96, title, lines,
               focal=i == 5, center=True))
f.save()

# Four fetch scripts and their output folders: eight nodes, no implied readers.
f = Figure('chip-backtest/01-fetch-data-folders', '架構總覽',
           'TDCC / yfinance / finlab / TWSE / TPEX', 864,
           'fetch_data.py、fetch_finlab.py、fetch_twse.py 與 fetch_us.py 分別寫入 data/chips/ 與 data/prices/、data/finlab/、data/twse/、data/us_finlab/。')
fetches = [
    ('fetch_data.py', ['TDCC 大戶集中度 + yfinance 股價'], 'data/chips/ + data/prices/'),
    ('fetch_finlab.py', ['finlab 三大法人/融資券/借券', '2007~2018'], 'data/finlab/'),
    ('fetch_twse.py', ['TWSE/TPEX 公開資料', '2019~今'], 'data/twse/'),
    ('fetch_us.py', ['finlab 美股 Nasdaq100', '~2018截止'], 'data/us_finlab/'),
]
for i, (script, lines, folder) in enumerate(fetches):
    y = 168 + i * 176
    f.add(arrow(560, y + 64, 688, y + 64))
    f.add(node(40, y, 520, 128, script, lines),
          node(688, y, 552, 128, folder))
f.save()

# Only the primary chips/prices input is connected to backtest.py;
# the article does not establish finlab/TWSE/US as direct readers of that script.
f = Figure('chip-backtest/02-backtest-analysis', '台股籌碼反向訊號回測系統',
           'backtest.py / analyze.py', 784,
           'data/chips/ 與 data/prices/ 提供籌碼及股價資料，經 backtest.py 輸出 results/detail.parquet 與 summary.csv，再由 analyze.py 進行深度分析。')
for i in range(3):
    f.add(arrow(640, 264 + i * 160, 640, 312 + i * 160))
f.add(node(280, 152, 720, 112, 'data/chips/ + data/prices/',
           ['TDCC 大戶集中度 + yfinance 股價'], center=True),
      node(280, 312, 720, 112, 'backtest.py', focal=True, center=True),
      node(280, 472, 720, 112, 'results/detail.parquet + summary.csv', center=True),
      node(280, 632, 720, 112, 'analyze.py', ['深度分析'], center=True))
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
