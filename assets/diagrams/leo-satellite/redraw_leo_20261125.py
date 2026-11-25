#!/usr/bin/env python3
"""Redraw the three LEO-satellite figures with Diagram Design; SVG + PNG.
Profile kb-night (site dark tokens). Same render contract as
../redraw_b_20261022.py: subset Noto Sans CJK TC embedded in the SVG, PNG
rendered from it with Chromium at 2x. Run from any cwd.
Deps (not in requirements.txt, which is the site build):
  pip install fonttools playwright && playwright install chromium
Pass the full NotoSansCJKtc-Regular.otf path as argv[1] (glyphs are subset).
Replaces the old light generator gen_leo.py (diagram_kit card style).
"""
from pathlib import Path
from html import escape
import base64, io, math, re, sys
from fontTools.ttLib import TTFont
from fontTools import subset
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent            # docs/assets/diagrams/leo-satellite
DOCS = ROOT.parent.parent.parent
PAPER = '#111729'; CARD = '#182038'; INK = '#C9CDD6'; MUTED = '#9AA0AD'; SOFT = '#6C7BA0'
RULE = '#2E3D66'; ACCENT = '#7CC0FF'; ORANGE = '#F0A868'
FOCAL = 'rgba(124,192,255,0.10)'; WARN = 'rgba(240,168,104,0.08)'; W = 1280
FIGURES = []


# ponytail: helpers copied from ../redraw_b_20261022.py (that file runs on import);
# pull them into a shared module if a third generator needs them.
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


# 01 supply-chain tiers: demand forks into the two confirmed beneficiaries; the
# concept tier gets no arrow on purpose (no evidence it receives the demand).
f = Figure('01-supply-chain-tiers', '台股低軌衛星供應鏈：誰有真實曝險',
           '需求端已證實；但部署量不能直接換成台廠利潤。依公開證據把台股公司分成三層。', 816,
           '低軌衛星需求已證實；台股中昇達科已受益、華通已受益但分部數字待驗，另有 12 家只是概念沾邊、證據不足。')
f.add(path('M640,248 V264', marker=None),
      path('M640,264 H338 Q330,264 330,272 V296'), path('M640,264 H942 Q950,264 950,272 V296'))
f.add(node(40, 144, 1200, 104, '需求端（已證實）',
           ['Starlink 公司稱 LEO 超過 11,000 顆（2026-10-06）· 訂戶 12.0 million（2026-06-30）· Amazon Leo 已發射 396 顆']))
f.add(node(40, 296, 580, 184, '已受益：昇達科 3491 · LEO RF 元件',
           ['公司簡報揭露 2026H1 LEO 占營收 77.0%', 'H1 營收年增約 69.54%（法定月報）',
            '注意：Q3 月營收仍低於改版前基準 · PE 121.22×（10/12）'], FOCAL, ACCENT, ACCENT))
f.add(node(660, 296, 580, 184, '已受益但分部數字待驗：華通 2313',
           ['衛星 PCB · 泰國廠月產能 40 萬平方呎（公司 5/29 簡報）', '航太／衛星占比估約 20%（媒體／分析師估計）',
            '注意：市占口徑不一 · 衛星分部獲利未揭露 · PE 40.58×'], WARN, ORANGE, ORANGE))
f.add(node(40, 520, 1200, 184, '概念沾邊／證據不足（12 家）',
           ['地面站／終端：台揚 2314 · 啟碁 6285 · 明泰 3380　上游設備：台達電 2308 · 佳世達 2352 · 同欣電 6271',
            '射頻：全訊 5222 · 穩懋 3105 · 宏捷科 8086　PCB：金像電 2368　太陽能：元晶 6443 · 茂迪 6244',
            '只有交易所分類或第三手名單，缺第一手認證、出貨與營收證據'], 'none', SOFT, MUTED, '6,5'))
f.add(legend(736, [(CARD, RULE, None, '需求'), (FOCAL, ACCENT, None, '已受益'),
                   (WARN, ORANGE, None, '已受益・待驗'), ('none', SOFT, '6,5', '證據不足')]))
f.save()

# 02 payoff chain: a 2 x 4 status grid; the four gates run left to right.
f = Figure('02-payoff-chain', '從「技術是真的」到「股價還沒反映」',
           '每家公司都要依序過四關；任何一關過不了，就停在那裡，不往下推。', 640,
           '昇達科與華通依序檢驗技術、客戶、營收、股價四關：昇達科前三關大致通過但股價已高度反映，華通後三關仍有疑問或無法判斷。')
XS = [208, 472, 736, 1000]; CW = 232
for i in range(3):
    f.add(arrow(XS[i] + CW, 176, XS[i + 1], 176))
for x, t in zip(XS, ['① 技術是真的？', '② 客戶買單？', '③ 營收反映？', '④ 股價還沒反映？']):
    f.add(rect(x, 144, CW, 64), text(x + CW // 2, 184, t, 20, INK, 600, 'middle'))
PASS, DOUBT, FAIL = (CARD, RULE, ACCENT, None), (WARN, ORANGE, ORANGE, None), ('none', SOFT, MUTED, '6,5')
rows = [('昇達科', '3491', 240, [(PASS, '過', ['營收高成長', '不只是送樣']),
                                (DOUBT, '有疑問', ['自稱在手訂單約 18 億', '但客戶改版延後']),
                                (PASS, '過', ['H1 年增約 69.54%', '但 Q3 仍低於基準']),
                                (FAIL, '不過', ['PE 121.22×（10/12）', '成長已高度反映'])]),
        ('華通', '2313', 400, [(PASS, '過', ['報導供應 Starlink', '與 Kuiper']),
                              (DOUBT, '有疑問', ['有擴產', '缺訂單量與合約']),
                              (DOUBT, '有疑問', ['全公司已驗證', '衛星分部是估計']),
                              (FAIL, '無法判斷', ['有當日 PE 40.58×', '缺衛星分部獲利'])])]
for name, code, y, cells in rows:
    f.add(text(40, y + 52, name, 24, INK, 600), text(40, y + 84, code, 16, MUTED))
    for x, ((fill, stroke, tcol, dash), t, ls) in zip(XS, cells):
        f.add(node(x, y, CW, 136, t, ls, fill, stroke, tcol, dash, tsize=20))
f.add(legend(560, [(CARD, RULE, None, '通過'), (WARN, ORANGE, None, '有疑問'), ('none', SOFT, '6,5', '不過／無法判斷')]))
f.save()

# 03 verdict: three scenarios, the one assumption that breaks the moat (focal),
# and the pre-registered checkpoints. No encoding beyond focal, so no legend.
f = Figure('03-verdict-checkpoints', '結論：無法判定（under-determined）',
           '真實曝險可確認；「耐久又沒被充分定價」目前公開資料答不出來。', 704,
           '低軌衛星結論為無法判定：列出 Bear 35%、Base 45%、Bull 20% 三個情境，唯一會推翻護城河的假設，以及四個事先登記的檢查點。')
for x, t, ls in [(40, 'Bear 35%', ['合規產能可快速複製', '華通市占口徑收窄', '擴產帶來價格競爭']),
                 (448, 'Base 45%', ['「非中非台」要求延續', '華通維持主要供應位置', '定價權仍未證實']),
                 (856, 'Bull 20%', ['合規＋長認證難複製', '華通持續吃到部署量', '長認證仍是待證假設'])]:
    f.add(node(x, 144, 384, 168, t, ls))
f.add(node(40, 336, 1200, 136, '唯一會讓護城河論點失效的假設',
           ['客戶不再要求「非中非台」，或合規、已認證的東南亞衛星 PCB 產能不再稀缺',
            '機率是主觀情境，不是事實；用途是看結論對假設有多敏感'], FOCAL, ACCENT, ACCENT))
f.add(node(40, 496, 1200, 168, '四個檢查點（事先登記，到期對答案）',
           ['2026-10　時程：Q3 至少一個月回到約 3.49 億元？→ 七～九月全低於門檻；訂單下修未確認',
            '2026-10　定價：本益比仍反映高成長？→ 10/12 PE 121.22×',
            '2026-11　耐久性：華通泰國產能連得到衛星營收？　證據邊界：其他公司拿出第一手證據？']))
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
                  for i, c in [('arrow', MUTED), ('arrow-accent', ACCENT)])
with sync_playwright() as p:
    browser = p.chromium.launch()
    for f in FIGURES:
        slug = f'leo-{f.out}'
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
              const c=R.find(r=>b.x>=r.x&&b.x<r.x+r.width&&b.y>=r.y&&b.y<r.y+r.height); return c&&b.x+b.width>c.x+c.width;}).map(o=>o.t)}''')
        assert not bad, (f.out, 'text overflows canvas or card', bad)
        page.locator('svg').screenshot(path=str(out.with_suffix('.png')), omit_background=True); page.close()
        print('RENDERED', out.relative_to(DOCS), W, f.h, '@2x')
    browser.close()
print(f'PASS: {len(FIGURES)} figures; embedded Noto Sans CJK TC; text inside canvas and cards.')
