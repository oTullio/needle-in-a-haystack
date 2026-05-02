/* Image-tab switcher.
 *
 * Activated for every .image-tabs container on the page. Click a tab button
 * to show its corresponding panel and hide the others. Keyboard arrows
 * cycle between tabs (matches the WAI-ARIA tabs pattern).
 */
(function () {
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

  function init(group) {
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

  document.querySelectorAll('.image-tabs').forEach(init);
})();
