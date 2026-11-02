/* Youth LaunchPad — site behaviour
   1. sticky nav state + mobile menu
   2. hero bridge line-art draw (home only)
   3. inquiry forms: type switcher, submit via endpoint or email fallback
*/
(function () {
  "use strict";

  var nav = document.getElementById("nav");
  var burger = document.getElementById("navBurger");
  var mmenu = document.getElementById("mmenu");

  /* ---------- nav ---------- */
  function onScroll() {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function setMenu(open) {
    if (!burger || !mmenu) return;
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    mmenu.classList.toggle("is-open", open);
    mmenu.setAttribute("aria-hidden", String(!open));
    document.body.style.overflow = open ? "hidden" : "";
  }
  if (burger && mmenu) {
    burger.addEventListener("click", function () {
      setMenu(burger.getAttribute("aria-expanded") !== "true");
    });
    mmenu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setMenu(false);
    });
    window.matchMedia("(min-width: 1061px)").addEventListener("change", function (e) {
      if (e.matches) setMenu(false);
    });
  }

  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  /* ---------- hero bridge ---------- */
  var bridge = document.querySelector(".bridge");
  if (bridge) {
    bridge.querySelectorAll(".draw").forEach(function (p) {
      var len = typeof p.getTotalLength === "function" ? p.getTotalLength() : 1000;
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
    });
    requestAnimationFrame(function () {
      document.body.classList.add("is-loaded");
      bridge.classList.add("is-ready");
    });
  } else {
    document.body.classList.add("is-loaded");
  }

  /* ---------- forms ---------- */
  var form = document.querySelector("form.inquiry");
  if (!form) return;

  var panels = form.querySelectorAll("fieldset[data-type]");
  var switches = form.querySelectorAll(".form__switch button");
  var msg = form.querySelector(".form__msg");
  var typeInput = form.querySelector("input[name='inquiry_type']");

  function showType(type) {
    var found = false;
    panels.forEach(function (fs) {
      var match = fs.dataset.type === type;
      fs.hidden = !match;
      fs.querySelectorAll("[data-required]").forEach(function (el) { el.required = match; });
      if (match) found = true;
    });
    if (!found) return showType(panels[0].dataset.type);
    switches.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.type === type)); });
    if (typeInput) typeInput.value = type;
    if (history.replaceState) history.replaceState(null, "", "#" + type);
  }

  if (panels.length) {
    switches.forEach(function (b) {
      b.addEventListener("click", function () { showType(b.dataset.type); });
    });
    var initial = (location.hash || "").replace("#", "");
    showType(initial || panels[0].dataset.type);
    window.addEventListener("hashchange", function () {
      var t = (location.hash || "").replace("#", "");
      if (t) showType(t);
    });
  }

  function say(text, isError) {
    if (!msg) return;
    msg.textContent = text;
    msg.classList.add("is-visible");
    msg.classList.toggle("is-error", !!isError);
    msg.focus && msg.focus();
  }

  function collect() {
    var data = {};
    var fd = new FormData(form);
    fd.forEach(function (v, k) {
      var el = form.querySelector("[name='" + k + "']");
      if (el && el.closest("fieldset") && el.closest("fieldset").hidden) return;
      if (k === "website_url") return; // honeypot
      data[k] = v;
    });
    return data;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var hp = form.querySelector("input[name='website_url']");
    if (hp && hp.value) return; // bot

    var data = collect();
    var endpoint = form.dataset.endpoint;
    var submit = form.querySelector("button[type='submit']");
    var label = data.inquiry_type ? data.inquiry_type.replace(/-/g, " ") : "inquiry";

    if (endpoint) {
      if (submit) submit.disabled = true;
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data)
      }).then(function (r) {
        if (!r.ok) throw new Error("Request failed");
        form.reset();
        say("Thanks, your " + label + " was sent. We read every message and will reply by email.");
      }).catch(function () {
        say("Your message could not be sent. Please email info@youthlaunchpad.org directly.", true);
      }).finally(function () { if (submit) submit.disabled = false; });
      return;
    }

    // No endpoint configured yet: hand off to the visitor's email app.
    var lines = Object.keys(data).map(function (k) {
      return k.replace(/_/g, " ") + ": " + data[k];
    });
    var subject = encodeURIComponent("Youth LaunchPad " + label);
    var body = encodeURIComponent(lines.join("\n"));
    window.location.href = "mailto:info@youthlaunchpad.org?subject=" + subject + "&body=" + body;
    say("Your email app should open with this " + label + " filled in. If it doesn't, email info@youthlaunchpad.org and include the details above.");
  });
})();
