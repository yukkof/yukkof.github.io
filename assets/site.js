(function () {
  var root = document.documentElement;
  var stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") {
    root.setAttribute("data-theme", stored);
  } else {
    root.setAttribute(
      "data-theme",
      window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"
    );
  }

  var btn = document.getElementById("theme-toggle");
  if (btn) {
    var sync = function () {
      var dark = root.getAttribute("data-theme") !== "light";
      btn.innerHTML = dark
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
      btn.setAttribute("aria-label", dark ? "切换到浅色模式" : "切换到深色模式");
    };
    sync();
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      sync();
    });
  }

  var grid = document.getElementById("grid");
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var input = document.getElementById("q");
  var empty = document.getElementById("empty");
  var state = { platform: "all", q: "" };

  function apply() {
    var shown = 0;
    cards.forEach(function (card) {
      var plats = (card.dataset.platforms || "").toLowerCase();
      var text = (card.dataset.text || "").toLowerCase();
      var okPlat = state.platform === "all" || plats.indexOf(state.platform.toLowerCase()) > -1;
      var okText = !state.q || text.indexOf(state.q) > -1;
      var ok = okPlat && okText;
      card.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    if (empty) empty.style.display = shown ? "none" : "";
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      chips.forEach(function (c) {
        c.setAttribute("aria-pressed", String(c === chip));
      });
      state.platform = chip.dataset.platform || "all";
      apply();
    });
  });

  if (input) {
    input.addEventListener("input", function () {
      state.q = input.value.trim().toLowerCase();
      apply();
    });
  }
})();
