# -*- coding: utf-8 -*-
"""LEO 衛星專題三張圖 — 共用 passive-components/diagram_kit.py 卡片風。

    python3 gen_leo.py   # 產生 01/02/03 svg;再用 scripts/darken_diagrams.py 轉 png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "passive-components"))
from diagram_kit import (svg_head, svg_tail, title_block, card, arrow,
                         legend_chips, info_box, P)

W, H = 1800, 1050


def save(name, s):
    s.append(svg_tail())
    (Path(__file__).resolve().parent / name).write_text("".join(s), encoding="utf-8")
    print("wrote", name)


# 圖一:供應鏈曝險分層
s = [svg_head(W, H)]
s.append(title_block("SUPPLY CHAIN · 曝險分層", P["sky"][1],
                     "台股低軌衛星供應鏈：誰有真實曝險",
                     "需求端已證實；但部署量不能直接換成台廠利潤。依公開證據把台股公司分成三層"))
s.append(card(60, 230, 1680, 150, "indigo", "需求端（已證實）",
              ["Starlink 公司稱 LEO 超過 11,000 顆（2026-10-06）· 訂戶 12.0 million（2026-06-30）· Amazon Leo 已發射 396 顆"]))
s.append(arrow(900, 386, 900, 432))
s.append(card(60, 440, 820, 250, "teal", "已受益：昇達科 3491 · LEO RF 元件",
              ["公司簡報揭露 2026H1 LEO 占營收 77.0%",
               "H1 營收年增約 69.54%（法定月報）",
               "⚠ Q3 月營收仍低於改版前基準 · PE 121.22×（10/12）"]))
s.append(card(920, 440, 820, 250, "amber", "已受益但分部數字待驗：華通 2313",
              ["衛星 PCB · 泰國廠月產能 40 萬平方呎（公司 5/29 簡報）",
               "航太／衛星占比估約 20%（媒體／分析師估計）",
               "⚠ 市占口徑不一 · 衛星分部獲利未揭露 · PE 40.58×"]))
s.append(card(60, 730, 1680, 220, "rose", "概念沾邊／證據不足（12 家）",
              ["地面站／終端：台揚 2314 · 啟碁 6285 · 明泰 3380　上游設備：台達電 2308 · 佳世達 2352 · 同欣電 6271",
               "射頻：全訊 5222 · 穩懋 3105 · 宏捷科 8086　PCB：金像電 2368　太陽能：元晶 6443 · 茂迪 6244",
               "只有交易所分類或第三手名單，缺第一手認證、出貨與營收證據"]))
s.append(legend_chips([("indigo", "需求"), ("teal", "已受益"),
                       ("amber", "已受益・待驗"), ("rose", "證據不足")], 70, H - 40))
save("01-supply-chain-tiers.svg", s)

# 圖二:四環節傳導鏈
s = [svg_head(W, H)]
s.append(title_block("PAYOFF CHAIN · 四環節", P["violet"][1],
                     "從「技術是真的」到「股價還沒反映」",
                     "每家公司都要依序過四關；任何一關過不了，就停在那裡，不往下推"))
steps = [("indigo", "① 技術是真的？"), ("sky", "② 客戶買單？"),
         ("amber", "③ 營收反映？"), ("violet", "④ 股價還沒反映？")]
xs = [60, 490, 920, 1350]
cw = 390
for x, (ph, t) in zip(xs, steps):
    s.append(card(x, 220, cw, 100, ph, t, []))
for i in range(3):
    s.append(arrow(xs[i] + cw + 6, 270, xs[i + 1] - 8, 270))
rows = [("昇達科 3491", 400, [("teal", "過", ["營收高成長", "不只是送樣"]),
                              ("amber", "有疑問", ["自稱在手訂單約 18 億", "但客戶改版延後"]),
                              ("teal", "過", ["H1 年增約 69.54%", "但 Q3 仍低於基準"]),
                              ("rose", "不過", ["PE 121.22×（10/12）", "成長已高度反映"])]),
        ("華通 2313", 700, [("teal", "過", ["報導供應 Starlink", "與 Kuiper"]),
                            ("amber", "有疑問", ["有擴產", "缺訂單量與合約"]),
                            ("amber", "有疑問", ["全公司已驗證", "衛星分部是估計"]),
                            ("rose", "無法判斷", ["有當日 PE 40.58×", "缺衛星分部獲利"])])]
for name, y, cells in rows:
    s.append(f'<text x="64" y="{y-16}" font-size="26" font-weight="bold" fill="#1f2430">{name}</text>')
    for x, (ph, t, ls) in zip(xs, cells):
        s.append(card(x, y, cw, 200, ph, t, ls))
s.append(legend_chips([("teal", "通過"), ("amber", "有疑問"), ("rose", "不過／無法判斷")], 70, H - 40))
save("02-payoff-chain.svg", s)

# 圖三:結論與推翻條件
s = [svg_head(W, H)]
s.append(title_block("VERDICT · 結論與檢查點", P["rose"][1],
                     "結論：無法判定（under-determined）",
                     "真實曝險可確認；「耐久又沒被充分定價」目前公開資料答不出來"))
s.append(card(60, 230, 540, 250, "rose", "Bear 35%",
              ["合規產能可快速複製", "華通市占口徑收窄", "擴產帶來價格競爭"]))
s.append(card(630, 230, 540, 250, "amber", "Base 45%",
              ["「非中非台」要求延續", "華通維持主要供應位置", "定價權仍未證實"]))
s.append(card(1200, 230, 540, 250, "teal", "Bull 20%",
              ["合規＋長認證難複製", "華通持續吃到部署量", "長認證仍是待證假設"]))
s.append(info_box(60, 520, 1680, 150, "唯一會讓護城河論點失效的假設",
                  ["客戶不再要求「非中非台」，或合規、已認證的東南亞衛星 PCB 產能不再稀缺",
                   "機率是主觀情境，不是事實；用途是看結論對假設有多敏感"], accent="violet"))
s.append(info_box(60, 710, 1680, 190, "四個檢查點（事先登記，到期對答案）",
                  ["2026-10　時程：Q3 至少一個月回到約 3.49 億元？→ 七～九月全低於門檻；訂單下修未確認",
                   "2026-10　定價：本益比仍反映高成長？→ 10/12 PE 121.22×",
                   "2026-11　耐久性：華通泰國產能連得到衛星營收？　證據邊界：其他公司拿出第一手證據？"]))
save("03-verdict-checkpoints.svg", s)
