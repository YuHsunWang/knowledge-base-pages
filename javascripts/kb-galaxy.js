/* Knowledge Galaxy — one lazy, zoomable canvas from domains to articles. */
(function () {
  'use strict';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var HASH_PREFIX = 'kg=';
  var STAR_COUNT = 54;
  var scriptUrl = document.currentScript && document.currentScript.src;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var coarsePointer = window.matchMedia('(hover: none), (pointer: coarse)');
  var mobileLayout = window.matchMedia('(max-width: 44rem)');
  var mapCache = new Map();
  var activeCleanup = null;
  var activeHost = null;
  var pendingFocus = null;
  var failureLogged = false;

  function siteBase() {
    var base = document.querySelector('base');
    if (base && base.href) return base.href;
    if (scriptUrl) return new URL('../', scriptUrl).href;
    return new URL('./', window.location.href).href;
  }

  function span(className, text) {
    var element = document.createElement('span');
    element.className = className;
    if (text !== undefined && text !== null) element.textContent = text;
    return element;
  }

  function isCoordinate(value) {
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
  }

  function pointFor(node, layout) {
    return layout === 'mobile' && node.mobile ? node.mobile : node;
  }

  function validateGalaxy(data) {
    if (!data || typeof data !== 'object' || typeof data.id !== 'string' ||
        typeof data.title !== 'string' || !['domain-selector', 'region-index'].includes(data.mode) ||
        !data.center || typeof data.center.label !== 'string' || !Array.isArray(data.regions)) {
      throw new Error('Invalid galaxy data shape.');
    }
    var ids = new Set();
    data.regions.forEach(function (region) {
      var mobile = region && region.mobile;
      if (!region || typeof region.id !== 'string' || !region.id || ids.has(region.id) ||
          typeof region.label !== 'string' || !region.label || typeof region.href !== 'string' ||
          typeof region.description !== 'string' || !isCoordinate(region.x) || !isCoordinate(region.y) ||
          (mobile && (!isCoordinate(mobile.x) || !isCoordinate(mobile.y))) ||
          !['major', 'medium'].includes(region.size) || !['domain', 'satellite'].includes(region.kind)) {
        throw new Error('Invalid galaxy region.');
      }
      ids.add(region.id);
    });
    if (data.mode === 'region-index') {
      if (!Array.isArray(data.edges)) throw new Error('Invalid galaxy edges.');
      data.edges.forEach(function (edge) {
        if (!edge || !ids.has(edge.from) || !ids.has(edge.to) || edge.from === edge.to ||
            (edge.style !== undefined && edge.style !== 'dashed')) {
          throw new Error('Invalid galaxy edge.');
        }
      });
    }
    return data;
  }

  function normalizeMap(raw, url) {
    var galaxy = validateGalaxy(raw && raw.galaxy ? raw.galaxy : raw);
    var bundle = { galaxy: galaxy, url: url, items: [], itemById: {} };
    if (galaxy.mode === 'region-index') {
      if (!Array.isArray(raw.items)) throw new Error('Missing galaxy article items.');
      raw.items.forEach(function (item) {
        if (!item || typeof item.id !== 'string' || !item.id || bundle.itemById[item.id] ||
            typeof item.label !== 'string' || typeof item.href !== 'string' ||
            (item.step !== null && item.step !== undefined && typeof item.step !== 'string')) {
          throw new Error('Invalid galaxy article item.');
        }
        bundle.items.push(item);
        bundle.itemById[item.id] = item;
      });
      galaxy.regions.forEach(function (region) {
        if (!Array.isArray(region.members) || region.members.some(function (id) { return !bundle.itemById[id]; })) {
          throw new Error('Invalid galaxy article membership.');
        }
      });
      bundle.domain = galaxy.host.split('/')[0];
      bundle.articleBase = new URL(galaxy.host.replace(/index\.md$/, ''), siteBase()).href;
    }
    return bundle;
  }

  function loadMap(source) {
    var url = new URL(source, siteBase()).href;
    if (!mapCache.has(url)) {
      mapCache.set(url, fetch(url).then(function (response) {
        if (!response.ok) throw new Error('Galaxy data request failed: ' + response.status);
        return response.json();
      }).then(function (raw) { return normalizeMap(raw, url); }).catch(function (error) {
        mapCache.delete(url);
        throw error;
      }));
    }
    return mapCache.get(url);
  }

  function seeded(seed) {
    var state = seed >>> 0;
    return function () {
      state = (state * 1664525 + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }

  function hashString(value) {
    var hash = 2166136261;
    for (var i = 0; i < value.length; i++) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function buildStarfield(camera) {
    var random = seeded(0x5eed);
    var fragment = document.createDocumentFragment();
    for (var i = 0; i < STAR_COUNT; i++) {
      var star = span('kb-galaxy-star');
      var weight = random();
      star.style.setProperty('--star-x', (random() * 100).toFixed(2) + '%');
      star.style.setProperty('--star-y', (random() * 100).toFixed(2) + '%');
      star.style.setProperty('--star-size', (0.9 + weight * 1.7).toFixed(2) + 'px');
      star.style.setProperty('--star-opacity', (0.16 + weight * 0.44).toFixed(2));
      star.style.setProperty('--star-period', (5.5 + random() * 7).toFixed(2) + 's');
      star.style.setProperty('--star-delay', (random() * -9).toFixed(2) + 's');
      star.setAttribute('aria-hidden', 'true');
      fragment.appendChild(star);
    }
    camera.appendChild(fragment);
  }

  function articleNodes(bundle, region) {
    var desktopSlots = [
      { x: 0.25, y: 0.15 }, { x: 0.75, y: 0.15 },
      { x: 0.86, y: 0.39 }, { x: 0.84, y: 0.69 },
      { x: 0.65, y: 0.84 }, { x: 0.35, y: 0.84 },
      { x: 0.16, y: 0.69 }, { x: 0.14, y: 0.39 }
    ];
    var seed = hashString(bundle.domain + '/' + region.id);
    var offset = seed % desktopSlots.length;
    var reverse = Boolean(seed & 1);
    return region.members.map(function (id, index) {
      var item = bundle.itemById[id];
      var slotIndex = reverse ? offset - index : offset + index;
      var point = desktopSlots[(slotIndex + desktopSlots.length * 2) % desktopSlots.length];
      var mobileIndex = reverse ? index ^ 1 : index;
      var mobile = { x: mobileIndex % 2 ? 0.73 : 0.27, y: 0.12 + Math.floor(index / 2) * 0.24 };
      return {
        id: item.id,
        label: item.label,
        href: new URL(item.href, bundle.articleBase).href,
        description: item.note || (item.fresh && item.fresh.label) || '',
        freshness: item.fresh && item.fresh.label,
        step: item.step,
        x: point.x,
        y: point.y,
        mobile: mobile,
        size: 'medium',
        kind: 'satellite',
        article: true
      };
    });
  }

  function buildLinks(camera, nodes, edges, layout) {
    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'kb-galaxy-links');
    svg.setAttribute('viewBox', '0 0 1 1');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('aria-hidden', 'true');
    svg.dataset.layout = layout;
    var points = {};
    var byNode = {};
    nodes.forEach(function (node) {
      points[node.id] = pointFor(node, layout);
      byNode[node.id] = [];
    });
    var links = edges || nodes.map(function (node) { return { to: node.id, style: 'dashed' }; });
    links.forEach(function (edge) {
      var from = edge.from ? points[edge.from] : { x: 0.5, y: 0.5 };
      var to = points[edge.to];
      var line = document.createElementNS(SVG_NS, 'line');
      line.setAttribute('class', 'kb-galaxy-link');
      line.setAttribute('x1', String(from.x));
      line.setAttribute('y1', String(from.y));
      line.setAttribute('x2', String(to.x));
      line.setAttribute('y2', String(to.y));
      if (edge.style === 'dashed') line.dataset.style = 'dashed';
      svg.appendChild(line);
      if (edge.from) byNode[edge.from].push(line);
      byNode[edge.to].push(line);
    });
    camera.appendChild(svg);
    return byNode;
  }

  function buildCentre(camera, label) {
    var centre = span('kb-galaxy-center');
    centre.setAttribute('aria-hidden', 'true');
    centre.appendChild(span('kb-galaxy-center__bloom'));
    centre.appendChild(span('kb-galaxy-center__orbit-2'));
    centre.appendChild(span('kb-galaxy-center__orbit'));
    centre.appendChild(span('kb-galaxy-center__core'));
    centre.appendChild(span('kb-galaxy-center__label', label));
    camera.appendChild(centre);
  }

  function stateHash(state) {
    if (state.level === 0) return '';
    return '#' + HASH_PREFIX + state.domain + (state.level === 2 ? '/' + state.region : '');
  }

  function parseLocation(seedDomain) {
    var raw = window.location.hash.slice(1);
    if (!raw.startsWith(HASH_PREFIX)) return { level: seedDomain ? 1 : 0, domain: seedDomain || null };
    var parts = raw.slice(HASH_PREFIX.length).split('/');
    if (!parts[0] || parts.length > 2 || (seedDomain && parts[0] !== seedDomain)) return null;
    return parts.length === 2 && parts[1]
      ? { level: 2, domain: parts[0], region: parts[1] }
      : { level: 1, domain: parts[0] };
  }

  function historyState(state) {
    var next = Object.assign({}, window.history.state || {});
    next.kbGalaxy = { level: state.level, domain: state.domain || null, region: state.region || null };
    return next;
  }

  function replaceHistory(state, url) {
    window.history.replaceState(historyState(state), '', url === undefined ? stateHash(state) : url);
  }

  function pushHistory(state) {
    window.history.pushState(historyState(state), '', stateHash(state));
  }

  function primeDeepHistory(state, seedDomain) {
    if (state.level <= (seedDomain ? 1 : 0) || (window.history.state && window.history.state.kbGalaxy)) {
      replaceHistory(state, window.location.href);
      return;
    }
    var base = new URL(window.location.href);
    base.hash = '';
    var seed = seedDomain ? { level: 1, domain: seedDomain } : { level: 0, domain: null };
    replaceHistory(seed, base.href);
    if (!seedDomain && state.level === 2) pushHistory({ level: 1, domain: state.domain });
    pushHistory(state);
  }

  function showShell(host, failed) {
    host.replaceChildren();
    host.classList.add('kb-galaxy-scope');
    buildStarfield(host);
    var link = document.createElement('a');
    link.className = 'kb-galaxy__fallback';
    link.href = '#learning-paths';
    link.textContent = failed ? '地圖載入失敗 · 前往文章清單 ↓' : '前往文章清單 ↓';
    link.addEventListener('click', function (event) {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
          event.shiftKey || event.altKey) return;
      var target = document.getElementById('learning-paths');
      if (!target) return;
      event.preventDefault();
      event.stopPropagation();
      window.history.replaceState(window.history.state, '', link.href);
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      target.scrollIntoView();
    });
    host.appendChild(link);
  }

  function fail(host, error) {
    if (!host.isConnected || document.querySelector('[data-kbgalaxy]') !== host) return;
    showShell(host, true);
    host.classList.remove('is-selecting');
    delete host.dataset.ready;
    delete host.dataset.level;
    document.documentElement.classList.remove('kb-galaxy-ready');
    if (!failureLogged && window.console) {
      failureLogged = true;
      console.warn('[kb-galaxy] Falling back to static navigation.', error);
    }
  }

  function createHeaderController(host) {
    var header = document.querySelector('.md-header');
    if (!header) return function () {};
    var frame = 0;
    var pointerY = null;
    var passive = { passive: true };

    /* Hysteresis, and the reason for it: the revealed header is as tall as the
       whole plate chrome, so a single threshold at headerHeight swallowed
       .kb-galaxy__back at y 15-59. Aiming for that button crossed the
       threshold first, the header dropped over it, and the pointer could
       never reach it — the button was dead to the mouse while still working
       for Tab and Esc. Arming only at the very top edge keeps the button
       clear; the wider release threshold then keeps the header in place while
       the pointer travels down into it. */
    var ARM_BAND = 10;

    function update() {
      frame = 0;
      var headerHeight = header.getBoundingClientRect().height;
      var revealed = header.classList.contains('kb-galaxy-header--revealed');
      var pastCanvas = host.getBoundingClientRect().bottom <= headerHeight;
      var focusWithin = header.contains(document.activeElement);
      var band = revealed ? headerHeight : ARM_BAND;
      var pointerNearTop = pointerY !== null && pointerY <= band;
      header.classList.toggle(
        'kb-galaxy-header--revealed',
        pastCanvas || focusWithin || pointerNearTop
      );
    }

    function schedule() {
      if (!frame) frame = window.requestAnimationFrame(update);
    }

    function onPointerMove(event) {
      pointerY = event.clientY;
      schedule();
    }

    window.addEventListener('scroll', schedule, passive);
    window.addEventListener('resize', schedule, passive);
    window.addEventListener('pointermove', onPointerMove, passive);
    header.addEventListener('focusin', schedule, passive);
    header.addEventListener('focusout', schedule, passive);
    schedule();

    return function () {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      window.removeEventListener('pointermove', onPointerMove);
      header.removeEventListener('focusin', schedule);
      header.removeEventListener('focusout', schedule);
      header.classList.remove('kb-galaxy-header--revealed');
    };
  }

  function createController(host, initialBundle) {
    var seedDomain = initialBundle.galaxy.mode === 'region-index' ? initialBundle.domain : null;
    var homeBundle = seedDomain ? null : initialBundle;
    var current = null;
    var currentCamera = null;
    var currentEntries = [];
    var transitioning = false;
    var disposed = false;
    var live = span('kb-galaxy-live');
    live.setAttribute('aria-live', 'polite');
    live.setAttribute('aria-atomic', 'true');

    function homeRegion(domain) {
      return homeBundle && homeBundle.galaxy.regions.find(function (region) {
        return region.id === domain || region.href.replace(/\/$/, '') === domain;
      });
    }

    function sectionBundle(domain) {
      if (initialBundle.domain === domain) return Promise.resolve(initialBundle);
      var region = homeRegion(domain);
      if (!region || !region.sectionMap) return Promise.reject(new Error('Domain has no section map: ' + domain));
      return loadMap(region.sectionMap);
    }

    function resolveView(state) {
      if (state.level === 0) {
        if (!homeBundle) return Promise.reject(new Error('L0 is not hosted on this page.'));
        return Promise.resolve({
          title: homeBundle.galaxy.title,
          centre: homeBundle.galaxy.center.label,
          nodes: homeBundle.galaxy.regions,
          edges: null,
          unit: 'domains'
        });
      }
      return sectionBundle(state.domain).then(function (bundle) {
        if (state.level === 1) {
          return {
            title: bundle.galaxy.title,
            centre: bundle.galaxy.center.label,
            nodes: bundle.galaxy.regions,
            edges: bundle.galaxy.edges,
            unit: 'regions',
            bundle: bundle
          };
        }
        var region = bundle.galaxy.regions.find(function (entry) { return entry.id === state.region; });
        if (!region) throw new Error('Unknown galaxy region: ' + state.region);
        return {
          title: bundle.galaxy.title + ' · ' + region.label,
          centre: region.label,
          nodes: articleNodes(bundle, region),
          edges: null,
          unit: 'articles',
          bundle: bundle,
          region: region
        };
      });
    }

    function announce(view) {
      var labels = { domains: '領域', regions: '主題區', articles: '篇文章' };
      live.textContent = '';
      window.requestAnimationFrame(function () {
        if (!disposed) live.textContent = view.title + ' · ' + view.nodes.length + ' ' + labels[view.unit];
      });
    }

    function nextStateFor(node, state) {
      if (state.level === 0 && node.sectionMap) {
        return { level: 1, domain: node.href.replace(/\/$/, '') };
      }
      if (state.level === 1) return { level: 2, domain: state.domain, region: node.id };
      return null;
    }

    function buildChrome(galaxy, view, state) {
      if (state.level > 0) {
        var back = document.createElement('button');
        back.type = 'button';
        back.className = 'kb-galaxy__back';
        back.textContent = '← 返回上一層';
        back.setAttribute('aria-label', '返回上一層');
        back.addEventListener('click', function (event) {
          event.preventDefault();
          event.stopPropagation();
          zoomOut();
        });
        galaxy.appendChild(back);
      }
      var title = span('kb-galaxy__title', 'L' + state.level + ' · ' + view.title);
      title.setAttribute('aria-hidden', 'true');
      galaxy.appendChild(title);
      var hint = span('kb-galaxy__hint', view.nodes.length + ' ' + view.unit + ' · Enter / Space · Esc');
      hint.setAttribute('aria-hidden', 'true');
      galaxy.appendChild(hint);
      ['tl', 'tr', 'bl', 'br'].forEach(function (corner) {
        var mark = span('kb-galaxy__reg');
        mark.dataset.corner = corner;
        mark.setAttribute('aria-hidden', 'true');
        galaxy.appendChild(mark);
      });
    }

    function focusAfterChange(previous, state, entries) {
      var id = null;
      if (pendingFocus && pendingFocus.level === state.level && pendingFocus.expires > Date.now()) {
        id = pendingFocus.id;
      } else if (previous && state.level < previous.level) {
        id = state.level === 0 ? previous.domain : previous.region;
      }
      var target = entries.find(function (entry) {
        return entry.node.id === id || entry.node.href.replace(/\/$/, '') === id;
      }) || entries[0];
      if (target) target.element.focus({ preventScroll: true });
    }

    function renderResolved(state, view, previous, shouldFocus) {
      if (disposed) return;
      var galaxy = document.createElement('div');
      galaxy.className = 'kb-galaxy';
      galaxy.dataset.level = 'L' + state.level;
      galaxy.setAttribute('role', 'navigation');
      galaxy.setAttribute('aria-label', view.title + ' Knowledge Galaxy');
      buildChrome(galaxy, view, state);
      var camera = document.createElement('div');
      camera.className = 'kb-galaxy-camera';
      galaxy.appendChild(camera);
      buildStarfield(camera);
      var desktopLinks = buildLinks(camera, view.nodes, view.edges, 'desktop');
      var mobileLinks = buildLinks(camera, view.nodes, view.edges, 'mobile');
      buildCentre(camera, view.centre);
      var entries = [];

      view.nodes.forEach(function (node) {
        var zoomState = nextStateFor(node, state);
        var anchor = document.createElement('a');
        anchor.className = 'kb-galaxy-node' + (node.article ? ' kb-galaxy-node--article' : '');
        anchor.href = node.article ? node.href : (zoomState ? stateHash(zoomState) : new URL(node.href, siteBase()).href);
        anchor.dataset.nodeId = node.id;
        anchor.dataset.kind = node.kind;
        anchor.dataset.size = node.size;
        anchor.setAttribute('aria-label', node.label +
          (node.count !== undefined ? ', ' + node.count + ' 篇文章' : '') +
          (node.step ? ', 閱讀步驟 ' + node.step : '') + ': ' + node.description);
        anchor.style.setProperty('--node-x', (node.x * 100) + '%');
        anchor.style.setProperty('--node-y', (node.y * 100) + '%');
        var mobilePoint = pointFor(node, 'mobile');
        anchor.style.setProperty('--node-mobile-x', (mobilePoint.x * 100) + '%');
        anchor.style.setProperty('--node-mobile-y', (mobilePoint.y * 100) + '%');
        anchor.appendChild(span('kb-galaxy-node__halo'));
        anchor.appendChild(span('kb-galaxy-node__ring'));
        [0, 90, 180, 270].forEach(function (angle) {
          var tick = span('kb-galaxy-node__tick');
          tick.style.setProperty('--tick-angle', angle + 'deg');
          anchor.appendChild(tick);
        });
        anchor.appendChild(span('kb-galaxy-node__core'));
        anchor.appendChild(span('kb-galaxy-node__label', node.label));
        if (node.count !== undefined) anchor.appendChild(span('kb-galaxy-node__count', node.count + ' 篇'));
        if (node.step) anchor.appendChild(span('kb-galaxy-node__step', node.step));
        anchor.appendChild(span('kb-galaxy-node__note', node.description));
        camera.appendChild(anchor);
        var entry = { element: anchor, node: node, point: pointFor(node, mobileLayout.matches ? 'mobile' : 'desktop') };
        entries.push(entry);

        function light(on) {
          desktopLinks[node.id].concat(mobileLinks[node.id]).forEach(function (line) {
            line.classList.toggle('is-lit', on);
          });
        }
        anchor.addEventListener('pointerenter', function () { light(true); });
        anchor.addEventListener('pointerleave', function () { if (!transitioning) light(false); });
        anchor.addEventListener('focus', function () { light(true); });
        anchor.addEventListener('blur', function () { if (!transitioning) light(false); });
        if (zoomState) {
          anchor.addEventListener('click', function (event) {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
                event.shiftKey || event.altKey) return;
            event.preventDefault();
            event.stopPropagation();
            changeLevel(zoomState, entry, true, true);
          });
          anchor.addEventListener('keydown', function (event) {
            if (event.key !== ' ') return;
            event.preventDefault();
            event.stopPropagation();
            changeLevel(zoomState, entry, true, true);
          });
        } else if (node.article) {
          /* Dim the plate behind the picked star while the page transition
             fades out, so leaving the galaxy reads as travelling into that
             article rather than as the map vanishing. */
          anchor.addEventListener('click', function (event) {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
                event.shiftKey || event.altKey) return;
            host.classList.add('is-selecting');
            anchor.classList.add('kb-galaxy-node--diving');
          });
          /* Space activates the anchor itself. Assigning location.href here
             forced a full document load and dropped out of navigation.instant,
             which Enter on the same star never did. */
          anchor.addEventListener('keydown', function (event) {
            if (event.key !== ' ') return;
            event.preventDefault();
            anchor.click();
          });
        }
      });

      host.replaceChildren(galaxy, live);
      host.classList.add('kb-galaxy-scope');
      host.dataset.ready = '1';
      host.dataset.level = 'L' + state.level;
      host.dataset.nodeCount = String(view.nodes.length);
      document.documentElement.classList.add('kb-galaxy-ready');
      current = state;
      currentCamera = camera;
      currentEntries = entries;
      transitioning = false;
      announce(view);
      var hasPendingFocus = pendingFocus && pendingFocus.level === state.level && pendingFocus.expires > Date.now();
      if (shouldFocus || hasPendingFocus) window.requestAnimationFrame(function () {
        window.setTimeout(function () {
          focusAfterChange(previous, state, entries);
          window.setTimeout(function () {
            focusAfterChange(previous, state, entries);
          }, 500);
        }, 0);
      });
    }

    function waitForCamera(entry, deeper) {
      if (reducedMotion.matches || !currentCamera) return Promise.resolve();
      var duration = coarsePointer.matches ? 380 : 620;
      host.style.setProperty('--galaxy-duration', duration + 'ms');
      if (entry) {
        currentCamera.style.setProperty('--camera-x', ((0.5 - entry.point.x) * 100) + '%');
        currentCamera.style.setProperty('--camera-y', ((0.5 - entry.point.y) * 100) + '%');
        entry.element.classList.add('is-selected');
      }
      host.classList.add('is-selecting');
      return new Promise(function (resolve) {
        window.requestAnimationFrame(function () {
          currentCamera.classList.add(deeper ? 'is-zoomed' : 'is-zoomed-out');
        });
        window.setTimeout(resolve, duration + 40);
      });
    }

    function changeLevel(next, trigger, push, animate) {
      if (transitioning || !next) return;
      transitioning = true;
      var previous = current;
      var deeper = !previous || next.level > previous.level;
      Promise.all([
        resolveView(next),
        animate ? waitForCamera(trigger, deeper) : Promise.resolve()
      ]).then(function (results) {
        if (disposed) return;
        if (push) pushHistory(next);
        host.classList.remove('is-selecting');
        renderResolved(next, results[0], previous, Boolean(previous));
      }).catch(function (error) {
        if (!disposed) fail(host, error);
      });
    }

    function zoomOut() {
      if (!current) return;
      var seedLevel = seedDomain ? 1 : 0;
      if (current.level <= seedLevel) {
        if (seedDomain) window.location.href = siteBase();
        return;
      }
      pendingFocus = {
        level: current.level - 1,
        id: current.level === 2 ? current.region : current.domain,
        expires: Date.now() + 2000
      };
      window.history.back();
    }

    function onPopState() {
      var next = parseLocation(seedDomain);
      if (!next) {
        window.location.href = siteBase() + window.location.hash;
        return;
      }
      if (current) {
        pendingFocus = {
          level: next.level,
          id: next.level < current.level
            ? (next.level === 0 ? current.domain : current.region)
            : null,
          expires: Date.now() + 2000
        };
      }
      var returnEntry = null;
      if (current && next.level > current.level) {
        var id = next.level === 1 ? next.domain : next.region;
        returnEntry = currentEntries.find(function (entry) { return entry.node.id === id; }) || null;
      }
      changeLevel(next, returnEntry, false, true);
    }

    function onKeyDown(event) {
      if (event.key !== 'Escape' || event.defaultPrevented) return;
      event.preventDefault();
      zoomOut();
    }

    var initial = parseLocation(seedDomain);
    if (!initial) {
      window.location.replace(siteBase() + window.location.hash);
      return function () { disposed = true; };
    }
    primeDeepHistory(initial, seedDomain);
    window.addEventListener('popstate', onPopState);
    document.addEventListener('keydown', onKeyDown);
    changeLevel(initial, null, false, false);

    return function () {
      disposed = true;
      window.removeEventListener('popstate', onPopState);
      document.removeEventListener('keydown', onKeyDown);
      document.documentElement.classList.remove('kb-galaxy-ready');
    };
  }

  function initKbGalaxy() {
    var host = document.querySelector('[data-kbgalaxy]');
    if (host && host === activeHost && host.dataset.kbGalaxyReady === '1') {
      document.documentElement.classList.toggle('kb-galaxy-ready', host.dataset.ready === '1');
      return;
    }
    if (activeCleanup) {
      activeCleanup();
      activeCleanup = null;
    }
    activeHost = null;
    if (!host) return;
    activeHost = host;
    host.dataset.kbGalaxyReady = '1';
    showShell(host, false);
    var disposeHeader = createHeaderController(host);
    var disposeController = null;
    var disposed = false;
    activeCleanup = function () {
      disposed = true;
      disposeHeader();
      if (disposeController) disposeController();
    };
    loadMap(host.dataset.kbgalaxy).then(function (bundle) {
      if (disposed || !host.isConnected || document.querySelector('[data-kbgalaxy]') !== host) return;
      disposeController = createController(host, bundle);
    }).catch(function (error) {
      if (!disposed) fail(host, error);
    });
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(initKbGalaxy);
  } else {
    document.addEventListener('DOMContentLoaded', initKbGalaxy);
  }
})();
