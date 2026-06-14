# -*- coding: utf-8 -*-
"""
diagram_kit.py — design-system helpers for clean, editable knowledge-base diagrams.

Why this exists: diagrams for the KB should look consistent (same fonts, card
style, colours, shadows) and ship as *editable* SVG, not throwaway PNG. This
module gives you the shared tokens + small builders so a new diagram is ~40
lines of composition instead of re-deriving the look every time.

Render to PNG (Traditional-Chinese safe) with librsvg:
    rsvg-convert in.svg -o out.png            # native size
    rsvg-convert -z 2 in.svg -o out@2x.png    # 2x for retina / print

All colours go through CSS-ish hex tokens below so the palette stays coherent.
Edit the tokens here once and every diagram inherits the change.
"""
from html import escape

# ---- shared design tokens -------------------------------------------------
# Font: Noto Sans CJK TC renders Traditional Chinese + Latin cleanly under
# librsvg/fontconfig. Keep this exact family string; it is what resolves.
FONT   = "Noto Sans CJK TC, Noto Sans CJK SC, sans-serif"
INK    = "#1f2430"   # near-black, slightly warm — titles / row labels
MUTE   = "#5b6472"   # muted body text
FAINT  = "#8a93a6"   # arrows / hairlines
CARD   = "#ffffff"
BORDER = "#e6e8ef"

# Phase palette — colour ENCODES meaning (lifecycle phase / category), it is
# not decoration. Each entry is (base, dark-for-text). Pick 2-4 per diagram and
# explain them in a legend so the colour is readable, not random.
P = {
    "indigo": ("#6366f1", "#4338ca"),
    "sky":    ("#0ea5e9", "#0369a1"),
    "amber":  ("#f59e0b", "#b45309"),
    "violet": ("#8b5cf6", "#6d28d9"),
    "teal":   ("#14b8a6", "#0f766e"),
    "rose":   ("#f43f5e", "#be123c"),
}

# Traffic-light grades for matrices: (bg, text, border). Muted, print-friendly.
GRADE = {
    "高": ("#e7f6ec", "#15803d", "#bfe5ca"),
    "中": ("#fef5e1", "#b45309", "#f4dca6"),
    "低": ("#fdeaea", "#be123c", "#f4c7c7"),
}


# ---- canvas ---------------------------------------------------------------
def svg_head(w, h, bg_top="#fbfcfe", bg_bot="#f3f5f9"):
    """Open an SVG with the standard soft canvas, shadow filter and arrowheads.

    Arrowhead markers available: aFaint (neutral flow), aViolet (loop/emphasis).
    Add more markers here if you need another accent colour.
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{bg_top}"/><stop offset="1" stop-color="{bg_bot}"/>
  </linearGradient>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="5" stdDeviation="9" flood-color="#27324a" flood-opacity="0.10"/>
  </filter>
  <marker id="aFaint" markerWidth="11" markerHeight="11" refX="7.5" refY="4" orient="auto">
    <path d="M0,0 L9,4 L0,8 Z" fill="{FAINT}"/>
  </marker>
  <marker id="aViolet" markerWidth="12" markerHeight="12" refX="8" refY="4.2" orient="auto">
    <path d="M0,0 L9.5,4.2 L0,8.4 Z" fill="{P['violet'][0]}"/>
  </marker>
</defs>
<rect x="0" y="0" width="{w}" height="{h}" fill="url(#bg)"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="none" stroke="#e9ecf3"/>
'''


def svg_tail():
    return "</svg>"


# ---- building blocks ------------------------------------------------------
def title_block(kicker, kcolor, title, subtitle):
    """Top-left header. `kicker` is the small letter-spaced eyebrow label.

    IMPORTANT: `title` is the REAL diagram title (e.g. the article topic), never
    a design-style note. Leftover scaffolding like "A | Clean SaaS Card …" must
    never reach the final image.
    """
    return f'''
<text x="72" y="78" font-size="22" font-weight="bold" letter-spacing="3" fill="{kcolor}">{escape(kicker)}</text>
<text x="70" y="132" font-size="46" font-weight="bold" fill="{INK}">{escape(title)}</text>
<text x="72" y="172" font-size="22" fill="{MUTE}">{escape(subtitle)}</text>
'''


def card(x, y, w, h, phase, title, lines):
    """White card with a coloured top accent bar, phase-coloured title, soft
    shadow, and up to a few muted body lines. `lines` is a list of strings."""
    base, dark = P[phase]
    r = 18
    box = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
           f'fill="{CARD}" stroke="{BORDER}" filter="url(#soft)"/>')
    # top accent bar with rounded top corners matching the card radius
    bar = (f'<path d="M{x+r},{y} h{w-2*r} a{r},{r} 0 0 1 {r},{r} v6 '
           f'h-{w} v-6 a{r},{r} 0 0 1 {r},-{r} z" fill="{base}"/>')
    tx = x + 26
    out = [box, bar,
           f'<text x="{tx}" y="{y+62}" font-size="27" font-weight="bold" fill="{dark}">{escape(title)}</text>']
    ly = y + 103
    for ln in lines:
        out.append(f'<text x="{tx}" y="{ly}" font-size="20" fill="{MUTE}">{escape(ln)}</text>')
        ly += 33
    return "".join(out)


def arrow(x1, y1, x2, y2, marker="aFaint", color=None, dash="", width=2.4):
    """Straight connector with an arrowhead."""
    col = color or FAINT
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" '
            f'stroke-width="{width}"{d} marker-end="url(#{marker})"/>')


def loop_arrow(x1, y1, x2, y2, color=None, label="", lcolor=None):
    """Curved S-shaped connector for a feedback / return edge (the 'closed
    loop'). Drawn dashed in an accent colour so the loop reads at a glance."""
    col = color or P["violet"][0]
    lc = lcolor or P["violet"][1]
    # vertical-ish S-curve; tune the 150 offset if endpoints are far apart
    path = (f'<path d="M{x1},{y1} C{x1},{y1-150} {x2},{y2+150} {x2},{y2}" '
            f'fill="none" stroke="{col}" stroke-width="2.6" '
            f'stroke-dasharray="9 7" marker-end="url(#aViolet)"/>')
    txt = ''
    if label:
        txt = (f'<text x="{(x1+x2)/2-150}" y="{(y1+y2)/2-6}" font-size="20" '
               f'font-weight="bold" fill="{lc}">{escape(label)}</text>')
    return path + txt


def legend_chips(items, x, y):
    """Horizontal phase legend: items = [(phase_key, label), ...]."""
    out, lx = [], x
    for ph, lab in items:
        out.append(f'<circle cx="{lx+8}" cy="{y-6}" r="8" fill="{P[ph][0]}"/>')
        out.append(f'<text x="{lx+26}" y="{y}" font-size="21" fill="{MUTE}">{escape(lab)}</text>')
        lx += 40 + len(lab) * 22 + 60
    return "".join(out)


def info_box(x, y, w, h, title, lines, accent="ink"):
    """Rounded note box (e.g. 讀法 / 建議). accent='ink' for neutral, or a phase
    key like 'violet' to tint it."""
    if accent == "ink":
        fill, stroke, tcol = CARD, BORDER, INK
    else:
        base, dark = P[accent]
        fill, stroke, tcol = "#f5f3ff", "#e3dcff", dark
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" '
           f'fill="{fill}" stroke="{stroke}" filter="url(#soft)"/>',
           f'<text x="{x+28}" y="{y+44}" font-size="24" font-weight="bold" fill="{tcol}">{escape(title)}</text>']
    ly = y + 80
    for ln in lines:
        out.append(f'<text x="{x+28}" y="{ly}" font-size="20" fill="{MUTE}">{escape(ln)}</text>')
        ly += 28
    return "".join(out)


def matrix(rows, cols, data, x_left, y_top, width_right,
           lab_w=200, hdr_h=58, rh=78, gapx=16, gapy=12):
    """Render a scorecard/comparison matrix of 高/中/低 cells.

    rows: list of row labels (task types). cols: list of column headers.
    data: rows x cols list of grade strings ('高'/'中'/'低').
    Returns (svg_string, bottom_y) so the caller can place legend boxes after.
    """
    x0 = x_left + lab_w + 24
    cw = (width_right - x0 - gapx * (len(cols) - 1)) / len(cols)
    out = []
    for j, c in enumerate(cols):
        cx = x0 + j * (cw + gapx)
        out.append(f'<rect x="{cx}" y="{y_top}" width="{cw}" height="{hdr_h}" rx="13" '
                   f'fill="{CARD}" stroke="{BORDER}" filter="url(#soft)"/>')
        out.append(f'<text x="{cx+cw/2}" y="{y_top+hdr_h/2+8}" font-size="23" '
                   f'font-weight="bold" text-anchor="middle" fill="{INK}">{escape(c)}</text>')
    row_y0 = y_top + hdr_h + 28
    for i, r in enumerate(rows):
        ry = row_y0 + i * (rh + gapy)
        out.append(f'<text x="{x_left+lab_w}" y="{ry+rh/2+8}" font-size="23" '
                   f'text-anchor="end" fill="{INK}">{escape(r)}</text>')
        for j in range(len(cols)):
            cx = x0 + j * (cw + gapx)
            g = data[i][j]
            bg, fg, bd = GRADE[g]
            out.append(f'<rect x="{cx}" y="{ry}" width="{cw}" height="{rh}" rx="13" '
                       f'fill="{bg}" stroke="{bd}"/>')
            out.append(f'<text x="{cx+cw/2}" y="{ry+rh/2+11}" font-size="30" '
                       f'font-weight="bold" text-anchor="middle" fill="{fg}">{escape(g)}</text>')
    bottom_y = row_y0 + len(rows) * (rh + gapy)
    return "".join(out), bottom_y
