#!/usr/bin/env python3
"""Three A5 concept diagrams; house helpers and rendering copied from redraw_a4_20261022.py.
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


# Article labels only; three, five, and seven nodes respectively.
f = Figure('llm-adaptation/01-prompting-rag-fine-tuning', '決策流程',
           '先把能用提示解決的都解決。', 384,
           '先 Prompting；不夠且需要外部、即時或專有知識時加 RAG；仍不夠且需要穩定風格、推理模式或深度專業，且 prompt 已過於複雜時，才考慮 Fine-tuning。')
f.add(arrow(288, 264, 508, 264), arrow(740, 264, 960, 264))
# Multiline masks end exactly 8px above the horizontal connector.
for cx, width, lines in [
    (400, 200, ['不夠？', '需要外部/即時/', '專有知識']),
    (848, 208, ['仍不夠?', '需要穩定的風格/', '推理模式/深度專業，', '且 prompt 已過於複雜']),
]:
    top = 256 - len(lines) * 28 - 8
    s = rect(cx - width // 2, top, width, 256 - top, PAPER, PAPER, 2)
    for i, line in enumerate(lines):
        s += text(cx, top + 24 + i * 28, line, 16, MUTED, 400, 'middle')
    f.add('<g data-label="true">' + s + '</g>')
f.add(node(40, 184, 248, 160, '先 Prompting',
           ['最快、最好debug。', '先把能用提示解決的', '都解決。']),
      node(508, 184, 232, 160, '加 RAG',
           ['注入知識，weights 不動。', 'debug 容易、知識可更新。'], focal=True),
      node(960, 184, 280, 160, '才考慮 Fine-tuning',
           ['改行為。', '先確認它帶來的提升值得', '成本與重訓負擔。']))
f.save()

f = Figure('kb-publishing/01-vault-to-pages', '從 Obsidian 到 GitHub Pages 的發布流程',
           'GitHub Pages 只發布 MkDocs 從 docs/ 產生的內容。', 344,
           'Obsidian Vault 為單一事實來源，GitHub Private Repo 用於版本控制與備份；只有已整理完成、不是草稿的 docs/ 內容經 MkDocs 建置，交由 GitHub Pages 對外發布。')
for x1, x2 in [(248, 296), (560, 608), (740, 788), (980, 1028)]:
    f.add(arrow(x1, 236, x2, 236))
f.add(node(40, 168, 208, 136, 'Obsidian Vault', ['單一事實來源']),
      node(296, 168, 264, 136, 'GitHub Private Repo', ['版本控制 / 備份']),
      node(608, 168, 132, 136, 'docs/', ['已整理完成', '不是草稿。'], focal=True),
      node(788, 168, 192, 136, 'MkDocs', ['公開知識網站建置']),
      node(1028, 168, 212, 136, 'GitHub Pages', ['對外發布']))
f.save()

# The section has both OneHot and Ordinal categorical branches.
# ColumnTransformer groups the three pipelines; it is not an extra stage.
f = Figure('sklearn-pipeline/01-column-transformer-model', 'ColumnTransformer：處理混合型態資料',
           '不同欄位走不同前處理管道', 776,
           'ColumnTransformer 將 num_cols、cat_onehot_cols、cat_ordinal_cols 分別交給 num_pipe、cat_onehot_pipe、cat_ordinal_pipe；各分支經缺失值填補與縮放或編碼後，合併給 GradientBoostingClassifier 模型。')
f.add(rect(304, 152, 608, 584, PAPER, RULE),
      text(336, 192, 'ColumnTransformer', 24, INK, 600))
for y in [296, 472, 648]:
    f.add(arrow(256, y, 336, y))
# A merge dot joins the transformed columns before the model input.
f.add(path('M880,296 H928 Q936,296 936,304 V468', marker=None),
      arrow(880, 472, 932, 472, marker=None),
      path('M880,648 H928 Q936,648 936,640 V476', marker=None),
      f'<circle cx="936" cy="472" r="4" fill="{MUTED}"/>',
      arrow(940, 472, 984, 472))
f.add(node(40, 240, 216, 112, '數值', ['num_cols']),
      node(40, 416, 216, 112, '低基數類別', ['cat_onehot_cols']),
      node(40, 592, 216, 112, '有序類別', ['cat_ordinal_cols']),
      node(336, 224, 544, 144, 'num_pipe',
           ["SimpleImputer(strategy='median')", 'StandardScaler()']),
      node(336, 400, 544, 144, 'cat_onehot_pipe',
           ["SimpleImputer(strategy='most_frequent')", 'OneHotEncoder']),
      node(336, 576, 544, 144, 'cat_ordinal_pipe',
           ["SimpleImputer(strategy='most_frequent')", 'OrdinalEncoder']),
      node(984, 416, 256, 112, '模型', ['GradientBoostingClassifier'], focal=True))
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
