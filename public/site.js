(function () {
  // Filters: <div data-filter-for="id"> with buttons[data-f]; rows carry data-k (space separated).
  [].forEach.call(document.querySelectorAll('[data-filter-for]'), function (g) {
    var list = document.getElementById(g.dataset.filterFor);
    if (!list) return;
    var btns = [].slice.call(g.querySelectorAll('button[data-f]'));
    var rows = [].slice.call(list.querySelectorAll('[data-k]'));
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var f = b.dataset.f;
        btns.forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        rows.forEach(function (r) { r.hidden = !(f === 'all' || (' ' + r.dataset.k + ' ').indexOf(' ' + f + ' ') > -1); });
      });
    });
  });
  // Copy buttons: data-copy="element id", data-done="label shown after copying".
  [].forEach.call(document.querySelectorAll('[data-copy]'), function (b) {
    b.addEventListener('click', function () {
      var el = document.getElementById(b.dataset.copy);
      if (!el) return;
      var txt = el.innerText.trim(), label = b.textContent;
      function done() { b.textContent = b.dataset.done || '✓'; setTimeout(function () { b.textContent = label; }, 1600); }
      function select() { var r = document.createRange(); r.selectNodeContents(el); var s = getSelection(); s.removeAllRanges(); s.addRange(r); }
      try { navigator.clipboard.writeText(txt).then(done, select); } catch (e) { select(); }
    });
  });
  // Phones: every section after the first opens on tap; the text stays in the page.
  var mq = window.matchMedia('(max-width: 719px)');
  var art = document.querySelector('.art');
  if (art && mq.matches) {
    var secs = [].slice.call(art.querySelectorAll(':scope > section'));
    var keep = secs[0] && secs[0].id === 'latest' ? 2 : 1;
    secs.slice(keep).forEach(function (s) {
      var h = s.querySelector(':scope > h2');
      if (!h) return;
      s.classList.add('fold');
      h.setAttribute('role', 'button'); h.setAttribute('tabindex', '0'); h.setAttribute('aria-expanded', 'false');
      function toggle() { var o = s.classList.toggle('open'); h.setAttribute('aria-expanded', o); }
      h.addEventListener('click', toggle);
      h.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
    function openHash() {
      var id = location.hash.slice(1); if (!id) return;
      var el = document.getElementById(id); if (!el) return;
      var s = el.closest('section.fold');
      if (s && !s.classList.contains('open')) { s.classList.add('open'); s.querySelector(':scope > h2').setAttribute('aria-expanded', 'true'); el.scrollIntoView(); }
    }
    openHash(); window.addEventListener('hashchange', openHash);
  }
})();
