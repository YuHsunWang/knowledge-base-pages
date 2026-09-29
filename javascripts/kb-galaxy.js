/* Knowledge Galaxy — one lazy, zoomable canvas from domains to articles. */
(function () {
  'use strict';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var HASH_PREFIX = 'kg=';
  var STAR_COUNT = 90;
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

  /* ── World geometry ───────────────────────────────────────────────
     Every layer lives in one coordinate space measured in L0 pixels.
     Each node owns a box with the viewport's aspect ratio; zooming to a
     layer means fitting that node's box to the viewport. A domain box
     holds its regions at their authored layout positions, and a region
     box holds its articles, so the camera flies into the very stars
     that were already visible one layer up. */
  var DOMAIN_SCALE = 0.3;
  var REGION_SCALE = 0.14;
  var DUST_COUNT = 280;

  function fitBox(cx, cy, w, h) {
    return { x: cx, y: cy, w: w, h: h };
  }

  function childBox(parent, point, scale) {
    return fitBox(parent.x + (point.x - 0.5) * parent.w, parent.y + (point.y - 0.5) * parent.h,
      parent.w * scale, parent.h * scale);
  }

  /* Articles sit on concentric ellipses, clockwise from the top in reading
     order. Each ring holds as many stars as its perimeter has room for at
     the article layer, so a new article never lands on an old one. A phone
     is too narrow for captions around a ring: there the stars run down one
     gently curved arm with the captions beside them. */
  function ringLayout(count, vw, vh, mobile) {
    if (count === 1) return [{ x: 0.5, y: 0.5 }];
    if (mobile) {
      // ponytail: one column; past ~20 articles per region the rows get tight on a phone.
      return Array.from({ length: count }, function (_, i) {
        var t = i / (count - 1);
        return { x: 0.1 + 0.16 * Math.sin(Math.PI * t), y: 0.16 + t * 0.74 };
      });
    }
    var rx = 0.34;
    var ry = 0.33;
    var gap = 150;
    var points = [];
    var remaining = count;
    for (var ring = 0; remaining > 0; ring++) {
      var k = Math.pow(0.62, ring);
      var a = rx * vw * k;
      var b = ry * vh * k;
      var room = Math.max(1, Math.floor(2 * Math.PI * Math.sqrt((a * a + b * b) / 2) / gap));
      // ponytail: rings past the third take everything left; labels may crowd past ~60 articles per region.
      var take = ring >= 2 ? remaining : Math.min(remaining, room);
      for (var i = 0; i < take; i++) {
        var angle = -Math.PI / 2 + (i + ring * 0.5) * 2 * Math.PI / take;
        points.push({ x: 0.5 + Math.cos(angle) * rx * k, y: 0.5 + Math.sin(angle) * ry * k });
      }
      remaining -= take;
    }
    return points;
  }

  /* Two-armed spiral dust in the unit disc, tilted and turned per domain so
     no two galaxies look stamped from one template. */
  function spiralDust(seed) {
    var random = seeded(seed);
    var turn = random() * Math.PI * 2;
    var tilt = 0.55 + random() * 0.2;
    var cos = Math.cos(turn);
    var sin = Math.sin(turn);
    var dust = [];
    for (var i = 0; i < DUST_COUNT; i++) {
      var bulge = i % 4 === 0;
      var t = bulge ? Math.abs(random() - random()) * 0.35 : Math.pow(random(), 0.8);
      var angle = bulge ? random() * Math.PI * 2 : (i % 2) * Math.PI + t * Math.PI * 2.6 + (random() - 0.5) * 0.7;
      var radius = bulge ? t : 0.08 + t * 0.9 + (random() - 0.5) * 0.08;
      var u = Math.cos(angle) * radius;
      var v = Math.sin(angle) * radius * tilt;
      dust.push({
        x: u * cos - v * sin,
        y: u * sin + v * cos,
        size: 0.5 + random() * random() * 1.3,
        alpha: (bulge ? 0.45 : 0.32) + random() * 0.45,
        blue: random() < 0.55
      });
    }
    return dust;
  }

  function buildWorld(homeBundle, sections, seedDomain, vw, vh, mobile) {
    var layout = mobile ? 'mobile' : 'desktop';
    var domains = [];
    function addDomain(key, node, box, bundle) {
      var domain = { key: key, node: node, box: box, dust: spiralDust(hashString(key)), regions: [] };
      if (bundle) {
        domain.bornAt = bundle.bornAt;
        bundle.galaxy.regions.forEach(function (region) {
          var regionBox = childBox(box, pointFor(region, layout), REGION_SCALE);
          var points = ringLayout(region.members.length, vw, vh, mobile);
          domain.regions.push({
            node: region,
            box: regionBox,
            stars: region.members.map(function (id, index) {
              return {
                item: bundle.itemById[id],
                x: regionBox.x + (points[index].x - 0.5) * regionBox.w,
                y: regionBox.y + (points[index].y - 0.5) * regionBox.h
              };
            })
          });
        });
      }
      domains.push(domain);
    }
    if (homeBundle) {
      homeBundle.galaxy.regions.forEach(function (node) {
        var point = pointFor(node, layout);
        var scale = DOMAIN_SCALE * (node.size === 'major' ? 1 : 0.7);
        var key = node.href.replace(/\/$/, '');
        addDomain(key, node, fitBox(point.x * vw, point.y * vh, vw * scale, vh * scale), sections[key]);
      });
    } else {
      addDomain(seedDomain, null, fitBox(vw / 2, vh / 2, vw, vh), sections[seedDomain]);
    }
    return { vw: vw, vh: vh, mobile: mobile, domains: domains };
  }

  function findDomain(world, key) {
    return world.domains.find(function (domain) { return domain.key === key; });
  }

  function findRegion(world, key, id) {
    var domain = findDomain(world, key);
    return domain && domain.regions.find(function (region) { return region.node.id === id; });
  }

  function cameraFor(world, state) {
    var box = fitBox(world.vw / 2, world.vh / 2, world.vw, world.vh);
    if (state.level >= 1) box = findDomain(world, state.domain).box;
    if (state.level === 2) box = findRegion(world, state.domain, state.region).box;
    /* Authored phone layouts run to the plate edge; leave the bottom row
       room for its caption. */
    var room = world.mobile && state.level === 1 ? 0.9 : 1;
    return { x: box.x, y: box.y + (1 - room) * 0.3 * box.h, s: room * world.vw / box.w };
  }

  /* Zoom about the one world point that sits at the same screen position in
     both cameras: the target glides straight to the centre while the scale
     changes geometrically, with no sideways swing. */
  function cameraAt(from, to, t) {
    var s = Math.exp(Math.log(from.s) + (Math.log(to.s) - Math.log(from.s)) * t);
    if (Math.abs(to.s - from.s) < 1e-6) {
      return { x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t, s: s };
    }
    var px = (to.s * to.x - from.s * from.x) / (to.s - from.s);
    var py = (to.s * to.y - from.s * from.y) / (to.s - from.s);
    return { x: px - (px - from.x) * from.s / s, y: py - (py - from.y) * from.s / s, s: s };
  }

  function easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function rgba(hex, alpha) {
    var value = parseInt(hex.replace('#', ''), 16);
    return 'rgba(' + (value >> 16 & 255) + ',' + (value >> 8 & 255) + ',' + (value & 255) + ',' + alpha + ')';
  }

  function glowSprite(hex) {
    var sprite = document.createElement('canvas');
    sprite.width = sprite.height = 64;
    var context = sprite.getContext('2d');
    var gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, rgba(hex, 1));
    gradient.addColorStop(0.25, rgba(hex, 0.35));
    gradient.addColorStop(1, rgba(hex, 0));
    context.fillStyle = gradient;
    context.fillRect(0, 0, 64, 64);
    return sprite;
  }

  function createPainter(canvas, tokens) {
    var context = canvas.getContext('2d');
    var coreGlow = glowSprite(tokens.star);
    var blueGlow = glowSprite(tokens.glow);

    return function paint(world, camera, now) {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var vw = world.vw;
      var vh = world.vh;
      if (canvas.width !== Math.round(vw * dpr) || canvas.height !== Math.round(vh * dpr)) {
        canvas.width = Math.round(vw * dpr);
        canvas.height = Math.round(vh * dpr);
      }
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, vw, vh);
      context.globalCompositeOperation = 'lighter';
      var s = camera.s;
      var starRadius = Math.max(1.3, Math.min(4.2, 1.3 * Math.pow(s, 0.3)));
      var fading = false;

      function sx(x) { return (x - camera.x) * s + vw / 2; }
      function sy(y) { return (y - camera.y) * s + vh / 2; }
      function onScreen(x, y, margin) {
        return x > -margin && y > -margin && x < vw + margin && y < vh + margin;
      }

      world.domains.forEach(function (domain) {
        var box = domain.box;
        var cx = sx(box.x);
        var cy = sy(box.y);
        var radius = 0.5 * Math.min(box.w, box.h) * s;
        if (!onScreen(cx, cy, radius * 2.2)) return;

        /* The glow grows with the galaxy only up to a point; past it the
           core would wash out the clusters it sits among. */
        context.globalAlpha = 0.4;
        var haze = Math.min(radius * 1.9, 420);
        context.drawImage(blueGlow, cx - haze, cy - haze, haze * 2, haze * 2);
        context.globalAlpha = 0.8;
        var core = Math.min(radius * 0.3, 48);
        context.drawImage(coreGlow, cx - core, cy - core, core * 2, core * 2);

        var halfW = 0.5 * box.w * 0.95 * s;
        var halfH = 0.5 * box.h * 0.95 * s;
        domain.dust.forEach(function (mote) {
          var x = cx + mote.x * halfW;
          var y = cy + mote.y * halfH;
          if (!onScreen(x, y, 4)) return;
          context.globalAlpha = mote.alpha;
          context.fillStyle = mote.blue ? tokens.blue : tokens.star;
          context.beginPath();
          context.arc(x, y, mote.size, 0, Math.PI * 2);
          context.fill();
        });

        var arrival = domain.bornAt ? Math.min(1, (now - domain.bornAt) / 600) : 1;
        if (arrival < 1) fading = true;
        domain.regions.forEach(function (region) {
          region.stars.forEach(function (star) {
            var x = sx(star.x);
            var y = sy(star.y);
            if (!onScreen(x, y, 24)) return;
            var glow = starRadius * 5;
            context.globalAlpha = 0.55 * arrival;
            context.drawImage(blueGlow, x - glow, y - glow, glow * 2, glow * 2);
            context.globalAlpha = arrival;
            context.fillStyle = tokens.star;
            context.beginPath();
            context.arc(x, y, starRadius, 0, Math.PI * 2);
            context.fill();
          });
        });
      });
      context.globalAlpha = 1;
      context.globalCompositeOperation = 'source-over';
      return fading;
    };
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
    var sections = {};
    var current = null;
    var currentEntries = [];
    var transitioning = false;
    var disposed = false;
    var world = null;
    var camera = null;
    var frame = 0;
    var flight = null;
    var live = span('kb-galaxy-live');
    live.setAttribute('aria-live', 'polite');
    live.setAttribute('aria-atomic', 'true');

    if (seedDomain) {
      initialBundle.bornAt = 0;
      sections[seedDomain] = initialBundle;
    }

    var galaxy = document.createElement('div');
    galaxy.className = 'kb-galaxy';
    galaxy.setAttribute('role', 'navigation');
    buildStarfield(galaxy);
    var canvas = document.createElement('canvas');
    canvas.className = 'kb-galaxy-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    galaxy.appendChild(canvas);
    var overlay = document.createElement('div');
    overlay.className = 'kb-galaxy-overlay';
    galaxy.appendChild(overlay);

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
    var title = span('kb-galaxy__title');
    title.setAttribute('aria-hidden', 'true');
    var hint = span('kb-galaxy__hint');
    hint.setAttribute('aria-hidden', 'true');
    galaxy.append(back, title, hint);

    var styles = getComputedStyle(host);
    function token(name) { return styles.getPropertyValue(name).trim(); }
    var paint = createPainter(canvas, {
      star: token('--kb-space-star'),
      blue: token('--kb-space-blue'),
      glow: token('--kb-space-glow')
    });

    function measure() {
      var rect = host.getBoundingClientRect();
      world = buildWorld(homeBundle, sections, seedDomain, rect.width, rect.height, mobileLayout.matches);
    }

    function draw() {
      frame = 0;
      if (disposed || !world || !camera) return;
      var now = window.performance.now();
      if (flight) {
        var t = Math.min(1, (now - flight.start) / flight.duration);
        camera = cameraAt(flight.from, flight.to, easeInOut(t));
        if (t >= 1) {
          var done = flight.done;
          flight = null;
          done();
        }
      }
      if (paint(world, camera, now) || flight) requestDraw();
    }

    function requestDraw() {
      if (!frame && !disposed) frame = window.requestAnimationFrame(draw);
    }

    function fly(target) {
      if (reducedMotion.matches || !camera) {
        camera = target;
        requestDraw();
        return Promise.resolve();
      }
      return new Promise(function (resolve) {
        flight = {
          from: camera,
          to: target,
          start: window.performance.now(),
          duration: coarsePointer.matches ? 750 : 1000,
          done: resolve
        };
        requestDraw();
      });
    }

    function adoptSection(bundle) {
      if (disposed || sections[bundle.domain]) return;
      bundle.bornAt = window.performance.now();
      sections[bundle.domain] = bundle;
      measure();
      requestDraw();
    }

    function homeRegion(domain) {
      return homeBundle && homeBundle.galaxy.regions.find(function (region) {
        return region.id === domain || region.href.replace(/\/$/, '') === domain;
      });
    }

    function sectionBundle(domain) {
      if (sections[domain]) return Promise.resolve(sections[domain]);
      var region = homeRegion(domain);
      if (!region || !region.sectionMap) return Promise.reject(new Error('Domain has no section map: ' + domain));
      return loadMap(region.sectionMap).then(function (bundle) {
        adoptSection(bundle);
        return bundle;
      });
    }

    function resolveView(state) {
      if (state.level === 0) {
        if (!homeBundle) return Promise.reject(new Error('L0 is not hosted on this page.'));
        return Promise.resolve({ title: homeBundle.galaxy.title, unit: 'domains' });
      }
      return sectionBundle(state.domain).then(function (bundle) {
        if (state.level === 1) return { title: bundle.galaxy.title, unit: 'regions' };
        var region = bundle.galaxy.regions.find(function (entry) { return entry.id === state.region; });
        if (!region) throw new Error('Unknown galaxy region: ' + state.region);
        return { title: bundle.galaxy.title + ' · ' + region.label, unit: 'articles' };
      });
    }

    /* The clickable layer for one level: where each thing sits in the world,
       how large its hit disc is, and what it says. */
    function layerNodes(state) {
      if (state.level === 0) {
        return world.domains.map(function (domain) {
          return {
            node: domain.node,
            locate: function () {
              var d = findDomain(world, domain.key);
              return { x: d.box.x, y: d.box.y, r: 0.36 * Math.min(d.box.w, d.box.h) };
            }
          };
        });
      }
      var domain = findDomain(world, state.domain);
      if (state.level === 1) {
        return domain.regions.map(function (region) {
          var id = region.node.id;
          return {
            node: Object.assign({ count: region.node.members.length }, region.node),
            locate: function () {
              var r = findRegion(world, state.domain, id);
              var reach = r.stars.reduce(function (most, star) {
                return Math.max(most, Math.hypot(star.x - r.box.x, star.y - r.box.y));
              }, 0);
              return { x: r.box.x, y: r.box.y, r: reach };
            }
          };
        });
      }
      var bundle = sections[state.domain];
      return findRegion(world, state.domain, state.region).stars.map(function (star, index) {
        var item = star.item;
        return {
          node: {
            id: item.id,
            label: item.label,
            href: new URL(item.href, bundle.articleBase).href,
            description: item.note || (item.fresh && item.fresh.label) || '',
            step: item.step,
            article: true
          },
          locate: function () {
            var s = findRegion(world, state.domain, state.region).stars[index];
            return { x: s.x, y: s.y, r: 0 };
          }
        };
      });
    }

    function place(entry) {
      var spot = entry.locate();
      var x = (spot.x - camera.x) * camera.s + world.vw / 2;
      var y = (spot.y - camera.y) * camera.s + world.vh / 2;
      entry.element.style.setProperty('--node-x', x.toFixed(1) + 'px');
      entry.element.style.setProperty('--node-y', y.toFixed(1) + 'px');
      entry.element.style.setProperty('--hit', Math.max(22, spot.r * camera.s + 10).toFixed(1) + 'px');
    }

    function announce(view, count) {
      var labels = { domains: '領域', regions: '主題區', articles: '篇文章' };
      live.textContent = '';
      window.requestAnimationFrame(function () {
        if (!disposed) live.textContent = view.title + ' · ' + count + ' ' + labels[view.unit];
      });
    }

    function nextStateFor(node, state) {
      if (state.level === 0 && node.sectionMap) {
        return { level: 1, domain: node.href.replace(/\/$/, '') };
      }
      if (state.level === 1) return { level: 2, domain: state.domain, region: node.id };
      return null;
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

    function buildNode(item, state, index) {
      var node = item.node;
      var zoomState = nextStateFor(node, state);
      var anchor = document.createElement('a');
      anchor.className = 'kb-galaxy-node' + (node.article ? ' kb-galaxy-node--article' : '');
      anchor.href = node.article ? node.href : (zoomState ? stateHash(zoomState) : new URL(node.href, siteBase()).href);
      anchor.dataset.nodeId = node.id;
      anchor.style.setProperty('--order', String(Math.min(index, 12)));
      anchor.setAttribute('aria-label', node.label +
        (node.count !== undefined ? ', ' + node.count + ' 篇文章' : '') +
        (node.step ? ', 閱讀步驟 ' + node.step : '') + ': ' + node.description);
      anchor.appendChild(span('kb-galaxy-node__ring'));
      var caption = span('kb-galaxy-node__caption');
      if (node.step) caption.appendChild(span('kb-galaxy-node__step', node.step));
      caption.appendChild(span('kb-galaxy-node__label', node.label));
      if (node.count !== undefined) caption.appendChild(span('kb-galaxy-node__count', node.count + ' 篇'));
      if (node.description) caption.appendChild(span('kb-galaxy-node__note', node.description));
      anchor.appendChild(caption);
      var entry = { element: anchor, node: node, locate: item.locate };

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
        /* Dim the rest of the sky behind the picked star while the page
           transition fades out, so leaving reads as travelling into it. */
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
      return entry;
    }

    function renderLayer(state, view, previous, shouldFocus) {
      if (disposed) return;
      var entries = layerNodes(state).map(function (item, index) { return buildNode(item, state, index); });
      entries.forEach(place);
      overlay.replaceChildren.apply(overlay, entries.map(function (entry) { return entry.element; }));
      overlay.classList.remove('is-leaving');
      var level = 'L' + state.level;
      galaxy.dataset.level = level;
      galaxy.setAttribute('aria-label', view.title + ' Knowledge Galaxy');
      back.hidden = state.level === 0;
      title.textContent = view.title;
      hint.textContent = state.level === 2 ? '點星星開啟文章 · Esc 返回' : (state.level ? '點星團放大 · Esc 返回' : '點星系放大');
      if (!galaxy.isConnected) host.replaceChildren(galaxy, live);
      host.classList.add('kb-galaxy-scope');
      host.dataset.ready = '1';
      host.dataset.level = level;
      host.dataset.nodeCount = String(entries.length);
      document.documentElement.classList.add('kb-galaxy-ready');
      current = state;
      currentEntries = entries;
      transitioning = false;
      announce(view, entries.length);
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

    function changeLevel(next, trigger, push, animate) {
      if (transitioning || !next) return;
      transitioning = true;
      var previous = current;
      if (trigger) trigger.element.classList.add('is-selected');
      overlay.classList.add('is-leaving');
      resolveView(next).then(function (view) {
        if (disposed) return null;
        if (!world) measure();
        var target = cameraFor(world, next);
        return (animate ? fly(target) : Promise.resolve()).then(function () {
          if (disposed) return;
          camera = target;
          requestDraw();
          if (push) pushHistory(next);
          host.classList.remove('is-selecting');
          renderLayer(next, view, previous, Boolean(previous));
        });
      }).catch(function (error) {
        if (!disposed) fail(host, error);
      });
    }

    function zoomOut() {
      if (!current || transitioning) return;
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
        returnEntry = currentEntries.find(function (entry) {
          return entry.node.id === id || (entry.node.href || '').replace(/\/$/, '') === id;
        }) || null;
      }
      changeLevel(next, returnEntry, false, true);
    }

    function onKeyDown(event) {
      if (event.key !== 'Escape' || event.defaultPrevented) return;
      event.preventDefault();
      zoomOut();
    }

    var resizeObserver = new ResizeObserver(function () {
      if (disposed || !world) return;
      measure();
      if (current && !flight) camera = cameraFor(world, current);
      currentEntries.forEach(place);
      requestDraw();
    });

    var initial = parseLocation(seedDomain);
    if (!initial) {
      window.location.replace(siteBase() + window.location.hash);
      return function () { disposed = true; };
    }
    primeDeepHistory(initial, seedDomain);
    window.addEventListener('popstate', onPopState);
    document.addEventListener('keydown', onKeyDown);
    resizeObserver.observe(host);
    measure();
    changeLevel(initial, null, false, false);
    /* Fill the other galaxies in the background so the home sky shows real
       clusters. A failed prefetch only leaves that galaxy as dust; the click
       that needs it retries and reports through fail(). */
    if (homeBundle) {
      homeBundle.galaxy.regions.forEach(function (region) {
        if (region.sectionMap) loadMap(region.sectionMap).then(adoptSection, function () {});
      });
    }

    return function () {
      disposed = true;
      if (frame) window.cancelAnimationFrame(frame);
      resizeObserver.disconnect();
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
