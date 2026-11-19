(function () {
  var root = document.documentElement;

  /* ---------------- 主题 ---------------- */
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
    var syncTheme = function () {
      var dark = root.getAttribute("data-theme") !== "light";
      btn.innerHTML = dark
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
      btn.setAttribute("aria-label", dark ? "切换到浅色模式" : "切换到深色模式");
    };
    syncTheme();
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      syncTheme();
    });
  }

  /* ---------------- 语言 ---------------- */
  var DICT = {
    zh: {
      eyebrow: "{n} 个作品 · 持续更新",
      browse: "浏览全部",
      onGithub: "在 GitHub 上看",
      statApps: "个软件",
      statPlatforms: "个平台",
      statAds: "个广告",
      works: "作品",
      searchPh: "搜索软件",
      empty: "没有匹配的软件",
      back: "全部软件",
      about: "介绍",
      features: "功能",
      shots: "截图",
      logs: "更新记录",
      getApp: "获取这个软件",
      download: "下载",
      notYet: "暂未发布"
    },
    en: {
      eyebrow: "{n} apps · always shipping",
      browse: "Browse all",
      onGithub: "View on GitHub",
      statApps: "apps",
      statPlatforms: "platforms",
      statAds: "ads",
      works: "Works",
      searchPh: "Search apps",
      empty: "Nothing matches that search",
      back: "All apps",
      about: "About",
      features: "Features",
      shots: "Screenshots",
      logs: "Changelog",
      getApp: "Get this app",
      download: "Download",
      notYet: "Coming soon"
    }
  };

  function applyLang(lang) {
    var d = DICT[lang] || DICT.zh;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (!d[key]) return;
      el.textContent = d[key].replace("{n}", el.getAttribute("data-count") || "");
    });

    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-ph");
      if (d[key]) el.setAttribute("placeholder", d[key]);
    });

    document.querySelectorAll("[data-zh]").forEach(function (el) {
      var v = el.getAttribute("data-" + lang) || el.getAttribute("data-zh");
      if (v) el.textContent = v;
    });

    root.setAttribute("lang", lang === "en" ? "en" : "zh-CN");

    var sw = document.getElementById("lang-switch");
    if (sw) {
      sw.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
      });
    }
  }

  var savedLang = localStorage.getItem("lang");
  var lang = savedLang === "en" || savedLang === "zh" ? savedLang : "zh";
  applyLang(lang);

  var sw = document.getElementById("lang-switch");
  if (sw) {
    sw.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        lang = b.dataset.lang === "en" ? "en" : "zh";
        localStorage.setItem("lang", lang);
        applyLang(lang);
        applyFilter();
      });
    });
  }

  /* ---------------- 筛选与搜索 ---------------- */
  var grid = document.getElementById("grid");
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var input = document.getElementById("q");
  var empty = document.getElementById("empty");
  var state = { platform: "all", q: "" };

  function applyFilter() {
    var shown = 0;
    cards.forEach(function (card) {
      var plats = (card.dataset.platforms || "").toLowerCase();
      var text = ((card.dataset.text || "") + " " + (card.dataset.textEn || "")).toLowerCase();
      var okPlat =
        state.platform === "all" || plats.indexOf(state.platform.toLowerCase()) > -1;
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
      applyFilter();
    });
  });

  if (input) {
    input.addEventListener("input", function () {
      state.q = input.value.trim().toLowerCase();
      applyFilter();
    });
  }
})();
