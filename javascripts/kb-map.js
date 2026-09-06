/* 知識庫互動地圖 — 通用渲染器
 *
 * 一份渲染器driven三張地圖（被動元件產業鏈、ML 學習路徑、AI Engineering 主題圖）。
 * 差異全部在資料裡，不在程式碼裡；新增一張地圖＝新增一份 JSON ＋一個容器 div。
 *
 * navigation.instant 已啟用，Material 換文件而非重載頁面，所以進入點掛在 document$、
 * 每次導覽重跑；用 DOMContentLoaded 只會在第一頁生效。與 kb-apparatus.js 同一模式。
 *
 * 資料 schema（由 assets/data/gen_maps.py 產生）：
 *   columns: [{key, title, sub}]                欄位＝地圖的主軸
 *   nodes:   [{id, column, name, desc, items}]  節點＝一群項目
 *   edges:   [{from, to, style?, label?}]       連線＝節點之間的關係
 *   items:   [{id, label, sub?, href?, accent?, plain?, meta?, note?}]
 */
(function () {
  'use strict';

  /* 站台開了 use_directory_urls，頁面深度不定；而 MkDocs 只改寫它認得的連結，
   * 不會改寫 data-kbmap 這種自訂屬性。因此以「MkDocs 已正確改寫的 kb-map.css」
   * 當基準來推資料位置，屬性本身只放檔名。 */
  function dataUrl(doc, name) {
    var css = doc.querySelector('link[href$="stylesheets/kb-map.css"]') ||
              document.querySelector('link[href$="stylesheets/kb-map.css"]');
    var base = css ? css.href : window.location.href;
    return new URL('../assets/data/' + name, base).href;
  }

  function boot(doc) {
    doc.querySelectorAll('[data-kbmap]').forEach(function (host) {
      if (host.dataset.ready === '1') return;
      host.dataset.ready = '1';
      var url = dataUrl(doc, host.getAttribute('data-kbmap'));
      fetch(url)
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function (data) { render(host, data); })
        .catch(function (err) {
          host.className = 'kbmap';
          host.appendChild(el('p', 'kbmap__hint',
            '互動地圖載入失敗（' + err.message + '）。本頁下方的清單為相同內容。'));
        });
    });
  }

  function render(host, DATA) {
    var byId = {};
    DATA.items.forEach(function (it) { byId[it.id] = it; });
    DATA.items.forEach(function (it) {
      it._nodes = DATA.nodes.filter(function (n) { return n.items.indexOf(it.id) >= 0; });
    });

    var onlyAccent = false, onlyMulti = false;
    var selected = null, hover = null, hotNode = null, pop = null, anchorEl = null;

    host.textContent = '';
    host.className = 'kbmap';

    // 沒有任何篩選按鈕時（例如文章地圖，每篇只屬於一個節點）整條控制列不渲染，
    // 免得留下一條空殼。
    var bAccent = null, bMulti = null;
    var hasAccent = DATA.items.some(function (i) { return i.accent; });
    var hasMulti = DATA.items.some(function (i) { return i._nodes.length > 1; });
    var bar = null;
    if (hasAccent || hasMulti) {
      bar = el('div', 'kbmap__bar');
      bar.appendChild(el('span', 'kbmap__lab', '篩選'));
      if (hasAccent) { bAccent = filterBtn('只看' + (DATA.accentLabel || '重點')); bar.appendChild(bAccent); }
      if (hasMulti) { bMulti = filterBtn('只看跨節點'); bar.appendChild(bMulti); }
    }

    var hint = el('p', 'kbmap__hint', DATA.hint ||
      '滑過項目：它在其他節點的出現一起亮起。滑過節點：相關連線亮起。點項目：詳情從旁邊展開。');

    var stage = el('div', 'kbmap__stage');
    var wires = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    wires.setAttribute('class', 'kbmap__wires');
    wires.setAttribute('aria-hidden', 'true');
    stage.appendChild(wires);

    // 每個 column 變成一條由上往下的橫幅，段內節點自動換行。
    var colEls = {};
    DATA.columns.forEach(function (c) {
      var band = el('div', 'kbmap__band');
      var h = el('div', 'kbmap__rail kbmap__rail--' + c.key);
      h.appendChild(el('b', '', c.title));
      if (c.sub) h.appendChild(el('small', '', c.sub));
      band.appendChild(h);
      colEls[c.key] = el('div', 'kbmap__nodes');
      band.appendChild(colEls[c.key]);
      stage.appendChild(band);
    });

    var legend = el('div', 'kbmap__legend');
    (DATA.legend || []).forEach(function (l) {
      var s = el('span');
      if (l.swatch) { var i = document.createElement('i'); i.style.background = l.swatch; s.appendChild(i); }
      s.appendChild(document.createTextNode(l.text));
      legend.appendChild(s);
    });

    if (bar) host.appendChild(bar);
    host.append(hint, stage);
    if (legend.childNodes.length) host.appendChild(legend);

    function visible(it) {
      if (onlyAccent && !it.accent) return false;
      if (onlyMulti && it._nodes.length < 2) return false;
      return true;
    }

    function build() {
      closePop();
      Object.keys(colEls).forEach(function (k) { colEls[k].textContent = ''; });
      DATA.nodes.forEach(function (n) {
        var members = n.items.map(function (i) { return byId[i]; })
                             .filter(function (i) { return i && (i.plain || visible(i)); });
        var node = el('div', 'kbmap__node kbmap__node--' + n.column);
        node.dataset.node = n.id;
        node.appendChild(el('h3', '', n.name));
        var countable = members.filter(function (m) { return !m.plain; }).length;
        var desc = (n.desc || '');
        if (countable) desc = (desc ? desc + ' · ' : '') + countable + ' ' + (DATA.unit || '項');
        if (desc) node.appendChild(el('div', 'kbmap__desc', desc));
        var chips = el('div', 'kbmap__chips');
        members.forEach(function (it) { chips.appendChild(it.plain ? plainChip(it) : chip(it)); });
        node.appendChild(chips);
        node.addEventListener('mouseenter', function () { hotNode = n.id; wire(); });
        node.addEventListener('mouseleave', function () { hotNode = null; wire(); });
        colEls[n.column].appendChild(node);
      });
      paint();
      requestAnimationFrame(wire);
    }

    function plainChip(it) { return el('span', 'kbmap__seg', it.label); }

    function chip(it) {
      var b = el('button', 'kbmap__chip' + (it.accent ? ' is-accent' : ''));
      b.type = 'button';
      b.dataset.item = it.id;
      b.setAttribute('aria-expanded', 'false');
      b.appendChild(document.createTextNode(it.label));
      if (it.sub) b.appendChild(el('code', '', it.sub));
      /* 只有需要動作的狀態才畫點：到期在即或已逾期。常青與仍在期內不畫，
         否則 31 篇常青頁各掛一個點，反而把真正該注意的兩三篇淹掉。 */
      if (it.fresh && (it.fresh.state === 'due' || it.fresh.state === 'overdue')) {
        var dot = el('i', 'kbmap__dot kbmap__dot--' + it.fresh.state);
        dot.title = it.fresh.label;
        b.appendChild(dot);
      }
      b.addEventListener('mouseenter', function () {
        hover = it.id; paint();
        if (peekTimer) clearTimeout(peekTimer);
        peekTimer = setTimeout(function () { showPeek(b, it); }, 400);
      });
      b.addEventListener('mouseleave', function () { hover = null; paint(); hidePeek(); });
      b.addEventListener('focus', function () {
        hover = it.id; paint();
        if (peekTimer) clearTimeout(peekTimer);
        peekTimer = setTimeout(function () { showPeek(b, it); }, 400);
      });
      b.addEventListener('blur', function () { hover = null; paint(); hidePeek(); });
      b.addEventListener('click', function (e) {
        e.stopPropagation();
        hidePeek();
        if (selected === it.id && anchorEl === b) { closePop(); paint(); return; }
        selected = it.id; openPop(b, it); paint();
      });
      return b;
    }

    function paint() {
      var active = hover || selected;
      host.querySelectorAll('.kbmap__chip').forEach(function (b) {
        var id = b.dataset.item;
        var isSel = id === selected && b === anchorEl;
        b.classList.toggle('is-sel', isSel);
        b.classList.toggle('is-echo', !!active && id === active && !isSel);
        b.classList.toggle('is-dim', !!active && id !== active);
        b.setAttribute('aria-expanded', String(b === anchorEl));
      });
    }

    function rectOf(id) {
      var e = stage.querySelector('[data-node="' + id + '"]');
      if (!e) return null;
      var s = stage.getBoundingClientRect(), r = e.getBoundingClientRect();
      return { x: r.left - s.left, y: r.top - s.top, w: r.width, h: r.height };
    }
    function curve(a, b) {
      // 直向版：由來源節點底緣中點連到目標節點頂緣中點。
      var x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
      var dy = Math.max(18, (y2 - y1) * 0.45);
      return 'M' + x1 + ',' + y1 + ' C' + x1 + ',' + (y1 + dy) + ' ' +
             x2 + ',' + (y2 - dy) + ' ' + x2 + ',' + y2;
    }
    function wire() {
      wires.textContent = '';
      wires.setAttribute('viewBox', '0 0 ' + stage.offsetWidth + ' ' + stage.offsetHeight);
      (DATA.edges || []).forEach(function (e) {
        var a = rectOf(e.from), b = rectOf(e.to);
        if (!a || !b) return;
        var p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', curve(a, b));
        var cls = e.style === 'dashed' ? 'is-dashed' : '';
        if (hotNode) cls += (e.from === hotNode || e.to === hotNode) ? ' is-hot' : ' is-faded';
        if (cls.trim()) p.setAttribute('class', cls.trim());
        wires.appendChild(p);
        // 刻意不畫逐條連線的標籤：欄間空隙只有 2rem，標籤一定會壓到相鄰欄的
        // chip；同一來源的多條線標籤還會互相重疊。線型的意義由圖例說明，
        // 方向由欄標題與左到右的版面本身表達，逐條標註是冗餘的。
      });
    }

    function openPop(anchor, it) {
      closePop(true);
      anchorEl = anchor;
      pop = el('div', 'kbmap__pop');
      pop.setAttribute('role', 'dialog');
      pop.setAttribute('aria-label', it.label);
      pop.addEventListener('click', function (e) { e.stopPropagation(); });
      pop.appendChild(el('div', 'kbmap__arrow'));
      var x = el('button', 'kbmap__x', '×');
      x.type = 'button';
      x.setAttribute('aria-label', '關閉');
      x.addEventListener('click', function () { closePop(); paint(); anchor.focus(); });
      pop.appendChild(x);
      pop.appendChild(el('h4', '', it.label));
      if (it.sub) pop.appendChild(el('div', 'kbmap__code', it.sub));

      var tags = el('div', 'kbmap__tags');
      if (it.accent) tags.appendChild(el('span', 'kbmap__tag kbmap__tag--accent', DATA.accentLabel || '重點'));
      if (it._nodes.length > 1) {
        tags.appendChild(el('span', 'kbmap__tag kbmap__tag--multi', '跨 ' + it._nodes.length + ' 個節點'));
      }
      var colsSeen = [];
      it._nodes.forEach(function (n) { if (colsSeen.indexOf(n.column) < 0) colsSeen.push(n.column); });
      colsSeen.forEach(function (k) {
        var c = DATA.columns.filter(function (x) { return x.key === k; })[0];
        if (c) tags.appendChild(el('span', 'kbmap__tag', c.title.replace(/\s+/g, '')));
      });
      if (tags.childNodes.length) pop.appendChild(tags);

      var dl = document.createElement('dl');
      (it.meta || []).forEach(function (m) { row(dl, m[0], m[1]); });
      if (it.fresh) row(dl, '時效', it.fresh.label);
      row(dl, '所在節點', it._nodes.map(function (n) { return n.name; }).join('、'));
      pop.appendChild(dl);
      if (it.note) pop.appendChild(el('p', 'kbmap__note', it.note));

      /* 反向連結：站上有哪幾篇引用了這一篇。這層關係散在各頁的「延伸閱讀」
         裡，平常只看得到「這篇連出去哪」，看不到「誰連進來」。 */
      if (it.backlinks && it.backlinks.length) {
        var back = el('div', 'kbmap__back');
        back.appendChild(el('div', 'kbmap__back-h', '被站上 ' + it.backlinks.length + ' 篇引用'));
        var ul = document.createElement('ul');
        it.backlinks.slice(0, 5).forEach(function (b) {
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = b.href;
          a.textContent = b.label.split('：')[0].split('（')[0];
          li.appendChild(a);
          ul.appendChild(li);
        });
        back.appendChild(ul);
        if (it.backlinks.length > 5) {
          back.appendChild(el('div', 'kbmap__back-more',
            '另有 ' + (it.backlinks.length - 5) + ' 篇'));
        }
        pop.appendChild(back);
      }

      if (it.href) {
        var a = document.createElement('a');
        a.className = 'kbmap__go';
        a.href = it.href;
        a.textContent = (DATA.goLabel || '前往') + ' →';
        pop.appendChild(a);
      }
      document.body.appendChild(pop);
      place();
      x.focus({ preventScroll: true });
    }

    /* 詳情卡與預覽卡共用同一套定位：優先展在右側，右邊不夠翻左，兩側都不夠
       就落在下方，並夾在視窗內。 */
    function placeAt(box, anchor) {
      if (!box || !anchor) return;
      var r = anchor.getBoundingClientRect();
      var pw = box.offsetWidth, ph = box.offsetHeight, gap = 12, edge = 10;
      var left, side;
      if (r.right + gap + pw <= window.innerWidth - edge) { left = r.right + gap; side = 'right'; }
      else if (r.left - gap - pw >= edge) { left = r.left - gap - pw; side = 'left'; }
      else { side = 'below'; left = Math.min(Math.max(edge, r.left), window.innerWidth - pw - edge); }
      var top = side === 'below' ? r.bottom + gap : r.top + r.height / 2 - ph / 2;
      top = Math.min(Math.max(top, edge), Math.max(edge, window.innerHeight - ph - edge));
      box.dataset.side = side;
      box.style.left = (left + window.scrollX) + 'px';
      box.style.top = (top + window.scrollY) + 'px';
      var a = box.querySelector('.kbmap__arrow');
      if (!a) return;
      if (side === 'below') {
        a.style.left = Math.min(Math.max(r.left + r.width / 2 - left, 14), pw - 25) + 'px';
        a.style.top = '-6px';
      } else {
        a.style.left = ''; a.style.top =
          Math.min(Math.max(r.top + r.height / 2 - top, 14), ph - 25) + 'px';
      }
    }

    function place() { placeAt(pop, anchorEl); }

    /* 預覽：滑過先給標題與一句話，要看反向連結與前往連結才點開詳情卡。
       延遲 400ms 是必要的——30 個 chip 排在一起，游標經過就跳卡片會很吵。 */
    var peek = null, peekTimer = null, peekAnchor = null;

    function showPeek(anchor, it) {
      if (pop) return;                       // 詳情卡開著就不疊預覽
      hidePeek();
      peekAnchor = anchor;
      peek = el('div', 'kbmap__peek');
      peek.setAttribute('aria-hidden', 'true');   // 內容在詳情卡裡有無障礙版本
      peek.appendChild(el('div', 'kbmap__arrow'));
      peek.appendChild(el('div', 'kbmap__peek-t', it.label));
      if (it.note) peek.appendChild(el('div', 'kbmap__peek-n', it.note));
      if (it.fresh && it.fresh.state !== 'evergreen') {
        peek.appendChild(el('div', 'kbmap__peek-f', it.fresh.label));
      }
      document.body.appendChild(peek);
      placeAt(peek, anchor);
    }

    function hidePeek() {
      if (peekTimer) { clearTimeout(peekTimer); peekTimer = null; }
      if (peek) { peek.remove(); peek = null; }
      peekAnchor = null;
    }

    function closePop(keep) {
      if (pop) { pop.remove(); pop = null; }
      anchorEl = null;
      if (!keep) selected = null;
    }

    if (bAccent) bAccent.addEventListener('click', function (e) {
      e.stopPropagation(); onlyAccent = !onlyAccent;
      bAccent.setAttribute('aria-pressed', String(onlyAccent)); build();
    });
    if (bMulti) bMulti.addEventListener('click', function (e) {
      e.stopPropagation(); onlyMulti = !onlyMulti;
      bMulti.setAttribute('aria-pressed', String(onlyMulti)); build();
    });
    document.addEventListener('click', function () { if (pop) { closePop(); paint(); } });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && pop) { var a = anchorEl; closePop(); paint(); if (a) a.focus(); }
    });
    window.addEventListener('resize', function () { place(); hidePeek(); wire(); });
    window.addEventListener('scroll', function () { place(); hidePeek(); }, { passive: true });

    build();
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function filterBtn(label) {
    var b = el('button', 'kbmap__f', label);
    b.type = 'button';
    b.setAttribute('aria-pressed', 'false');
    return b;
  }
  function row(dl, k, v) {
    dl.appendChild(el('dt', '', k));
    dl.appendChild(el('dd', '', v));
  }

  if (typeof window.document$ !== 'undefined' && window.document$ && window.document$.subscribe) {
    window.document$.subscribe(boot);
  } else {
    document.addEventListener('DOMContentLoaded', function () { boot(document); });
  }
})();
