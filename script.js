/* Image-tab switcher and click-to-enlarge lightbox. */
(function () {
  // ----- Tab switcher (one widget per .image-tabs container) -----
  function activate(group, btn) {
    var btns = group.querySelectorAll('.image-tab-btn');
    var panels = group.querySelectorAll('.image-tab-panel');
    btns.forEach(function (b) {
      var on = b === btn;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    var targetId = btn.getAttribute('data-target');
    panels.forEach(function (p) {
      var on = p.id === targetId;
      p.classList.toggle('is-active', on);
      if (on) {
        p.removeAttribute('hidden');
      } else {
        p.setAttribute('hidden', '');
      }
    });
  }

  function initTabs(group) {
    var btns = Array.prototype.slice.call(
      group.querySelectorAll('.image-tab-btn')
    );
    btns.forEach(function (btn, i) {
      btn.addEventListener('click', function () { activate(group, btn); });
      btn.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var dir = e.key === 'ArrowRight' ? 1 : -1;
        var next = btns[(i + dir + btns.length) % btns.length];
        next.focus();
        activate(group, next);
      });
    });
  }

  document.querySelectorAll('.image-tabs').forEach(initTabs);

  // ----- Lightbox -----
  // One reusable overlay; populated and shown on demand.
  var lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-hidden', 'true');
  lb.innerHTML =
    '<button type="button" class="lightbox-close" aria-label="Close">&times;</button>' +
    '<img alt="">' +
    '<div class="lightbox-caption"></div>';
  document.body.appendChild(lb);

  var lbImg = lb.querySelector('img');
  var lbCap = lb.querySelector('.lightbox-caption');
  var lbClose = lb.querySelector('.lightbox-close');

  function openLightbox(src, alt, caption) {
    lbImg.src = src;
    lbImg.alt = alt || '';
    lbCap.textContent = caption || '';
    lbCap.style.display = caption ? 'block' : 'none';
    lb.classList.add('is-open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    lbClose.focus();
  }

  function closeLightbox() {
    lb.classList.remove('is-open');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    // Defer src clear so the fade-out doesn't show a flash of white.
    setTimeout(function () {
      if (!lb.classList.contains('is-open')) lbImg.src = '';
    }, 200);
  }

  // Click anywhere on the overlay (except the image) closes it.
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target === lbCap) closeLightbox();
  });
  lbClose.addEventListener('click', closeLightbox);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lb.classList.contains('is-open')) closeLightbox();
  });

  // Bind every chart image inside content sections.
  document.querySelectorAll('.section img').forEach(function (img) {
    img.addEventListener('click', function () {
      var caption = '';
      // Prefer an adjacent figcaption if the img is inside a <figure>.
      var fig = img.closest('figure');
      if (fig) {
        var capEl = fig.querySelector('figcaption');
        if (capEl) caption = capEl.textContent.trim();
      }
      openLightbox(img.currentSrc || img.src, img.alt, caption);
    });
  });
})();
