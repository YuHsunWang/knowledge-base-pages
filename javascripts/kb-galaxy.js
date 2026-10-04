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
  /* The last layer shown, kept across Material's instant-navigation swaps.
     Going back (Esc, the back control, the browser, or leaving an article)
     makes Material replace the whole galaxy, so the fresh one starts where
     this says the viewer was and flies out from there. Mirrored into
     sessionStorage because a full page load (a new tab, a link Material
     does not intercept) would otherwise forget it. */
  var VIEW_KEY = 'kbGalaxyView';

  function rememberView(view) {
    try {
      if (view) window.sessionStorage.setItem(VIEW_KEY, JSON.stringify(view));
      else window.sessionStorage.removeItem(VIEW_KEY);
    } catch (error) { /* storage blocked: going back just skips the flight */ }
  }

  function recallView() {
    try {
      var view = JSON.parse(window.sessionStorage.getItem(VIEW_KEY));
      return view && view.state && typeof view.state.level === 'number' ? view : null;
    } catch (error) {
      return null;
    }
  }
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

  /* The prose of a section's index page, everything after its plate, with
     links made absolute so they still work when shown on the home page. */
  var textCache = new Map();
  function loadSectionText(domain) {
    var url = new URL(domain + '/', siteBase()).href;
    if (!textCache.has(url)) {
      textCache.set(url, fetch(url).then(function (response) {
        if (!response.ok) throw new Error('Section page request failed: ' + response.status);
        return response.text();
      }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var article = doc.querySelector('.md-content__inner');
        if (!article) throw new Error('Section page has no article: ' + url);
        var plate = article.querySelector(':scope > [data-kbgalaxy]');
        var nodes = Array.prototype.slice.call(article.childNodes);
        if (plate) nodes = nodes.slice(nodes.indexOf(plate) + 1);
        nodes.forEach(function (node) {
          if (!node.querySelectorAll) return;
          [node].concat(Array.prototype.slice.call(node.querySelectorAll('[href],[src]'))).forEach(function (el) {
            ['href', 'src'].forEach(function (attr) {
              var value = el.getAttribute && el.getAttribute(attr);
              if (value && value.charAt(0) !== '#') el.setAttribute(attr, new URL(value, url).href);
            });
          });
        });
        return nodes.map(function (node) { return document.importNode(node, true); });
      }).catch(function (error) {
        textCache.delete(url);
        throw error;
      }));
    }
    return textCache.get(url);
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

  /* Articles in one nav sub-series form one constellation; the loose ones
     share another. Each constellation gets its own share of the plate. */
  function constellations(items) {
    var groups = [];
    var byLabel = {};
    items.forEach(function (item, index) {
      var key = item.cluster || '';
      if (!byLabel[key]) {
        byLabel[key] = { label: item.cluster || null, members: [] };
        groups.push(byLabel[key]);
      }
      byLabel[key].members.push(index);
    });
    return groups;
  }

  /* Stars are laid down by a seeded walk: each one steps off the last at a
     drifting angle, so a constellation reads as a hand-drawn figure yet
     lands in the same place on every visit. A candidate is kept only if
     its caption box clears every caption already placed, which is what
     lets any number of articles share a region without stacking. Works in
     article-layer pixels and returns fractions of the region box. */
  function constellationLayout(items, vw, vh, mobile, seed) {
    var random = seeded(seed);
    var groups = constellations(items);
    var points = new Array(items.length);
    var placed = [];
    var top = 0.17 * vh;
    var bottom = 0.9 * vh;
    var left = 0.07 * vw;
    var right = 0.93 * vw;

    function clear(x, y) {
      return placed.every(function (p) {
        return mobile ? Math.abs(y - p.y) >= 46 : Math.abs(x - p.x) >= 235 || Math.abs(y - p.y) >= 80;
      });
    }

    var segments = [];
    function crosses(ax, ay, bx, by) {
      function side(px, py, qx, qy, rx, ry) { return (qx - px) * (ry - py) - (qy - py) * (rx - px); }
      return segments.some(function (g) {
        if (g[2] === ax && g[3] === ay) return false;
        return side(ax, ay, bx, by, g[0], g[1]) * side(ax, ay, bx, by, g[2], g[3]) < 0 &&
          side(g[0], g[1], g[2], g[3], ax, ay) * side(g[0], g[1], g[2], g[3], bx, by) < 0;
      });
    }

    function put(index, x, y) {
      points[index] = { x: x / vw, y: y / vh };
      placed.push({ x: x, y: y });
    }

    if (mobile) {
      /* A phone has room for captions only beside the stars: each
         constellation runs down its own stretch of one wandering arm. */
      var labelled = groups.filter(function (group) { return group.label; }).length;
      var rowGap = Math.min(64, (bottom - top - 30 * labelled) / Math.max(1, items.length - 1));
      var y = top;
      groups.forEach(function (group) {
        if (group.label) y += 30;
        var x = 0.08 * vw + random() * 0.14 * vw;
        group.members.forEach(function (index) {
          put(index, x, y);
          y += rowGap;
          x = Math.max(0.06 * vw, Math.min(0.34 * vw, x + (random() - 0.5) * 0.18 * vw));
        });
        group.labelAt = { x: 0.06, y: (placed[placed.length - group.members.length].y - 30) / vh };
      });
      return { points: points, groups: groups };
    }

    var total = items.length;
    var x0 = left;
    groups.forEach(function (group) {
      var x1 = x0 + (right - left) * group.members.length / total;
      var cx = (x0 + x1) / 2;
      var cy = (top + bottom) / 2;
      var inside = function (x, y) { return x >= x0 + 60 && x <= x1 - 60 && y >= top && y <= bottom - 50; };
      var px = x0 + 60 + random() * Math.max(1, (x1 - x0) * 0.4 - 60);
      var py = top + 20 + random() * (bottom - top) * 0.35;
      var heading = Math.atan2(cy - py, cx - px);
      group.members.forEach(function (index, step) {
        if (step > 0) {
          var found = false;
          for (var attempt = 0; attempt < 60 && !found; attempt++) {
            var turn = heading + (random() - 0.5) * (2.2 + attempt * 0.08);
            var reach = 170 + random() * 60 + attempt * 2;
            var nx = px + Math.cos(turn) * reach;
            var ny = py + Math.sin(turn) * reach * 0.75;
            /* No near-vertical steps (the line would run down the whole
               caption) and no step that crosses a line already drawn. */
            var steep = attempt < 40 && Math.abs(Math.sin(turn)) > 0.9;
            if (!steep && inside(nx, ny) && clear(nx, ny) && !crosses(px, py, nx, ny)) {
              segments.push([px, py, nx, ny]);
              heading = turn;
              px = nx;
              py = ny;
              found = true;
            }
          }
          for (var jump = 0; jump < 300 && !found; jump++) {
            var jx = x0 + 60 + random() * (x1 - x0 - 120);
            var jy = top + random() * (bottom - 50 - top);
            if (clear(jx, jy)) {
              segments.push([px, py, jx, jy]);
              px = jx;
              py = jy;
              found = true;
            }
          }
          // ponytail: past ~40 articles per region no clear spot is left and stars may crowd; add a page then.
        }
        put(index, px, py);
      });
      var ys = group.members.map(function (index) { return points[index].y * vh; });
      var xs = group.members.map(function (index) { return points[index].x * vw; });
      group.labelAt = {
        x: (Math.min.apply(null, xs) + Math.max.apply(null, xs)) / 2 / vw,
        y: (Math.min.apply(null, ys) - 42) / vh
      };
      x0 = x1;
    });
    /* A walk wanders off-centre; re-centre the whole figure so the region
       caption one layer up sits under the stars rather than beside them. */
    var xs = points.map(function (p) { return p.x; });
    var ys = points.map(function (p) { return p.y; });
    var dx = 0.5 - (Math.min.apply(null, xs) + Math.max.apply(null, xs)) / 2;
    var dy = 0.52 - (Math.min.apply(null, ys) + Math.max.apply(null, ys)) / 2;
    points.forEach(function (p) { p.x += dx; p.y += dy; });
    groups.forEach(function (group) { group.labelAt.x += dx; group.labelAt.y += dy; });
    return { points: points, groups: groups };
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
          var items = region.members.map(function (id) { return bundle.itemById[id]; });
          var sky = constellationLayout(items, vw, vh, mobile, hashString(key + '/' + region.id));
          function at(point) {
            return { x: regionBox.x + (point.x - 0.5) * regionBox.w, y: regionBox.y + (point.y - 0.5) * regionBox.h };
          }
          domain.regions.push({
            node: region,
            box: regionBox,
            stars: items.map(function (item, index) {
              return Object.assign({ item: item }, at(sky.points[index]));
            }),
            groups: sky.groups.map(function (group) {
              return { label: group.label, members: group.members, labelAt: at(group.labelAt) };
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
          /* Constellation lines, in reading order within each group only. */
          context.globalAlpha = 0.32 * arrival * Math.min(1, s / 3);
          context.strokeStyle = tokens.blue;
          context.lineWidth = 1;
          region.groups.forEach(function (group) {
            context.beginPath();
            group.members.forEach(function (index, step) {
              var star = region.stars[index];
              if (step) context.lineTo(sx(star.x), sy(star.y));
              else context.moveTo(sx(star.x), sy(star.y));
            });
            context.stroke();
          });
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

  /* The site header stays out of the sky entirely: the galaxy is the
     navigation there. It returns once the page scrolls past the plate to
     the article list (search and tabs are useful again), or when keyboard
     focus enters it. */
  function createHeaderController(host) {
    var header = document.querySelector('.md-header');
    if (!header) return function () {};
    var frame = 0;
    var settleTimer = 0;
    var settledY = window.scrollY;
    var passive = { passive: true };

    /* No resting half-sky / half-text. When scrolling stops between the
       plate and the text, finish the move: past half of the way from
       where it last rested goes to the other side, less goes back.
       The text side is the hero card (the link list above it duplicates
       the galaxy) or else the page's h1, or the plate's end without either.
       CSS scroll-snap can't do this: mandatory snapping traps the page at
       the top of the text, proximity leaves the half state. */
    function settle() {
      settleTimer = 0;
      var y = window.scrollY;
      var hero = document.querySelector('.hero-banner') || host.parentNode.querySelector(':scope > h1');
      var headerHeight = header.getBoundingClientRect().height;
      var textY = Math.round(hero
        ? y + hero.getBoundingClientRect().top - headerHeight - 16
        : y + host.getBoundingClientRect().bottom - headerHeight);
      if (y <= 1 || y >= textY - 1) { settledY = y; return; }
      var fromText = settledY >= textY - 1;
      var moved = Math.abs(y - settledY);
      var target = (moved > textY / 2) !== fromText ? textY : 0;
      settledY = target;
      window.scrollTo({ top: target, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
    }

    function onScroll() {
      schedule();
      if (settleTimer) window.clearTimeout(settleTimer);
      settleTimer = window.setTimeout(settle, 140);
    }

    function update() {
      frame = 0;
      var headerHeight = header.getBoundingClientRect().height;
      var pastCanvas = host.getBoundingClientRect().bottom <= headerHeight;
      var focusWithin = header.contains(document.activeElement);
      header.classList.toggle('kb-galaxy-header--revealed', pastCanvas || focusWithin);
    }

    function schedule() {
      if (!frame) frame = window.requestAnimationFrame(update);
    }

    window.addEventListener('scroll', onScroll, passive);
    window.addEventListener('resize', schedule, passive);
    header.addEventListener('focusin', schedule, passive);
    header.addEventListener('focusout', schedule, passive);
    schedule();

    return function () {
      if (frame) window.cancelAnimationFrame(frame);
      if (settleTimer) window.clearTimeout(settleTimer);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', schedule);
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
    var currentTags = [];
    var transitioning = false;
    var disposed = false;
    var world = null;
    var camera = null;
    var frame = 0;
    var flight = null;
    var homeText = null;
    var textDomain = null;
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
      if (!galaxy.isConnected) host.replaceChildren(galaxy, live);
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
              /* Centre on the drawn figure, not the box: a phone's figure
                 hugs the left edge so its captions fit one layer down. */
              var r = findRegion(world, state.domain, id);
              var xs = r.stars.map(function (star) { return star.x; });
              var ys = r.stars.map(function (star) { return star.y; });
              var cx = (Math.min.apply(null, xs) + Math.max.apply(null, xs)) / 2;
              var cy = (Math.min.apply(null, ys) + Math.max.apply(null, ys)) / 2;
              var reach = r.stars.reduce(function (most, star) {
                return Math.max(most, Math.hypot(star.x - cx, star.y - cy));
              }, 0);
              return { x: cx, y: cy, r: reach };
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

    /* Constellation names on the article layer; text only, not links. */
    function groupTags(state) {
      var region = findRegion(world, state.domain, state.region);
      return region.groups.filter(function (group) { return group.label; }).map(function (group, index) {
        var tag = span('kb-galaxy-group', group.label);
        tag.setAttribute('aria-hidden', 'true');
        return {
          element: tag,
          locate: function () {
            var spot = findRegion(world, state.domain, state.region).groups.filter(function (g) { return g.label; })[index].labelAt;
            return { x: spot.x, y: spot.y, r: 0 };
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
          if (current) rememberView({ state: current, article: node.id });
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

    /* On the home sky, the text under the plate follows the chosen
       section: zoom into a domain and its index page's prose replaces the
       home prose; back out to the full sky and the home prose returns. */
    function syncText(state) {
      if (seedDomain) return;
      var domain = state.level ? state.domain : null;
      if (domain === textDomain) return;
      textDomain = domain;
      function after() {
        var nodes = [];
        for (var node = host.nextSibling; node; node = node.nextSibling) nodes.push(node);
        return nodes;
      }
      if (!homeText) homeText = after();
      var load = domain ? loadSectionText(domain) : Promise.resolve(homeText);
      load.then(function (nodes) {
        if (disposed || textDomain !== domain) return;
        after().forEach(function (node) { node.remove(); });
        host.parentNode.append.apply(host.parentNode, nodes);
      }, function (error) {
        if (textDomain === domain) textDomain = null;
        if (window.console) console.warn('[kb-galaxy] Section text unavailable.', error);
      });
    }

    function renderLayer(state, view, previous, shouldFocus) {
      if (disposed) return;
      var entries = layerNodes(state).map(function (item, index) { return buildNode(item, state, index); });
      var tags = state.level === 2 ? groupTags(state) : [];
      entries.concat(tags).forEach(place);
      overlay.replaceChildren.apply(overlay, tags.concat(entries).map(function (entry) { return entry.element; }));
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
      syncText(state);
      rememberView({ state: state, article: null });
      currentEntries = entries;
      currentTags = tags;
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

    /* Where to start the camera: the layer last shown, if it sits inside the
       one being opened, or the article just read inside this region. */
    function entryOrigin(state) {
      var last = recallView();
      rememberView(null);
      if (!last) return null;
      var from = last.state;
      if (seedDomain && from.domain !== seedDomain) return null;
      if (from.level === 2 && last.article && state.level === 2 &&
          from.domain === state.domain && from.region === state.region) {
        return { state: from, article: last.article };
      }
      var inside = from.level > state.level &&
        (state.level === 0 || from.domain === state.domain);
      return inside ? { state: from, article: null } : null;
    }

    function zoomOut() {
      if (!current || transitioning) return;
      var seedLevel = seedDomain ? 1 : 0;
      if (current.level <= seedLevel) {
        /* A clicked anchor stays inside navigation.instant, so the home
           galaxy is built in this same document and can fly out. */
        if (seedDomain) {
          var home = document.createElement('a');
          home.href = siteBase();
          home.hidden = true;
          document.body.appendChild(home);
          home.click();
          home.remove();
        }
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
      currentEntries.concat(currentTags).forEach(place);
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
    var origin = entryOrigin(initial);
    if (origin) {
      transitioning = true;
      resolveView(origin.state).then(function () {
        if (disposed) return;
        camera = cameraFor(world, origin.state);
        if (origin.article) {
          var star = findRegion(world, origin.state.domain, origin.state.region).stars.find(function (entry) {
            return entry.item.id === origin.article;
          });
          if (star) camera = { x: star.x, y: star.y, s: camera.s * 6 };
        }
        transitioning = false;
        changeLevel(initial, null, false, true);
      }).catch(function () {
        transitioning = false;
        changeLevel(initial, null, false, false);
      });
    } else {
      changeLevel(initial, null, false, false);
    }
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
