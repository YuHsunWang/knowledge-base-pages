/* 靛與朱 — navigation transition for the Knowledge Base.
 *
 * navigation.instant already swaps the document without a page load, so the
 * site is one continuous document. Material animates none of that swap: the
 * old content disappears and the new content appears in the same frame, which
 * reads as a hard cut — worst between a full-bleed galaxy page and an ordinary
 * article page, which share no chrome at all.
 *
 * This layer supplies the missing middle. Outgoing content fades on the click
 * that Material is about to intercept; incoming content fades in when
 * document$ reports the swap. Opacity only — nothing here may move the layout,
 * or it would undo the first-paint geometry work in kb-galaxy.css.
 *
 * The fade-out is speculative: it starts before we know the fetch will
 * succeed. Material falls back to a full reload on failure, and a plain hash
 * click never emits on document$ at all, so the class also clears itself on a
 * timer. A stuck-invisible page is the one failure mode worth engineering out.
 */
(function () {
  'use strict';

  var OUT_MS = 120;
  var SAFETY_MS = 700;

  var calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  var root = document.documentElement;
  var safety = null;
  var lastPath = null;
  var fades = 0;

  function clearOut() {
    if (safety) {
      window.clearTimeout(safety);
      safety = null;
    }
    root.classList.remove('kb-nav-out');
  }

  /* Material intercepts a click only for an internal link it can swap in.
     Mirror that test: anything we fade but it does not swap would leave the
     page dimmed until the safety timer fires. A same-pathname link is the
     common case — in-page anchors and the galaxy's own #kg= level changes
     both stay on the page, and document$ never emits for them. */
  function willSwap(event) {
    if (event.defaultPrevented || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    var el = event.target instanceof Element ? event.target.closest('a') : null;
    if (!el || el.target || !el.href) return false;
    var url;
    try { url = new URL(el.href); } catch (error) { return false; }
    if (url.origin !== window.location.origin) return false;
    return url.pathname !== window.location.pathname;
  }

  function onClick(event) {
    if (calm.matches || !willSwap(event)) return;
    root.classList.add('kb-nav-out');
    if (safety) window.clearTimeout(safety);
    safety = window.setTimeout(clearOut, SAFETY_MS);
  }

  /* Runs per navigation. The incoming animation is one-shot: it is removed on
     animationend so a later navigation can replay it.

     Two emissions must NOT animate. The first one is the cold load: starting
     the real content at opacity 0 would push back the largest contentful
     paint to buy a fade nobody asked for. And document$ also emits without a
     page change — an in-page anchor, or one of the galaxy's own #kg= level
     changes — where a fade would read as an unexplained blink. Only a genuine
     change of pathname earns the animation. */
  function onDocument() {
    clearOut();
    var path = window.location.pathname;
    var changed = lastPath !== null && lastPath !== path;
    lastPath = path;
    if (calm.matches || !changed) return;
    var main = document.querySelector('[data-md-component="main"]');
    if (!main) return;
    main.classList.remove('kb-nav-in');
    void main.offsetWidth;
    main.classList.add('kb-nav-in');
    fades += 1;
    main.addEventListener('animationend', function handler() {
      main.removeEventListener('animationend', handler);
      main.classList.remove('kb-nav-in');
    });
  }

  document.addEventListener('click', onClick, true);
  window.addEventListener('pagehide', clearOut);

  if (typeof window.document$ !== 'undefined' && window.document$ && window.document$.subscribe) {
    window.document$.subscribe(onDocument);
  } else if (document.readyState !== 'loading') {
    onDocument();
  } else {
    document.addEventListener('DOMContentLoaded', onDocument);
  }

  /* Exposed so the acceptance suite can assert that the fade actually ran.
     Asserting only that nothing blinks would stay green if this whole file
     were deleted. */
  window.kbNavigationTransition = {
    OUT_MS: OUT_MS,
    SAFETY_MS: SAFETY_MS,
    get fades() { return fades; }
  };
})();
