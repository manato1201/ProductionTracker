// テーマ(システム → ライト → ダーク)の切り替え。保存できない環境でも動く。
(function () {
  var KEY = "pt-docs-theme";
  var root = document.documentElement;
  function read() { try { return localStorage.getItem(KEY) || "system"; } catch (e) { return "system"; } }
  function apply(mode) { if (mode === "system") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", mode); }
  apply(read());
  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("theme-toggle");
    if (!button) return;
    var labels = { system: "テーマ: OS に合わせる", light: "テーマ: ライト", dark: "テーマ: ダーク" };
    function refresh() { var m = read(); button.setAttribute("aria-label", labels[m]); button.title = labels[m]; button.textContent = m === "dark" ? "☾" : m === "light" ? "☀" : "◐"; }
    button.addEventListener("click", function () {
      var order = ["system", "light", "dark"], next = order[(order.indexOf(read()) + 1) % 3];
      try { localStorage.setItem(KEY, next); } catch (e) { /* 保存できなくても続行 */ }
      apply(next); refresh();
    });
    refresh();
  });
})();
