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
})();
