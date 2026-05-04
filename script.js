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
  // Each trigger declares `data-src="content/transcripts/<slug>.html"` and the
  // body is fetched lazily on first open. Loaded markup is cached in-memory
  // so re-opening is instant.
  var transcriptCache = {};

  function loadTranscript(src) {
    if (transcriptCache[src]) return Promise.resolve(transcriptCache[src]);
    return fetch(src, { credentials: 'same-origin' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.text();
    }).then(function (html) {
      transcriptCache[src] = html;
      return html;
    });
  }

  document.querySelectorAll('.transcript-trigger').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var src = btn.getAttribute('data-src');
      var title = btn.getAttribute('data-title') || '';
      var source = btn.getAttribute('data-source') || '';
      if (!src) {
        // Backwards-compat with old `data-template` form.
        var tpl = document.getElementById(btn.getAttribute('data-template') || '');
        openText(title, source, tpl ? tpl.innerHTML : '<p>Transcript missing.</p>');
        return;
      }
      openText(title, source, '<p><em>Loading…</em></p>');
      loadTranscript(src).then(function (html) {
        openText(title, source, html);
      }).catch(function () {
        openText(title, source, '<p><em>Failed to load transcript.</em></p>');
      });
    });
  });
})();

/* ----- Email signup form ----- */
(function () {
  // Paste the deployed Apps Script web app URL here:
  var SIGNUP_ENDPOINT = 'PASTE_YOUR_APPS_SCRIPT_WEB_APP_URL_HERE';

  var form = document.getElementById('signup-form');
  if (!form) return;
  var input = document.getElementById('signup-email');
  var status = document.getElementById('signup-status');
  var button = form.querySelector('button[type="submit"]');

  function setStatus(msg, kind) {
    status.textContent = msg;
    status.classList.remove('is-success', 'is-error');
    if (kind) status.classList.add('is-' + kind);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var email = (input.value || '').trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setStatus('Please enter a valid email address.', 'error');
      input.focus();
      return;
    }
    if (SIGNUP_ENDPOINT.indexOf('PASTE_') === 0) {
      setStatus('Signup endpoint not configured yet.', 'error');
      return;
    }

    button.disabled = true;
    setStatus('Submitting…', null);

    var body = new URLSearchParams({
      email: email,
      source: 'needle-in-a-haystack site',
      userAgent: navigator.userAgent
    }).toString();

    // no-cors so the browser doesn't block the cross-origin POST.
    // We can't read the response, so we treat a resolved promise as success.
    fetch(SIGNUP_ENDPOINT, {
      method: 'POST',
      mode: 'no-cors',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body
    }).then(function () {
      setStatus('Thanks — we\'ll email you when the paper is out.', 'success');
      input.value = '';
    }).catch(function () {
      setStatus('Something went wrong. Please try again later.', 'error');
    }).then(function () {
      button.disabled = false;
    });
  });
})();
