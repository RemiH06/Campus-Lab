/* Marco Campus Lab. Liferay lo envuelve en una función con fragmentElement y configuration. */
(function () {
  if (window.__clMarco) return; /* si el fragmento quedó dos veces en la página, corre una sola */
  window.__clMarco = true;
  var html = document.documentElement;
  var B = document.getElementById("p_p_id_com_liferay_journal_content_web_portlet_JournalContentPortlet_INSTANCE_NAVEGACION_");
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  /* ── (b) Modo claro/oscuro: misma clave "cl-modo" que cl-kit.js, para que header, footer y componentes vayan juntos.
     Sin elección guardada manda el modo del dispositivo (decisión de Remi, 21-oct); eso ya lo resuelve el CSS sin
     esperar al JS, así que data-cl-modo solo se pone cuando alguien eligió con el botón ── */
  var sistema = window.matchMedia("(prefers-color-scheme: dark)");
  function modo() { return store.get("cl-modo") || (sistema.matches ? "oscuro" : "claro"); }
  function aplicarModo() {
    var m = modo(), elegido = store.get("cl-modo");
    if (elegido) html.dataset.clModo = elegido; else delete html.dataset.clModo;
    [].forEach.call(document.querySelectorAll(".cl"), function (el) { if (elegido) el.dataset.modo = elegido; else delete el.dataset.modo; });
    [].forEach.call(document.querySelectorAll(".clm-modo"), function (b) {
      var o = m === "oscuro";
      b.setAttribute("aria-pressed", o ? "true" : "false");
      b.querySelector(".clm-sr").textContent = o ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
    });
  }
  var ICONO = '<svg class="clm-luna" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.5 14.6A8.5 8.5 0 0 1 9.4 3.5a8.5 8.5 0 1 0 11.1 11.1z"/></svg>' +
    '<svg class="clm-sol" viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.3M12 19.2v2.3M2.5 12h2.3M19.2 12h2.3M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></g></svg>' +
    '<span class="clm-sr"></span>';
  function boton(antesDe) {
    if (!antesDe) return;
    var b = document.createElement("button");
    b.type = "button"; b.className = "clm-modo"; b.innerHTML = ICONO;
    b.onclick = function () { store.set("cl-modo", modo() === "oscuro" ? "claro" : "oscuro"); aplicarModo(); document.dispatchEvent(new CustomEvent("cl-modo")); };
    antesDe.parentNode.insertBefore(b, antesDe);
  }
  boton(document.getElementById("whats-desktop"));
  boton(document.querySelector("#mobil-menu .icon-search"));
  aplicarModo();
  sistema.addEventListener("change", aplicarModo); /* el dispositivo cambió de modo (p. ej. de día a noche) */
  window.addEventListener("storage", function (e) { if (e.key === "cl-modo") aplicarModo(); });
  document.addEventListener("cl-modo", aplicarModo); /* cl-kit avisa cuando su botón cambia el modo */

  /* ── (c) Idiomas y login: Liferay ya pone el p_l_id y la ruta (con ?…) de cada página; solo les falta texto
     para lectores de pantalla (son banderas y un ícono sin alt) ── */
  [].forEach.call(document.querySelectorAll('#banner a[href*="languageId="]'), function (a) {
    var en = /languageId=en_US/.test(a.getAttribute("href"));
    a.setAttribute("aria-label", en ? "English" : "Español"); a.setAttribute("hreflang", en ? "en" : "es");
  });
  [].forEach.call(document.querySelectorAll('#banner a[href*="/c/portal/login"]'), function (a) { a.setAttribute("aria-label", "Iniciar sesión"); });

  /* ── Celular: el buscador y el menú hamburguesa no se abren a la vez (se enciman). El buscador lo abre y
     cierra el jQuery del portlet de ITESO con un clic en la lupa (#icon-search) o en .close-buscador ── */
  var menu = document.getElementById("navbarToggleExternalContent2");
  var hamb = document.querySelector('#mobil-menu [data-target="#navbarToggleExternalContent2"]');
  var buscador = document.getElementById("search-element");
  var abierto = function () { return buscador && buscador.classList.contains("buscador-show"); };
  if (menu && hamb && buscador) {
    document.addEventListener("click", function (e) {
      if (e.target.closest(".icon-search") && !abierto() && menu.classList.contains("show")) hamb.click();
      if (e.target.closest('[data-target="#navbarToggleExternalContent2"]') && abierto()) document.querySelector(".close-buscador").click();
    }, true);
  }

  /* ── (a) Header compacto al bajar, sin mover el contenido ──
     Al plegar la barra superior y la de "Programas…" el contenedor (sticky) se encoge; el mismo alto se le da
     como margen inferior, así lo que viene después no se mueve. Lo que se pliega es justo el alto de las dos
     barras; se suma sin encoger nada (encoger para medir dispara el "scroll anchoring" del navegador).
     Ya plegadas, su alto se toma del contenido (scrollHeight): en el sitio público no llevan padding. */
  if (!B) return;
  var control = document.querySelector(".control-menu-container"), compacto = false;
  var barras = [B.querySelector(".top-bar"), document.getElementById("subm")].filter(Boolean);
  function plegado() {
    return barras.reduce(function (s, el) {
      return s + (getComputedStyle(el).display === "none" ? 0 : compacto ? el.scrollHeight : el.offsetHeight);
    }, 0);
  }
  function poner(c) {
    var p = c ? plegado() : 0;
    compacto = c;
    html.classList.toggle("clm-compacto", c);
    B.style.marginBottom = c ? p + "px" : "";
  }
  function alBajar() { var c = window.scrollY > 4; if (c !== compacto) poner(c); }
  function medir() {
    html.style.setProperty("--clm-top", control && /fixed|sticky/.test(getComputedStyle(control).position) ? control.offsetHeight + "px" : "0px");
    if (compacto) poner(true);
  }
  medir(); alBajar();
  window.addEventListener("scroll", alBajar, { passive: true });
  var t; window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(medir, 150); });
  if (document.fonts) document.fonts.ready.then(medir);
})();
