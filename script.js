/* Image-tab switcher, click-to-enlarge lightbox, and transcript expander. */
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
  var lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-hidden', 'true');
  lb.innerHTML =
    '<button type="button" class="lightbox-close" aria-label="Close">&times;</button>' +
    '<div class="lightbox-stage"></div>' +
    '<div class="lightbox-caption"></div>';
  document.body.appendChild(lb);

  var lbStage = lb.querySelector('.lightbox-stage');
  var lbCap = lb.querySelector('.lightbox-caption');
  var lbClose = lb.querySelector('.lightbox-close');

  function showLightbox() {
    lb.classList.add('is-open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    lbClose.focus();
  }

  function openImage(src, alt, caption) {
    lbStage.innerHTML = '';
    var img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';
    lbStage.appendChild(img);
    lbCap.textContent = caption || '';
    showLightbox();
  }

  function openText(title, source, htmlBody) {
    lbStage.innerHTML = '';
    var article = document.createElement('article');
    article.className = 'lightbox-text';
    var head = '';
    if (title) {
      head += '<h1>' + escapeHtml(title) + '</h1>';
    }
    if (source) {
      head += '<p style="color:var(--muted);font-size:.85rem;margin:.2rem 0 .9rem;">'
        + escapeHtml(source) + '</p>';
    }
    article.innerHTML = head + htmlBody;
    // Clicks inside the panel shouldn't bubble up and close the lightbox.
    article.addEventListener('click', function (e) { e.stopPropagation(); });
    lbStage.appendChild(article);
    lbCap.textContent = '';
    showLightbox();
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function closeLightbox() {
    lb.classList.remove('is-open');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    setTimeout(function () {
      if (!lb.classList.contains('is-open')) lbStage.innerHTML = '';
    }, 200);
  }

  // Click anywhere on the overlay (except the staged content) closes it.
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target === lbStage || e.target === lbCap) {
      closeLightbox();
    }
  });
  lbClose.addEventListener('click', closeLightbox);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lb.classList.contains('is-open')) closeLightbox();
  });

  // Bind every chart image inside content sections.
  document.querySelectorAll('.section img').forEach(function (img) {
    img.addEventListener('click', function () {
      var caption = '';
      var fig = img.closest('figure');
      if (fig) {
        var capEl = fig.querySelector('figcaption');
        if (capEl) caption = capEl.textContent.trim();
      }
      openImage(img.currentSrc || img.src, img.alt, caption);
    });
  });

  // Bind every transcript card.
  document.querySelectorAll('.transcript-trigger').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var tplId = btn.getAttribute('data-template');
      var title = btn.getAttribute('data-title') || '';
      var source = btn.getAttribute('data-source') || '';
      var tpl = document.getElementById(tplId);
      var body = tpl ? tpl.innerHTML : '<p>Transcript missing.</p>';
      openText(title, source, body);
    });
  });
})();
