/* 靛與朱 — apparatus layer for the Knowledge Base (DEV-114).
 *
 * navigation.instant is enabled, so Material swaps the document without a
 * page load. Everything here must re-run per navigation: that is what
 * document$ is for. A plain DOMContentLoaded listener would apply once and
 * then silently stop working on every subsequent page.
 *
 * Article counts come from hooks/section_counts.py via section-counts.json, so
 * they are the file tree's own numbers and cannot drift from it.
 */
(function () {
  'use strict';

  var calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  var fieldStop = null;

  /* ── rail stagger ─────────────────────────────────────────── */
  function decorateRail(doc) {
    var i = 0;
    doc.querySelectorAll('.md-nav--primary .md-nav__item').forEach(function (item) {
      if (!item.getClientRects().length) return;
      item.style.setProperty('--kb-i', String(i));
      i += 1;
    });
  }

  /* Counts come from hooks/section_counts.py, written to section-counts.json at
     build time. They are not counted in the browser: the header tabs mix content
     sections with generated indexes (首頁, 標籤), and DOM counting would conflate
     section indexes and the tag page with actual articles. */
  var countsPromise = null;

  function siteBase() {
    var el = document.getElementById('__config');
    if (el) {
      try {
        var base = JSON.parse(el.textContent).base;
        if (base) return new URL(base, location.href).href;
      } catch (e) { /* fall through */ }
    }
    return location.origin + '/';
  }

  function loadCounts() {
    if (!countsPromise) {
      countsPromise = fetch(new URL('section-counts.json', siteBase()).href)
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    }
    return countsPromise;
  }

  /* Section key is the path segment the tab points at: .../ai/ -> "ai". */
  function tabKey(href) {
    var parts = href.replace(/[?#].*$/, '').replace(/\/$/, '').split('/');
    return parts[parts.length - 1] || '';
  }

  function decorateTabs(doc, counts) {
    if (!counts || !counts.sections) return;
    doc.querySelectorAll('.md-tabs__link').forEach(function (tab) {
      if (tab.querySelector('.kb-count')) return;
      var n = counts.sections[tabKey(tab.href)];
      if (!n) return;
      var badge = doc.createElement('span');
      badge.className = 'kb-count';
      badge.textContent = String(n);
      tab.appendChild(badge);
    });
  }

  /* ── readout in the secondary sidebar ──────────────────────── */
  function buildReadout(doc, counts) {
    var sidebar = doc.querySelector('.md-sidebar--secondary');
    var scrollwrap = sidebar && sidebar.querySelector(':scope > .md-sidebar__scrollwrap');
    if (!sidebar || !scrollwrap || sidebar.querySelector('.kb-readout') || !counts) return;

    var block = doc.createElement('div');
    block.className = 'kb-readout';

    var head = doc.createElement('h4');
    head.textContent = 'Readout';
    block.appendChild(head);

    [['文章', counts.articles],
     ['分區', Object.keys(counts.sections || {}).length]].forEach(function (pair) {
      var row = doc.createElement('div');
      var label = doc.createElement('span');
      label.textContent = pair[0];
      var value = doc.createElement('b');
      value.textContent = String(pair[1]);
      row.appendChild(label);
      row.appendChild(value);
      block.appendChild(row);
    });

    sidebar.appendChild(block);
  }

  /* ── home hero: eyebrow, gate strip, plotted field ─────────── */
  function decorateHero(doc, counts) {
    var hero = doc.querySelector('.md-typeset .hero-banner');
    if (!hero) return;

    if (!hero.querySelector('.kb-eyebrow')) {
      var eyebrow = doc.createElement('p');
      eyebrow.className = 'kb-eyebrow';
      eyebrow.textContent = 'Obsidian Vault → 公開子集';
      hero.insertBefore(eyebrow, hero.firstElementChild);
    }

    if (!hero.querySelector('.kb-gate') && counts) {
      var gate = doc.createElement('div');
      gate.className = 'kb-gate';
      [['Articles', counts.articles],
       ['Sections', Object.keys(counts.sections || {}).length]].forEach(function (pair) {
        if (!pair[1]) return;
        var cell = doc.createElement('div');
        var value = doc.createElement('b');
        value.textContent = String(pair[1]);
        var label = doc.createElement('span');
        label.textContent = pair[0];
        cell.appendChild(value);
        cell.appendChild(label);
        gate.appendChild(cell);
      });
      if (gate.childElementCount) hero.appendChild(gate);
    }

  }

  function decorateHeroField(doc) {
    var hero = doc.querySelector('.md-typeset .hero-banner');
    if (!hero) return;
    var canvas = hero.querySelector('.kb-field');
    if (!canvas) {
      canvas = doc.createElement('canvas');
      canvas.className = 'kb-field';
      canvas.setAttribute('aria-hidden', 'true');
      hero.insertBefore(canvas, hero.firstChild);
    }
    startField(canvas);
  }

  /* Hairline tick marks that drift like a plotting instrument settling.
     Ambient motion is confined to the hero — never behind running prose. */
  function startField(canvas) {
    if (fieldStop) { fieldStop(); fieldStop = null; }

    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    var marks = [];
    var raf = null;
    var t = 0;
    var alive = true;

    function markColor() {
      var v = getComputedStyle(document.body).getPropertyValue('--kb-mark').trim();
      return v || 'rgba(92,100,136,0.3)';
    }

    function size() {
      var r = canvas.getBoundingClientRect();
      if (!r.width || !r.height) return false;
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(r.width * dpr);
      canvas.height = Math.round(r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      marks = [];
      var step = 44;
      for (var x = 0; x * step < r.width + step; x++) {
        for (var y = 0; y * step < r.height + step; y++) {
          marks.push({ x: x * step + 14, y: y * step + 14, p: x * 0.7 + y * 1.3 });
        }
      }
      return true;
    }

    function paint() {
      var r = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, r.width, r.height);
      ctx.strokeStyle = markColor();
      ctx.lineWidth = 1;
      var still = calm.matches;
      for (var i = 0; i < marks.length; i++) {
        var m = marks[i];
        var dy = still ? 0 : Math.sin(t * 0.6 + m.p) * 2.4;
        var len = 4 + (still ? 0 : Math.cos(t * 0.4 + m.p) * 1.2);
        ctx.beginPath();
        ctx.moveTo(m.x - len, m.y + dy);
        ctx.lineTo(m.x + len, m.y + dy);
        ctx.stroke();
      }
    }

    function loop() {
      if (!alive) return;
      t += 0.016;
      paint();
      raf = window.requestAnimationFrame(loop);
    }

    function begin() {
      if (!size()) return;
      if (calm.matches) { paint(); return; }
      if (raf) window.cancelAnimationFrame(raf);
      loop();
    }

    function onResize() { begin(); }
    window.addEventListener('resize', onResize);
    calm.addEventListener('change', begin);
    begin();

    fieldStop = function () {
      alive = false;
      if (raf) window.cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      calm.removeEventListener('change', begin);
    };
  }

  function apply() {
    try {
      decorateRail(document);
      loadCounts().then(function (counts) {
        try {
          decorateTabs(document, counts);
          buildReadout(document, counts);
          decorateHero(document, counts);
        } catch (e) {
          if (window.console) console.warn('[kb-apparatus] counts', e);
        }
      });
      // the hero canvas must not wait on a network round-trip
      decorateHeroField(document);
    } catch (e) {
      // never let the apparatus layer break the page content
      if (window.console) console.warn('[kb-apparatus]', e);
    }
  }

  /* ── collapsed list: reveal when linked into ─────────────── */
  /* 分區索引把完整清單收進 <details>，但目錄仍列出裡面的小標。若不處理，
     點目錄或從搜尋跳進去時 details 是關的，目標既看不到也捲不到。 */
  function revealTarget(doc) {
    var hash = decodeURIComponent(window.location.hash || '').slice(1);
    if (!hash) return;
    var target = doc.getElementById(hash);
    if (!target) return;
    var d = target.closest('details');
    while (d) { d.open = true; d = d.parentElement && d.parentElement.closest('details'); }
    target.scrollIntoView({ block: 'start' });
  }

  if (typeof window.document$ !== 'undefined' && window.document$ && window.document$.subscribe) {
    window.document$.subscribe(function (doc) { apply(doc); revealTarget(doc); });
    window.addEventListener('hashchange', function () { revealTarget(document); });
  } else if (document.readyState !== 'loading') {
    apply();
  } else {
    document.addEventListener('DOMContentLoaded', apply);
  }
})();
