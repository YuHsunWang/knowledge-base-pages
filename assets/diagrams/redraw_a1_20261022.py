#!/usr/bin/env python3
"""Four A1 concept diagrams; house helpers and rendering from redraw_b_20261022.py.
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
    return rect(cx - math.ceil(w / 8) * 4, line_y - 32, w, 24, PAPER, PAPER, 2) + text(cx, line_y - 16, s, size, color, 400, 'middle')


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


# A1: three independent return lanes reproduce the original ASCII topology.
f = Figure('coding-agent-sop/01-issue-to-pr', 'Coding Agent 工作流：從 Issue 到 PR 的實際 SOP',
           '每一階段都有明確的「完成定義」', 552,
           'Issue、Plan、Implement、Test、Review、PR 六階段；Implement、Test、Review 不過就退回 Plan 迭代。')
xs = [40, 248, 456, 664, 872, 1080]
for i in range(5):
    f.add(arrow(xs[i] + 160, 228, xs[i + 1], 228))
for source, target, lane in [(536, 348, 344), (744, 332, 408), (952, 316, 472)]:
    f.add(path(f'M{source},280 V{lane-8} Q{source},{lane} {source-8},{lane} H{target+8} Q{target},{lane} {target},{lane-8} V280', dashed=True))
f.add(label(640, 472, '不過就退回上一步迭代'))
for x, title, lines in zip(xs, ['Issue', 'Plan', 'Implement', 'Test', 'Review', 'PR'],
                            [['規格'], ['計畫'], ['實作'], ['測試'], ['審查'], []]):
    f.add(node(x, 176, 160, 104, title, lines, focal=title == 'Plan', center=True))
f.save()

# A2: three distinct exits; no shared bus or overlapping connectors.
f = Figure('agent-memory/01-upsert', 'Upsert 而非 Append',
           '寫入新記憶前，先查詢有沒有衝突的舊記憶，有則更新，沒有才新增。', 608,
           '新記憶查詢相似記憶（top-3）：有高相似且衝突就刪舊寫新並附 timestamp；相容則 merge 或保留舊的；無相似則直接寫入。')
f.add(arrow(240, 352, 328, 352),
      path('M520,256 V216 Q520,208 528,208 H936'),
      arrow(712, 352, 936, 352),
      path('M520,448 V488 Q520,496 528,496 H936'),
      label(772, 208, '有高相似 + 衝突'), label(824, 352, '有高相似 + 相容'), label(772, 496, '無相似'))
f.add(node(40, 300, 200, 104, '新記憶', center=True),
      f'<polygon points="520,256 712,352 520,448 328,352" fill="{FOCAL}" stroke="{ACCENT}"/>',
      text(520, 344, '查詢相似記憶', 24, ACCENT, 600, 'middle'), text(520, 376, 'top-3', 20, MUTED, 400, 'middle'),
      node(936, 152, 304, 112, '刪舊 + 寫新', ['附 timestamp']),
      node(936, 296, 304, 112, 'merge 或保留舊的', ['避免重複'], tsize=20),
      node(936, 440, 304, 112, '直接寫入'))
f.save()

# A3: the article specifies only the forward gates, with no failure return.
f = Figure('llm-evaluation/01-evaluation-gates', '整合的評估決策流程',
           '離線評估是速度，線上 A/B 是真相。', 944,
           '快速離線篩選、Golden set 回歸測試、Shadow test 或小量流量、線上 A/B、全量上線，依原文條件逐關通過。')
gates = [
    ('快速離線篩選', ['品質 + 成本']),
    ('Golden set 回歸測試', ['確認沒有退步']),
    ('Shadow test 或小量流量', ['offline-online 對齊確認']),
    ('線上 A/B', ['含護欄指標、預算樣本量、subgroup 分析']),
    ('全量上線', []),
]
conditions = ['只有通過品質門檻且在 Pareto frontier 上的配置', '通過', '方向一致', '主指標贏、護欄沒觸破']
# Straight drops between stacked gates; each pass condition sits beside its arrow.
for i, condition in enumerate(conditions):
    top = 264 + i * 160
    f.add(arrow(300, top, 300, top + 64), text(324, top + 38, condition, 16, MUTED))
for i, (title, lines) in enumerate(gates):
    f.add(node(40, 168 + i * 160, 520, 96, title, lines, focal=i == 4, lsize=20 if i != 3 else 16))
f.save()

# A4: a common linear day scale; 20-day gaps are 16px, not enlarged.
f = Figure('financial-ml/01-walk-forward', 'Walk-forward',
           '要估「上線後會怎樣」，就該照真實時間走。', 760,
           '三次擴大訓練窗：1–600、1–800、1–1000；各空 20 天後，測試 621–800、821–1000、1021–1200。')
f.add(arrow(160, 168, 1200, 168), text(1200, 152, '天', 16, MUTED, 400, 'end'))
for day, x in [(1, 160), (600, 640), (800, 800), (1000, 960), (1200, 1120)]:
    f.add(path(f'M{x},168 V180', color=RULE, marker=None), text(x, 204, str(day), 16, MUTED, 400, 'middle'))
for i, (train_end, test_start, test_end) in enumerate([(600, 621, 800), (800, 821, 1000), (1000, 1021, 1200)]):
    y = 256 + i * 152
    train_width = train_end * 4 // 5
    gap_x = 160 + train_width
    test_x = gap_x + 16
    f.add(path(f'M{gap_x+8},{y+80} V{y+96}', color=SOFT, marker=None),
          text(gap_x + 8, y + 116, '空 20 天', 16, MUTED, 400, 'middle'),
          rect(160, y, train_width, 80),
          text(180, y + 32, '訓練', 20, INK, 600), text(180, y + 60, f'1 ─ {train_end}', 16, MUTED),
          rect(gap_x, y, 16, 80, PAPER, SOFT, 0, '4,4'),
          rect(test_x, y, 144, 80, FOCAL if i == 2 else CARD, ACCENT if i == 2 else RULE),
          text(test_x + 72, y + 32, '測試', 20, INK, 600, 'middle'),
          text(test_x + 72, y + 60, f'{test_start} ─ {test_end}', 16, MUTED, 400, 'middle'))
f.add(text(40, 724, 'TimeSeriesSplit(gap=20)', 20, MUTED))
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
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas.')
