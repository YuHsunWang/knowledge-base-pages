// Close the GLightbox overlay when the enlarged image itself is clicked,
// instead of doing nothing / zooming. Capture phase runs before glightbox's
// own handlers. The selector only matches the open lightbox's media, so
// clicking a page thumbnail still opens (never immediately closes).
document.addEventListener(
  "click",
  function (e) {
    if (!e.target.closest(".gslide-media, .gslide-image, .gslide-inline")) return;
    if (!document.querySelector(".glightbox-open")) return;
    var closeBtn = document.querySelector(".gbtn.gclose, .gclose");
    if (closeBtn) closeBtn.click();
  },
  true
);
