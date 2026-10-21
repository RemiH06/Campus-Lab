/* Mapa 3D de los territorios del ITESO. El motor (Three.js + escena) es cl-mapa3d.js, un solo archivo en Documentos y
   Medios que se carga aquí, solo en esta página. Se pide como texto y se importa desde un Blob: así funciona aunque
   Documentos y Medios no lo sirva con tipo de JavaScript. Territorio y placa viven en la URL (flechas del navegador). */
(function () {
  var raiz = fragmentElement.querySelector(".cl-m3d"); if (!raiz) return;
  var cfg = typeof configuration !== "undefined" ? configuration : {};
  var $ = function (s) { return raiz.querySelector(s); }, $$ = function (s) { return [].slice.call(raiz.querySelectorAll(s)); };
  var TERR = ["campus", "clavigero", "primavera"], mapa = null, actual = null;
  /* "{t}" en la URL se cambia por el territorio; si no lo trae, se agrega al final (URL corta de Documentos y Medios) */
  var url = function (t) { var d = cfg.datos || "/documents/d/campuslab/territorio-"; return d.indexOf("{t}") >= 0 ? d.replace("{t}", t) : d + t; };

  /* quien edita el sitio (con sesión) ve qué archivo falta; quien visita, solo que el mapa no está disponible */
  var conSesion = function () { try { return !!(window.themeDisplay && themeDisplay.isSignedIn()); } catch (e) { return false; } };
  function aviso(motivo) {
    var a = $(".m3d-aviso");
    if (motivo) a.textContent = "El mapa 3D no está disponible por ahora." + (conSesion() ? " " + motivo : "");
    a.hidden = false; $(".m3d-herr").hidden = true; $(".m3d-pista").hidden = true; $(".m3d-estado").textContent = "";
  }
  function enUrl(modo) {
    try {
      var u = new URL(location.href);
      u.searchParams.set("cl-territorio", actual); var p = $("#m3d-placa").value.trim();
      if (p) u.searchParams.set("cl-placa", p); else u.searchParams.delete("cl-placa");
      history[modo === "push" ? "pushState" : "replaceState"]({ m3d: { t: actual, p: p } }, "", u.pathname + u.search + u.hash);
    } catch (e) { /* sin historial */ }
  }
  function leyenda() {
    var r = mapa.resumen(), h = "";
    if (r.florecen.length) h += '<span class="m3d-ley"><i style="--c:' + r.colores[0] + '"></i>Florecen este mes: ' + r.florecen.slice(0, 4).join(", ") + "</span>";
    if (r.arboles) h += '<span class="m3d-ley"><i class="m3d-ley-arbol"></i>' + r.arboles.toLocaleString("es-MX") + " árboles con placa, a su altura y copa reales</span>";
    Object.keys(r.obs).sort(function (a, b) { return r.obs[b] - r.obs[a]; }).forEach(function (g) {
      h += '<span class="m3d-ley"><i style="--c:' + r.grupos[g][r.oscuro ? 1 : 0] + '"></i>' + r.nombres[g] + " (" + r.obs[g] + ")</span>";
    });
    $(".m3d-leyenda").innerHTML = h;
  }
  function ir(t, modo, placa) {
    if (TERR.indexOf(t) < 0) t = "campus";
    actual = t; raiz.dataset.territorio = t;
    $$(".m3d-tabs button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.t === t)); });
    return mapa.cargar(url(t), cfg.arboles || "/documents/d/campuslab/arboles").then(function (D) {
      $(".m3d-nombre").textContent = D.nombre; $(".m3d-sub").textContent = D.sub; $(".m3d-creditos").textContent = D.creditos;
      $(".m3d-buscar").hidden = !(D.arb && D.arb.length); $('[data-capa="arb"]').closest("label").hidden = !(D.arb && D.arb.length);
      $$("[data-capa]").forEach(function (c) { mapa.capa(c.dataset.capa, c.checked); });
      $("#m3d-placa").value = placa || "";
      if (placa) mapa.irAPlaca(placa);
      leyenda(); if (modo) enUrl(modo);
    }).catch(function (e) {
      $(".m3d-estado").textContent = "No se pudo cargar el territorio." + (conSesion() ? " Revisa que " + url(t) + " y " + (cfg.arboles || "/documents/d/campuslab/arboles") +
        " estén en Documentos y Medios y sean públicos (" + e.message + ")." : "");
    });
  }

  fetch(cfg.script || "/documents/d/campuslab/cl-mapa3d", { credentials: "same-origin" })
    /* si el archivo no existe o no es público, Liferay redirige a la portada (302 → 200 con HTML): eso también es "falta" */
    .then(function (r) { if (!r.ok || r.redirected) throw new Error("falta"); return r.text(); })
    .then(function (codigo) { var u = URL.createObjectURL(new Blob([codigo], { type: "text/javascript" })); return import(u); })
    .then(function (m) { return m.montar(raiz, { ficha: cfg.ficha || "especie" }); })
    .then(function (m) {
      if (!m) { aviso(); return; }
      mapa = m;
      var q = new URLSearchParams(location.search);
      ir(q.get("cl-territorio") || raiz.dataset.territorio || "campus", "replace", q.get("cl-placa"));
      $(".m3d-tabs").addEventListener("click", function (ev) { var b = ev.target.closest("[data-t]"); if (b && b.dataset.t !== actual) ir(b.dataset.t, "push"); });
      $(".m3d-buscar").addEventListener("submit", function (ev) { ev.preventDefault(); var p = $("#m3d-placa").value.replace(/\D/g, ""); $("#m3d-placa").value = p; if (mapa.irAPlaca(p)) enUrl("push"); });
      $(".m3d-herr").addEventListener("click", function (ev) {
        var b = ev.target.closest("[data-h]"); if (!b) return;
        ({ mas: function () { mapa.zoom(0.7); }, menos: function () { mapa.zoom(1.4); }, izq: function () { mapa.girar(-30); }, der: function () { mapa.girar(30); }, inicio: mapa.inicio })[b.dataset.h]();
      });
      $$("[data-capa]").forEach(function (c) { c.addEventListener("change", function () { mapa.capa(c.dataset.capa, c.checked); }); });
      window.addEventListener("popstate", function (ev) { var s = ev.state && ev.state.m3d; if (s) ir(s.t, null, s.p); });
      document.addEventListener("cl-modo", function () { setTimeout(leyenda, 30); });
    })
    .catch(function () { aviso("Falta " + (cfg.script || "/documents/d/campuslab/cl-mapa3d") + " en Documentos y Medios, o no es público."); });
})();
