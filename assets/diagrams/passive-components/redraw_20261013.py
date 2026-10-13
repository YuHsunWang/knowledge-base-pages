#!/usr/bin/env python3
"""Redraw the eleven published figures; render HTML -> editable SVG + PNG.
Sources and frozen data: refresh-20261013-source.json. Run from any cwd.
Theme maps scripts/darken_diagrams.py roles to dark SVG directly (no recolor).
Noto Sans CJK TC is subset and embedded, so exports need no remote fonts.
Diagram Design: architecture, flowchart, state, line/bar and editorial matrix.
Fidelity: aggregate leaf lists into panels; all checks/company names retained.
The old 05–07 SVG placeholder text is replaced by actual plotted data.
Deps (not in requirements.txt, which is the site build):
  pip install fonttools playwright && playwright install chromium
New glyphs need NotoSansCJKtc-Regular.otf placed next to this script.
"""
from pathlib import Path
from html import escape
import json,base64,io,re
from fontTools.ttLib import TTFont
from fontTools import subset
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'refresh-20261013-source.json').read_text())
PAPER='#080D1C';CARD='#17213A';INK='#E6ECF8';MUTED='#A9B4CC';RULE='#394762';ACCENT='#F08A59'
SERIES=['#9CAF8F','#82A0C0','#D3AD7A',ACCENT]
FIGURES=[]
def text(x,y,s,size=20,color=INK,weight=400,anchor='start'):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(s))}</text>'
def rect(x,y,w,h,fill=CARD,stroke=RULE,rx=8):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
def line(x1,y1,x2,y2,color=RULE,width=1):
 return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'
def arrow(x1,y1,x2,y2):
 assert x1==x2 or y1==y2
 return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>'
def path(d,dashed=False):
 dash=' stroke-dasharray="4,4"' if dashed else ''
 return f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="1.2"{dash} marker-end="url(#arrow)"/>'
def box(x,y,w,h,title,lines,focal=False):
 s=rect(x,y,w,h,'#30241F' if focal else CARD,ACCENT if focal else RULE)
 s+=text(x+20,y+36,title,24,ACCENT if focal else INK,600)
 for i,l in enumerate(lines):s+=text(x+20,y+76+i*32,l,20,MUTED)
 return s
class Figure:
 def __init__(self,slug,title,subtitle,h=720):
  self.slug=slug;self.title=title;self.h=h;self.parts=[rect(0,0,1280,h,PAPER,PAPER,0),text(40,64,title,32,INK,600),text(40,108,subtitle,20,MUTED)]
 def add(self,*s):self.parts.extend(s)
 def footer(self,source,keys=None):
  y=self.h-80;self.add(line(40,y,1240,y))
  if keys:
   for x,(label,color) in zip([40,344,648,952],keys):self.add(line(x,y+24,x+24,y+24,color,3),text(x+36,y+32,label,16,MUTED))
  else:self.add(text(40,y+32,'資料查核截止：2026-10-13',16,MUTED))
  self.add(text(40,y+64,source,16,MUTED))
 def save(self):FIGURES.append(self)
# 01: same five tiers and all leaf categories; arrows carry tier sequence.
f=Figure('01-industry-tree','被動元件產業鏈全貌','材料與製程影響規格，元件連到終端，再以財務指標驗證。')
for i in range(4):f.add(arrow(256+i*240,360,280+i*240,360))
items=[('上游材料',['BaTiO3 粉體','Ni／RuO2 漿料','鐵氧體／磁粉芯','NiCr／銅合金']),('元件製造',['MLCC','晶片電阻','功率電感','鉭容／薄膜電容']),('終端應用',['AI 伺服器／HPC','電動車','工控／能源','消費電子']),('台廠曝險',['國巨／華新科','禾伸堂／大毅','奇力新：併入國巨','按產品拆分營收']),('追蹤指標',['月營收 MoM／YoY','ASP／交期','稼動率／毛利率','DSI／AI／車用占比'])]
for i,(title,ls) in enumerate(items):
 x=40+i*240;f.add(rect(x,208,216,304,'#30241F' if i==4 else CARD,ACCENT if i==4 else RULE));f.add(text(x+16,252,title,24,INK,600))
 for j,s in enumerate(ls):f.add(text(x+16,308+j*44,s,16,MUTED))
f.footer('來源：本站產業總覽與個股追蹤；框架示意，不代表已確認訂單。');f.save()
# 02: combine rumor/product into one gate; preserve spec, stage, finance, yes/no.
f=Figure('02-ai-server-validation','AI 伺服器需求驗證流程','把題材逐項驗證；證據不完整時停止外推 EPS。',1000)
for y in [240,368,496]:f.add(arrow(344,y,344,y+40))
f.add(arrow(344,624,344,648),arrow(472,704,840,704),arrow(344,760,344,812))
f.add(rect(624,672,64,24,PAPER,PAPER,0),text(656,688,'是',16,MUTED,400,'middle'),rect(356,776,64,24,PAPER,PAPER,0),text(388,792,'否',16,MUTED,400,'middle'))
gates=[('1｜題材與品類',['MLCC 去耦／VRM 電感／鉭容／電流感測']),('2｜規格驗證',['低 ESL／高 Isat／低 DCR／低 TCR']),('3｜供應鏈階段',['送樣 → AVL → 小量／大量量產']),('4｜財務與訂單',['營收占比／毛利貢獻／急單、短約、長約'])]
for i,(t,ls) in enumerate(gates):
 y=152+i*128;f.add(rect(64,y,560,88),text(84,y+32,t,24,INK,600),text(84,y+64,ls[0],20,MUTED))
f.add(f'<polygon points="344,648 472,704 344,760 216,704" fill="#30241F" stroke="{ACCENT}"/>',text(344,704,'證據完整？',20,INK,600,'middle'))
f.add(rect(840,660,360,88),text(864,696,'納入研究判斷',24,INK,600),text(864,728,'仍需估值與失效條件',20,MUTED))
f.add(rect(184,812,320,64),text(344,852,'待確認；不外推 EPS',20,MUTED,400,'middle'))
f.footer('來源：本站研究驗證框架；原「題材」與「品類」合併一關，其餘關卡保留。');f.save()
# 03: vertical customer qualification route; return branch uses a separate corridor.
f=Figure('03-automotive-qualification','車規認證與商業化路徑','AEC-Q200 元件測試與客戶量產核准分開確認。',1000)
for y in [248,376,504,632]:f.add(arrow(368,y,368,y+40))
f.add(path('M648,456 H744 Q752,456 752,464 V848 Q752,856 744,856 H96 Q88,856 88,848 V168 Q88,160 96,160 H128',True))
stages=[('1｜開發與元件測試',['MLCC／電阻／電感；AEC-Q200 測試']),('2｜Tier-1／OEM AVL',['客戶合格供應商名單與導入規格']),('3｜PPAP 量產前核准',['生產件核准與品質系統確認']),('4｜量產出貨',['出貨、營收與車用占比可核對']),('5｜長期可靠度與貢獻',['PCN 控管；營收、毛利與替換成本'])]
for i,(t,ls) in enumerate(stages):
 y=160+i*128;f.add(rect(128,y,520,88,'#30241F' if i==3 else CARD,ACCENT if i==3 else RULE),text(148,y+32,t,24,INK,600),text(148,y+64,ls[0],20,MUTED))
f.add(text(800,216,'應用不同，規格不同',24,INK,600),text(800,264,'BMS／電池管理',20,MUTED),text(800,304,'OBC／DC-DC',20,MUTED),text(800,344,'逆變器／ADAS',20,MUTED),text(800,520,'未核准或 PCN 變更',24,INK,600),text(800,560,'改善材料／製程並重驗',20,MUTED))
f.footer('來源：本站車規驗證框架；開發與元件測試合併，商業化關卡與重驗路徑保留。');f.save()
# 04: no connectors: comparative company research panels, same common checklist.
f=Figure('04-company-tracking-map','台灣公司研究追蹤地圖','同一套檢查順序，各家的財務問題不同。',896)
rows=[('國巨 2327｜平台型',['產品：MLCC／電阻／鉭容／磁性／感測','檢查：事業部毛利、整合與 AI 拆分','紅旗：槓桿、標準品 ASP、來源不明']),('華新科 2492｜景氣敏感',['產品：MLCC／電阻','檢查：ASP、稼動率、車規與 AI 量產','紅旗：業外收益與景氣過度外推']),('禾伸堂 3026｜製造與代理',['產品：自有 MLCC／主動元件代理','檢查：分部毛利、應收与庫存'.replace('与','與'),'紅旗：代理線變動、壓貨']),('大毅 2478｜电阻專業'.replace('电','電'),['產品：厚膜／薄膜／電流感測／抗硫化','檢查：利基占比、車用／AI 認證','紅旗：商品化、送樣未轉量產'])]
for i,(t,ls) in enumerate(rows):
 x=40+(i%2)*616;y=152+(i//2)*264;f.add(box(x,y,584,232,t,ls,i==3))
f.add(rect(40,680,1200,96),text(60,716,'奇力新／美桓｜國巨內部磁性元件',24,INK,600),text(60,752,'檢查 AI VRM 量產、車用認證與整合；沒有獨立財報，不能獨立估值。',20,MUTED))
f.footer('共同檢查：品類 → 規格 → 客戶階段 → 營收占比 → 毛利率 → 風險。');f.save()
# Helpers for data panels, where scaled coordinates are exempt from 4px grid.
def monthly(c):return [float(next(r for r in DATA['monthly'][str(m)]['rows'] if r[0]==c)[2].replace(',','')) for m in range(4,10)]
companies=['2327','2492','3026','2478'];names=[DATA['quarterly']['companies'][c]['name'] for c in companies]
# 05: all actual monthly observations; normalized index, disclose nonzero domain.
f=Figure('05-monthly-revenue-index-line','月營收指數化比較','2026/04–09；四月 = 100。縱軸 80–140，呈現相對變化，不比較絕對規模。')
left=112;right=1184;top=168;bottom=528
for tick in [80,100,120,140]:
 y=bottom-(tick-80)/60*(bottom-top);f.add(line(left,y,right,y,RULE),text(96,y+4,tick,16,MUTED,400,'end'))
for i,m in enumerate(range(4,10)):
 x=left+i*(right-left)/5;f.add(text(x,568,f'{m:02d} 月',20,MUTED,400,'middle'))
keys=[]
for j,c in enumerate(companies):
 vals=monthly(c);vals=[v/vals[0]*100 for v in vals];pts=[(left+i*(right-left)/5,bottom-(v-80)/60*(bottom-top)) for i,v in enumerate(vals)];points=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)
 f.add(f'<polyline points="{points}" fill="none" stroke="{SERIES[j]}" stroke-width="{3 if j==3 else 2}" stroke-linejoin="round"/>')
 if j==3:
  for x,y in pts:f.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{SERIES[j]}"/>')
 keys.append((f'{names[j]}：九月 {vals[-1]:.1f}',SERIES[j]))
f.footer('來源：MOPS 2026/04–09 自結月報；各月 URL 見來源 JSON／月度追蹤表。截止 2026-10-13。',keys);f.save()
# 06: four independent small multiples, same scale, consistent income attribution.
f=Figure('06-profitability-margin-trend','Q1–Q2 獲利率變化','毛利率／營益率／合併淨利率（%）；單季、同一合併口徑，不混用母公司淨利。',864)
metric_colors=[ACCENT,'#82A0C0','#9CAF8F'];labels=['毛利','營益','淨利']
for k,c in enumerate(companies):
 x=40+(k%2)*616;y=152+(k//2)*288;f.add(text(x,y,names[k],24,INK,600));lx=x+56;rx=x+360;ty=y+32;by=y+176
 for tick in [0,20,40]:
  yy=by-tick/40*(by-ty);f.add(line(lx,yy,rx,yy),text(lx-12,yy+4,tick,16,MUTED,400,'end'))
 old=DATA['quarterly_q1'][c];t=DATA['quarterly']['companies'][c];new=[t['gm'],t['om'],t['nm']]
 for j,(v1,v2) in enumerate(zip(old,new)):
  y1=by-v1/40*(by-ty);y2=by-v2/40*(by-ty);f.add(f'<polyline points="{lx},{y1:.2f} {rx},{y2:.2f}" fill="none" stroke="{metric_colors[j]}" stroke-width="2"/>',text(x+388,y+64+j*40,f'{labels[j]} {v2:.2f}%',16,metric_colors[j]))
 f.add(text(lx,by+32,'Q1',16,MUTED,400,'middle'),text(rx,by+32,'Q2',16,MUTED,400,'middle'))
f.footer('來源：2026Q2 公司簡報／MOPS 損益表；Q1 = H1 − Q2 或 Q1 揭露。截止 2026-10-13。',[(labels[i]+'率',metric_colors[i]) for i in range(3)]);f.save()
# 07: distinct units and dates; one axis per panel, 4 bars each (not 12 on one axis).
f=Figure('07-latest-snapshot-bars','營收、獲利與估值快照','三個面板日期不同；營收改善不能直接換成合理 PE。')
vals=[]
for c in companies:
 r=next(r for r in DATA['monthly']['9']['rows'] if r[0]==c);a=float(r[2].replace(',',''));b=float(r[4].replace(',',''));v=next(v for v in DATA['valuation']['twse']['rows'] if v[0]==c);vals.append([(a/b-1)*100,DATA['quarterly']['companies'][c]['om'],float(v[5])])
for p,(title,period,ceiling) in enumerate([('營收 YoY（%）','2026/09',60),('營益率（%）','2026Q2',30),('交易所 PE（倍）','2026-10-12',90)]):
 px=40+p*408;f.add(text(px,156,title,24,INK,600),text(px,188,period,16,MUTED));lx=px+40;by=528;ty=232
 for tick in [0,ceiling/3,ceiling*2/3,ceiling]:
  yy=by-tick/ceiling*(by-ty);f.add(line(lx,yy,px+384,yy),text(lx-8,yy+4,f'{tick:.0f}',16,MUTED,400,'end'))
 for k,c in enumerate(companies):
  x=lx+8+k*84;v=vals[k][p];h=v/ceiling*(by-ty);focal=(p==0 and k==1)or(p==2 and k==2);color=ACCENT if focal else MUTED
  f.add(rect(x,by-h,60,h,'#30241F' if focal else CARD,color,0),text(x+30,by-h-12,f'{v:.2f}',16,color,400,'middle'),text(x+30,568,names[k],16,MUTED,400,'middle'))
f.footer('來源：MOPS 九月月報、2026Q2 季報與 TWSE 10/12 收盤估值；查核截止 2026-10-13。');f.save()
# 08: five-stage cycle; directions retained, unsourced numeric thresholds disclosed in prose.
f=Figure('08-inventory-cycle-stages','被動元件景氣循環五階段','經驗框架；不以單月反彈或法說語氣直接判定景氣位置。')
for i,label in enumerate(['交期轉短','主動去庫','跌幅收斂','需求回溫']):
 x=216+i*240;f.add(arrow(x,360,x+64,360),rect(x+4,320,56,20,PAPER,PAPER,0),text(x+32,336,label,12,MUTED,400,'middle'))
f.add(path('M1088,504 V552 Q1088,560 1080,560 H136 Q128,560 128,552 V504'))
phases=[('1｜過熱',['溢價、交期上升','重複下單／擴產','法說：供不應求']),('2｜轉折',['溢價收斂／庫存增','交期縮短','法說：觀察通路']),('3｜衰退',['營收連降／去庫','ASP 與稼動率下滑','法說：能見度低']),('4｜築底',['跌幅收斂、交期穩','庫存降、稼動止跌','法說：時點未明']),('5｜復甦',['需求與營收改善','ASP／稼動率回升','法說：需求回溫'])]
for i,(t,ls) in enumerate(phases):
 x=40+i*240;f.add(rect(x,208,176,296,'#30241F' if i==0 else CARD,ACCENT if i==0 else RULE),text(x+16,252,t,24,INK,600))
 for j,l in enumerate(ls):f.add(text(x+16,304+j*72,l,16,MUTED))
f.add(text(640,600,'需求再次過熱，進入下一輪循環',20,MUTED,400,'middle'))
f.footer('來源：本站景氣框架；未有可靠來源的數值門檻留在文章並標未更新，不畫成最新實測。');f.save()
# 09: preserve the categorical matrix; do not invent two continuous axes.
f=Figure('09-cycle-valuation-matrix','景氣位置 × 估值判讀','同一個 PE，在不同景氣位置需要不同盈餘基礎。')
xs=[40,224,416,664,992];headers=['景氣階段','P/B','PE 表象','檢查原則','研究動作']
for x,h in zip(xs,headers):f.add(text(x+16,188,h,20,INK,600))
rows=[['過熱','高位','峰值 E 使 PE 偏低','用正常化 EPS 重算','降低樂觀假設'],['衰退／去庫','下修','E 下滑使 PE 偏高','高 PE 不等於貴','確認庫存与現金流'.replace('与','與')],['築底','可能接近低位','極高或虧損','需驗證復甦時間','保留情境與風險'],['復甦初期','逐步回升','隨獲利改善回落','同查獲利品質、倍數','檢查假設是否達成']]
for i,row in enumerate(rows):
 y=216+i*88;f.add(rect(40,y,1200,72,'#30241F' if i==0 else CARD,ACCENT if i==0 else RULE))
 for x,v in zip(xs,row):f.add(text(x+16,y+44,v,16,INK if x==40 else MUTED,600 if x==40 else 400))
f.footer('來源：本站估值框架；情境示意，非買賣指令；歷史位階須另以完整數列驗證。');f.save()
# 10: preserve all quality adjustments, company anchors, scenarios and falsifiers.
f=Figure('10-target-price-scenarios','目標價的三段拆解','先確定盈餘品質，再選估值錨，最後反推現價與失效條件。')
f.add(arrow(400,360,432,360),arrow(808,360,840,360))
f.add(box(40,168,360,360,'1｜建立 EPS 基礎',['落後／當年／正常化並列','調整業外與非控制權益','核對併購、股本與拆股','每個數字附來源與期間'],True))
f.add(box(432,168,376,360,'2｜選估值錨與倍數',['國巨：EV/EBITDA＋分部','華新科：P/B＋正常化 EPS','禾伸堂：製造／代理分部','大毅：轉型後正常化 EPS']))
f.add(box(840,168,400,360,'3｜情境與現價反推',['空方／基準／多方矩陣','現價 ÷ 倍數 = 隱含 EPS','確認所需事件是否可查','設定失效條件與重估觸發']))
f.add(text(40,584,'檢查：不要把樂觀 EPS 與樂觀倍數疊加；試算假設不等於市場共識。',20,MUTED))
f.footer('來源：本站目標價方法；試算數據、模型與日期見文章第五節與來源 JSON。');f.save()
# 11: 8 company-category nodes; count by codes, not category appearances.
f=Figure('11-industry-map','台股被動元件產業地圖','索引去重 38 個代號；含奇力新歷史對象與新聿科興櫃，排除後為 36 個上市櫃代號。',1200)
f.add(box(40,152,1200,144,'上游材料與材料通路',['信昌電(6173)／立敦(6175)／九豪(6127)／越峰(8121)','崇越(5434)／鑫科(3663)／艾華(6204)／勤凱(4760)']))
cat=[('MLCC／薄膜電容',['國巨(2327)／華新科(2492)','禾伸堂(3026)／信昌電(6173)','華容(5328)：薄膜電容']),('電阻與相關業務',['國巨(2327)／華新科(2492)','大毅(2478)／興勤(2428)','光頡(3624)／雷科(6207)','天二(6834)／台達電(2308)']),('鋁質電解電容',['立隆電(2472)／凱美(2375)','鈺邦(6449)／環科(2413)']),('電感／磁性元件',['臺慶科(3357)／鈞寶(6155)','千如(3236)／敦吉(2459)','台達電(2308)／佳邦(6284)','新聿科(7912)：興櫃']),('保護元件',['聚鼎(6224)／興勤(2428)','佳邦(6284)']),('石英／振盪元件',['晶技(3042)／希華(2484)','台嘉碩(3221)／加高(8182)'])]
for i,(title,ls) in enumerate(cat):
 x=40+(i%3)*408;y=344+(i//3)*264;f.add(rect(x,y,384,232,'#30241F' if i==0 else CARD,ACCENT if i==0 else RULE),text(x+16,y+40,title,24,INK,600))
 for j,l in enumerate(ls):f.add(text(x+16,y+80+j*36,l,16,MUTED))
f.add(box(40,896,1200,144,'代理通路 → 終端應用',['禾伸堂(3026)／蜜望實(8043)／日電貿(3090)／敦吉(2459)／增你強(3028)／堡達(3537)','終端：AI 伺服器／車用電子／工控與能源／手機、PC 等消費電子']))
f.add(text(40,1080,'奇力新(2456)：2022 年下市併入國巨，保留為歷史研究對象；跨品類不重複計家數。',16,MUTED))
f.footer('來源：本頁公司索引與公司／TPEx 來源；家數由代號去重重算，最新掛牌狀態仍待核對。');f.save()
# Embed only the actually used glyphs rather than eleven copies of a 16MB font.
alltext=''.join(''.join(f.parts)+f.title for f in FIGURES)
used=''.join(sorted(set(re.sub('<[^>]+>','',alltext))))
fontpath=ROOT/'NotoSansCJKtc-Regular.otf';smallpath=ROOT/'NotoSansCJKtc-Subset.woff'
if fontpath.exists():
 font=TTFont(fontpath);opts=subset.Options();opts.flavor='woff';sub=subset.Subsetter(options=opts);sub.populate(text=used);sub.subset(font);font.flavor='woff';font.save(smallpath)
cmap=TTFont(smallpath).getBestCmap()
missing=sorted({c for c in used if not c.isspace() and ord(c) not in cmap})
assert not missing,('glyphs missing from subset; add NotoSansCJKtc-Regular.otf and rerun',''.join(missing))
font64=base64.b64encode(smallpath.read_bytes()).decode()
fontcss="@font-face{font-family:'Noto Sans CJK TC';src:url(data:font/woff;base64,"+font64+") format('woff');font-weight:100 900}text{font-family:'Noto Sans CJK TC',sans-serif}"
markers=''.join(f'<marker id="{id}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="{color}"/></marker>' for id,color in [('arrow',MUTED),('arrow-accent',ACCENT),('arrow-link','#82A0C0')])
with sync_playwright() as p:
 browser=p.chromium.launch()
 for f in FIGURES:
  prefix=f.slug
  meta={'as_of':'2026-10-13','monthly_urls':[DATA['monthly'][str(m)]['url'] for m in range(4,10)],'quarterly_urls':DATA['quarterly']['sources'],'valuation_url':DATA['valuation']['twse']['url'],'data_file':'refresh-20261013-source.json'}
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="{f.h}" viewBox="0 0 1280 {f.h}" role="img" aria-labelledby="{prefix}-title {prefix}-desc"><title id="{prefix}-title">{escape(f.title)}</title><desc id="{prefix}-desc">{escape(f.title)}。資料期間與來源列於圖內；查核截止 2026-10-13。圖表原始數據見 refresh-20261013-source.json。</desc><defs><style>{fontcss}</style>{markers}</defs><metadata>{escape(json.dumps(meta,ensure_ascii=False))}</metadata>'+''.join(f.parts)+'</svg>'
  html='<!DOCTYPE html><html lang="zh-Hant"><meta charset="utf-8"><title>'+escape(f.title)+'</title><style>html,body{margin:0;background:'+PAPER+'}</style><body>'+svg+'</body></html>'
  source=ROOT/(f.slug+'.html');source.write_text(html)
  # Export first inline SVG from the HTML, per the skill's export contract.
  exported=re.search(r'<svg\b.*?</svg>',html,re.S).group(0)
  (ROOT/(f.slug+'.svg')).write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+exported)
  page=browser.new_page(viewport={'width':1280,'height':f.h},device_scale_factor=2)
  page.goto(source.as_uri());page.evaluate('document.fonts.ready');page.evaluate("document.fonts.load('20px \"Noto Sans CJK TC\"')")
  assert page.evaluate("document.fonts.check('20px \"Noto Sans CJK TC\"')")
  # Check the actual rendered text glyph bounds, not character-count guesses.
  bad=page.locator('svg').evaluate('''svg=>Array.from(svg.querySelectorAll('text')).map(e=>({text:e.textContent,b:e.getBBox()})).filter(o=>o.b.x<0||o.b.y<0||o.b.x+o.b.width>1280||o.b.y+o.b.height>svg.viewBox.baseVal.height).map(o=>o.text)''')
  assert not bad,(f.slug,'text outside canvas',bad)
  page.locator('svg').screenshot(path=str(ROOT/(f.slug+'.png')),omit_background=True);page.close();print('RENDERED',f.slug,1280,f.h,'@2x')
 browser.close()
# The raw font is our new download; remove only it once subset + exports succeed.
if fontpath.exists():fontpath.unlink()
print('PASS: 11 SVG/PNG pairs; embedded Noto Sans CJK TC; glyph bounds valid.')
