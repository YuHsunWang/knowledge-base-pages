# -*- coding: utf-8 -*-
"""產生四張互動地圖的資料檔與三區 Knowledge Galaxy payload。

每張地圖的「內容」來自站上既有來源，本檔只額外定義**結構**（欄位、節點、連線）
——那是來源檔案沒有的資訊：

  passive-components  公司清單取自〈被動元件台股公司全圖〉的表格；
                      節點把頁面平面的「上游材料」拆成三類材料，才能各自
                      接到它供應的中游品類。
  machine-learning    文章清單與描述取自 mkdocs nav 與各檔 frontmatter；
                      連線是閱讀先後順序。
  ai-engineering      同上，節點＝nav 的主題分組。

任一來源與結構不同步（文章新增/刪除、代號改動）時本檔會 raise 讓建置失敗，
而不是安靜產出一份與站台不一致的地圖。

用法：python3 docs/assets/data/gen_maps.py
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
OUT_DIR = Path(__file__).resolve().parent
LAYOUT_PATH = OUT_DIR / "galaxy-layout.json"
FAILURES = []
SECTION_MAPS = {
    "ai": "map-ai-engineering.json",
    "machine-learning": "map-machine-learning.json",
    "trading": "map-trading.json",
}


# ─────────────────────────── 共用工具 ───────────────────────────
def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if kv:
            out[kv.group(1)] = kv.group(2).strip().strip('"')
    return out


def nav_entries(section):
    """從 mkdocs.yml 取某區的 (標籤, 檔名) 清單，順序即 nav 順序。"""
    cfg = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    out = []
    for label, path in re.findall(r"^\s+- ([^:\n]+):\s*(" + section + r"/[a-z0-9-]+\.md)\s*$",
                                  cfg, re.M):
        out.append((label.strip(), path.strip()))
    return out


def nav_groups(section, nav_title):
    """從 mkdocs.yml 取某區的「分組 → article slug」，保留 nav 順序。"""
    cfg = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    match = re.search(
        rf"^  - {re.escape(nav_title)}:\s*$\n(.*?)(?=^  - |\Z)",
        cfg,
        re.M | re.S,
    )
    if not match:
        return {}
    groups, current = {}, None
    for line in match.group(1).split("\n"):
        group = re.match(r"^\s{6}- ([^:\n]+):\s*$", line)
        if group:
            current = group.group(1).strip()
            groups[current] = []
            continue
        article = re.match(
            rf"^\s+- [^:\n]+:\s*{re.escape(section)}/([a-z0-9-]+)\.md\s*$",
            line,
        )
        if article and current:
            groups[current].append(article.group(1))
    return groups


LINK_RE = re.compile(r"\]\((?!https?:|#|mailto:)([^)\s#]+\.md)(?:#[^)]*)?\)")


def backlink_graph():
    """全站「誰連到誰」。回傳 {目標相對路徑: {來源相對路徑}}。

    index.md 不算來源——它依規則連到該區每一篇，計入的話每篇都會多一條
    沒有訊息量的反向連結，把真正的引用關係淹掉。
    """
    graph = {}
    for md in DOCS.rglob("*.md"):
        if md.name == "index.md":
            continue
        src = md.relative_to(DOCS).with_suffix("").as_posix()
        for raw in LINK_RE.findall(md.read_text(encoding="utf-8")):
            tgt = (md.parent / raw).resolve()
            try:
                rel = tgt.relative_to(DOCS.resolve()).with_suffix("").as_posix()
            except ValueError:
                continue
            if rel != src and tgt.exists():
                graph.setdefault(rel, set()).add(src)
    return graph


def article_title(rel):
    fm = frontmatter(DOCS / (rel + ".md"))
    return fm.get("title", rel.split("/")[-1])


def href_from_section_index(section, rel):
    """從 /<section>/ 這個索引頁看出去，指向某篇文章的相對網址。"""
    sec, stem = rel.split("/", 1)
    return f"{stem}/" if sec == section else f"../{sec}/{stem}/"



REVIEW_DAYS = {"monthly": 31, "quarterly": 92}


def last_commit_date(path):
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(path)],
                         capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return dt.date.fromisoformat(out) if out else None


def freshness(rel, review):
    """回傳 {state, label, days}。與 kb_lint 同一套判準：git 最後提交日 + 週期。

    注意這量的是「檔案多久沒被改」，不是「內容裡的資料多舊」——一次純排版的
    提交也會讓計時重置。真正的資料基準日寫在各頁內文，不在這裡。
    """
    if review == "evergreen":
        return {"state": "evergreen", "label": "常青｜內容不隨時間失效"}
    if review == "archived":
        return {"state": "archived", "label": "已停止更新"}
    limit = REVIEW_DAYS.get(review)
    if not limit:
        return None
    d = last_commit_date(DOCS / (rel + ".md"))
    if not d:
        return {"state": "unknown", "label": "尚未提交"}
    days = (dt.date.today() - d).days
    cadence = {"monthly": "每月", "quarterly": "每季"}[review]
    if days > limit:
        state, note = "overdue", f"已逾期 {days - limit} 天"
    elif days > limit - 14:
        state, note = "due", f"再 {limit - days} 天到期"
    else:
        state, note = "fresh", f"{limit - days} 天內有效"
    return {"state": state, "days": days,
            "label": f"{cadence}複查｜{d.isoformat()} 更新｜{note}"}


def check(condition, message):
    if not condition:
        FAILURES.append(message)


def write(name, payload):
    p = OUT_DIR / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len([i for i in payload["items"] if not i.get("plain")])
    print(f"wrote {p.name}  節點 {len(payload['nodes'])}｜項目 {n}｜連線 {len(payload['edges'])}")


# ─────────────────────── 1. 被動元件產業鏈 ───────────────────────
# 市場別與產業別：2026-08-08 以 TWSE t187ap03_L、TPEx mopsfin_t187ap03_O
# 與 TPEx 興櫃名冊核對。
MARKET = {
    "2308": ("上市", "電子零組件"), "2327": ("上市", "電子零組件"),
    "2375": ("上市", "電子零組件"), "2413": ("上市", "電子零組件"),
    "2428": ("上市", "電子零組件"), "2456": ("已下市", "—"),
    "2459": ("上市", "電子零組件"), "2472": ("上市", "電子零組件"),
    "2478": ("上市", "電子零組件"), "2484": ("上市", "電子零組件"),
    "2492": ("上市", "電子零組件"), "3026": ("上市", "電子零組件"),
    "3028": ("上市", "電子通路"), "3042": ("上市", "電子零組件"),
    "3090": ("上市", "電子通路"), "3221": ("上市", "電子零組件"),
    "3236": ("上市", "電子零組件"), "3357": ("上櫃", "電子零組件"),
    "3537": ("上櫃", "電子零組件"), "3624": ("上櫃", "電子零組件"),
    "3663": ("上櫃", "電子零組件"), "4760": ("上櫃", "其他電子"),
    "5328": ("上櫃", "電子零組件"), "5434": ("上市", "電子通路"),
    "6127": ("上櫃", "電子零組件"), "6155": ("上櫃", "電子零組件"),
    "6173": ("上櫃", "電子零組件"), "6175": ("上櫃", "電子零組件"),
    "6204": ("上櫃", "電子零組件"), "6207": ("上櫃", "電子零組件"),
    "6224": ("上市", "電子零組件"), "6284": ("上櫃", "電子零組件"),
    "6449": ("上櫃", "電子零組件"), "6834": ("上櫃", "電子零組件"),
    "7912": ("興櫃", "電子零組件"), "8043": ("上櫃", "電子零組件"),
    "8121": ("上櫃", "電子零組件"), "8182": ("上櫃", "電子零組件"),
}
PC_NODES = [
    ("m_res", "a", "電阻器材料", "氧化鋁陶瓷基板、導電漿墨", ["3663", "6204", "4760"]),
    ("m_cap", "a", "電容器材料", "化成鋁箔、介面瓷粉", ["6173", "6175", "6127"]),
    ("m_ind", "a", "電感器材料", "鐵氧體、導電漿墨", ["8121", "4760"]),
    ("m_dist", "a", "材料與設備通路", "服務多個品類，未逐一對應", ["5434"]),
    ("c_res", "b", "晶片電阻", "", ["2327", "2492", "2478", "2428", "3624", "6207", "6834", "2308"]),
    ("c_mlcc", "b", "陶瓷電容 MLCC", "", ["2327", "2492", "3026", "6127"]),
    ("c_alu", "b", "鋁質電解電容", "", ["2472", "2375", "6449", "2413", "3537", "5328", "3090"]),
    ("c_ind", "b", "電感／磁性元件", "", ["2456", "3357", "6155", "3236", "2459", "7912", "2308", "6284", "8121"]),
    ("c_pro", "b", "保護元件", "", ["6224", "2428", "6284"]),
    ("c_xtal", "b", "石英／振盪元件", "", ["3042", "2484", "3221", "8182"]),
    ("d_dist", "c", "通路", "代理與零組件通路", ["3026", "8043", "3090", "2459", "3028"]),
    ("d_demand", "c", "終端應用", "需求領域，非公司", ["seg1", "seg2", "seg3", "seg4"]),
]
PC_EDGES = (
    [{"from": a, "to": b} for a, b in
     [("m_res", "c_res"), ("m_cap", "c_mlcc"), ("m_cap", "c_alu"), ("m_ind", "c_ind")]]
    + [{"from": n, "to": "d_dist"} for n in
       ["c_res", "c_mlcc", "c_alu", "c_ind", "c_pro", "c_xtal"]]
    + [{"from": "d_dist", "to": "d_demand"},
       {"from": "c_alu", "to": "d_demand", "style": "dashed"}]
)


def build_passive():
    page = DOCS / "trading/passive-components-company-universe.md"
    text = page.read_text(encoding="utf-8")
    section, found = None, {}
    for line in text.split("\n"):
        head = re.match(r"^## (.+)$", line)
        if head:
            section = head.group(1)
        row = re.match(r"^\|\s*(\d{4})\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|", line)
        if not row or not section or "延伸閱讀" in section:
            continue
        code, name, note = row.groups()
        rec = found.setdefault(code, {"name": name, "notes": [], "accent": False})
        if "深度覆蓋" in section:
            rec["accent"] = True
        note = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", note).replace("**", "")
        if note and not note.startswith("見上") and note not in rec["notes"]:
            rec["notes"].append(note)

    mapped = {c for _, _, _, _, m in PC_NODES for c in m if c.isdigit()}
    check(not (mapped - set(found)), f"[被動元件] 地圖引用了頁面沒有的代號：{sorted(mapped - set(found))}")
    check(not (set(found) - mapped), f"[被動元件] 頁面有、地圖未安置的代號：{sorted(set(found) - mapped)}")
    check(not (mapped - set(MARKET)), f"[被動元件] 缺市場別對照：{sorted(mapped - set(MARKET))}")
    if FAILURES:
        return

    items = []
    for code in sorted(mapped):
        rec = found[code]
        market, industry = MARKET[code]
        items.append({
            "id": code, "label": rec["name"], "sub": code, "accent": rec["accent"],
            "meta": [["市場別", market], ["產業別", industry]],
            "note": "；".join(rec["notes"]),
        })
    for i, seg in enumerate(["AI 伺服器", "車用電子", "工控與能源", "消費電子（手機・PC）"], 1):
        items.append({"id": f"seg{i}", "label": seg, "plain": True})

    write("map-passive-components.json", {
        "meta": {"source": "docs/trading/passive-components-company-universe.md",
                 "verified": "2026-08-08 TWSE／TPEx 上市櫃與興櫃名冊"},
        "unit": "家", "accentLabel": "深度覆蓋",
        "hint": "滑過公司：它在其他節點的出現一起亮起。滑過節點：該節點的供應線亮起。點公司：詳情從旁邊展開。",
        "columns": [{"key": "a", "title": "上游　材料", "sub": "決定規格與良率"},
                    {"key": "b", "title": "中游　元件製造", "sub": "吃 ASP 與稼動率"},
                    {"key": "c", "title": "下游　通路與終端", "sub": "庫存週轉的先行指標"}],
        "nodes": [{"id": i, "column": c, "name": n, "desc": d, "items": m}
                  for i, c, n, d, m in PC_NODES],
        "items": items,
        "edges": PC_EDGES,
        "legend": [{"swatch": "var(--kb-accent)", "text": "朱色＝系列深度覆蓋"},
                   {"swatch": "var(--kb-signal)", "text": "青框＝同一家公司在他處也出現"},
                   {"text": "實線＝材料供應與通路匯流"},
                   {"text": "虛線＝製造商直供 EMS／ODM"}],
    })


# ─────────────────────── 2. Machine Learning ───────────────────────
ML_NODES = [
    ("n1", "a", "觀念地基", "先看懂在做什麼", None),
    ("n2", "b", "動手實作", "做得出一個能交付的模型", None),
    ("n3", "c", "綜合應用", "把前兩軌接起來", None),
    ("n4", "c", "統計與實驗", "判斷差異是不是真的", None),
]
ML_EDGES = [
    {"from": "n1", "to": "n2"},
    {"from": "n2", "to": "n3"},
    {"from": "n1", "to": "n4", "style": "dashed"},
]

# ─────────────────────── 3. AI Engineering ───────────────────────
AI_NODES = [
    ("g1", "a", "Prompt 與 Context 工程", "餵給模型什麼", None),
    ("g2", "a", "成本與 Token 優化", "餵得省一點", None),
    ("g3", "b", "RAG 與檢索系統", "讓模型讀到外部知識", None),
    ("g4", "b", "Agent 工程", "讓模型會用工具、能自主", None),
    ("g5", "c", "評估、記憶與觀測", "知道它到底做得好不好", None),
    ("g6", "c", "Claude Code / Skills / MCP", "實際落地的工具鏈", None),
    ("g7", "c", "用 AI 維護知識庫", "本站自己的用例", None),
]
AI_EDGES = [
    {"from": "g1", "to": "g3"},
    {"from": "g1", "to": "g4"},
    {"from": "g3", "to": "g5"},
    {"from": "g4", "to": "g5"},
    {"from": "g4", "to": "g6"},
    {"from": "g2", "to": "g4", "style": "dashed"},
    {"from": "g6", "to": "g7", "style": "dashed"},
]

# ─────────────────────── 4. Trading Research ───────────────────────
TRADING_NODES = [
    ("t1", "a", "策略研究與回測", "研究訊號、回測方法與否證", None),
    ("t2", "b", "產業研究方法", "建立可重複的產業研究流程", None),
    ("t3", "c", "被動元件專題", "用被動元件走完產業研究流程", None),
]
TRADING_EDGES = [
    {"from": "t2", "to": "t3"},
]


GRAPH = {}


def build_section(section, nodes, edges, columns, out_name, hint, group_map, layout,
                  galaxy_id, galaxy_title):
    """AI / ML / Trading 共用：文章與 Galaxy 顯示資料由站台來源合成。"""
    entries = nav_entries(section)
    check(bool(entries), f"[{section}] 從 mkdocs.yml 讀不到任何 nav 條目")
    if not entries:
        return
    stem_label = {}
    for label, path in entries:
        stem_label[Path(path).stem] = label

    node_defs = []
    for nid, col, name, desc, members in nodes:
        if members is None:
            members = group_map.get(name, [])
        node_defs.append((nid, col, name, desc, members))

    node_ids = {nid for nid, *_ in node_defs}
    check(not (node_ids - set(layout)),
          f"[{section}] galaxy layout 缺少節點：{sorted(node_ids - set(layout))}")
    check(not (set(layout) - node_ids),
          f"[{section}] galaxy layout 有不存在的節點：{sorted(set(layout) - node_ids)}")

    mapped = {m for _, _, _, _, ms in node_defs for m in ms}
    check(not (mapped - set(stem_label)),
          f"[{section}] 地圖引用了 nav 沒有的文章：{sorted(mapped - set(stem_label))}")
    check(not (set(stem_label) - mapped),
          f"[{section}] nav 有、地圖未安置的文章：{sorted(set(stem_label) - mapped)}")
    if FAILURES:
        return

    items = []
    for stem in sorted(mapped):
        fm = frontmatter(DOCS / section / f"{stem}.md")
        step_match = re.match(r"^(\d+)\s*·\s*", stem_label[stem])
        label = re.sub(r"^\d+\s*·\s*", "", stem_label[stem])
        label = re.sub(r"（[^）]*）$", "", label).strip()
        meta = []
        if fm.get("date"):
            meta.append(["首次發布", fm["date"]])
        sources = sorted(GRAPH.get(f"{section}/{stem}", set()))
        fresh = freshness(f"{section}/{stem}", fm.get("review"))
        items.append({
            # 地圖掛在該區的 index 頁（URL 為 /<區>/），因此同區文章是相對於它的
            # 子路徑；寫成 ../ 會跳到站根。
            "id": stem, "label": label,
            "href": f"{stem}/",
            "step": step_match.group(1) if step_match else None,
            "meta": meta,
            "note": fm.get("description", ""),
            "fresh": fresh,
            "backlinks": [{"label": article_title(s),
                           "href": href_from_section_index(section, s),
                           "section": s.split("/")[0]}
                          for s in sources],
        })

    region_ids = {
        nid: layout[nid].get("anchorId")
        for nid, *_ in node_defs
        if nid in layout
    }
    regions = []
    for nid, _col, name, desc, members in node_defs:
        if nid not in layout:
            continue
        placement = layout[nid]
        region = {
            "id": placement.get("anchorId"),
            "anchorId": placement.get("anchorId"),
            "label": name,
            "href": "#" + str(placement.get("anchorId")),
            "description": desc,
            "count": len(members),
            "members": members,
        }
        for key in ("x", "y", "mobile", "size", "kind"):
            if key in placement:
                region[key] = placement[key]
        regions.append(region)

    galaxy = {
        "id": galaxy_id,
        "title": galaxy_title,
        "mode": "region-index",
        "host": f"{section}/index.md",
        "center": {"label": galaxy_title},
        "regions": regions,
        "edges": [
            {**edge, "from": region_ids.get(edge["from"]),
             "to": region_ids.get(edge["to"])}
            for edge in edges
        ],
    }
    write(out_name, {
        "meta": {"source": f"mkdocs.yml nav + docs/{section}/*.md frontmatter"},
        "unit": "篇", "goLabel": "閱讀這篇",
        "hint": hint,
        "columns": columns,
        "nodes": [{"id": i, "column": c, "name": n, "desc": d, "items": m}
                  for i, c, n, d, m in node_defs],
        "items": items,
        "edges": edges,
        "galaxy": galaxy,
        "legend": [{"swatch": "var(--kb-signal)", "text": "青框＝同一篇出現在多個節點"},
                   {"swatch": "#C89A2E", "text": "琥珀點＝接近複查期限"},
                   {"swatch": "var(--kb-accent)", "text": "朱點＝已逾期未複查"},
                   {"text": "實線＝建議的閱讀順序｜虛線＝可獨立閱讀"}],
    })


def build_home_galaxy():
    """Derive each drillable domain's section-map pointer from its path."""
    path = OUT_DIR / "map-home.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for region in data.get("regions", []):
        section = region.get("href", "").strip("/")
        if section in SECTION_MAPS:
            region["sectionMap"] = f"assets/data/{SECTION_MAPS[section]}"
        else:
            region.pop("sectionMap", None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {path.name}  領域 {len(data.get('regions', []))}")


def main():
    global GRAPH
    FAILURES.clear()
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    section_names = {"ai", "machine-learning", "trading"}
    check(not (section_names - set(layout)),
          f"[galaxy layout] 缺少 section：{sorted(section_names - set(layout))}")
    check(not (set(layout) - section_names),
          f"[galaxy layout] 有不存在的 section：{sorted(set(layout) - section_names)}")
    GRAPH = backlink_graph()
    build_passive()
    if FAILURES:
        _report_failures()
    build_section(
        "machine-learning", ML_NODES, ML_EDGES,
        [{"key": "a", "title": "觀念", "sub": "懂原理"},
         {"key": "b", "title": "實作", "sub": "做得出來"},
         {"key": "c", "title": "應用與驗證", "sub": "接起來、並確認有效"}],
        "map-machine-learning.json",
        "滑過節點看閱讀順序，點文章看它涵蓋什麼、更新頻率，並可直接前往。",
        nav_groups("machine-learning", "Machine Learning"),
        layout["machine-learning"],
        "machine-learning-galaxy", "Machine Learning",
    )
    build_section(
        "ai", AI_NODES, AI_EDGES,
        [{"key": "a", "title": "輸入", "sub": "餵給模型什麼"},
         {"key": "b", "title": "系統", "sub": "讓它讀得到、做得到"},
         {"key": "c", "title": "營運", "sub": "評估、工具鏈與維運"}],
        "map-ai-engineering.json",
        "滑過節點看主題之間的依賴，點文章看它涵蓋什麼，並可直接前往。",
        nav_groups("ai", "AI Engineering"),
        layout["ai"],
        "ai-engineering-galaxy", "AI Engineering",
    )
    build_section(
        "trading", TRADING_NODES, TRADING_EDGES,
        [{"key": "a", "title": "策略", "sub": "訊號、回測與否證"},
         {"key": "b", "title": "研究方法", "sub": "建立可重複流程"},
         {"key": "c", "title": "產業專題", "sub": "用個案走完流程"}],
        "map-trading.json",
        "滑過節點看研究路徑，點文章看內容、更新頻率，並可直接前往。",
        nav_groups("trading", "Trading Research"),
        layout["trading"],
        "trading-research-galaxy", "Trading Research",
    )
    build_home_galaxy()
    if FAILURES:
        _report_failures()


def _report_failures():
    print("", file=sys.stderr)
    for failure in FAILURES:
        print(f"FAIL  {failure}", file=sys.stderr)
    print("\n地圖結構已與站台內容不同步，請更新 gen_maps.py 或對應頁面。", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
