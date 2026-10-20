/* ═══════════════════════════════════════════════════════════════════════
   cl-kit.js · Campus Lab (camino B). Se sube una vez a Documentos y Medios.
   Busca en la página cada <div class="cl" data-cl="..."> y lo monta:

     data-cl            coleccion | especie | mapa
     data-datos         URL de arboles.json
     data-mapa          URL de mapa-campus.json
     data-fotos         prefijo de las fotos (URL de la carpeta en Documentos y Medios)
     data-fotos-ext     extensión que se agrega al nombre (vacía en Liferay, ".jpg" en local)
     data-foto-grande   sufijo para fotos grandes (ej. "?imagePreview=1")
     data-foto-chica    sufijo para miniaturas (ej. "?imageThumbnail=1")
     data-ficha         URL de la página de ficha (se le agrega ?id=)
     data-pagina-mapa   URL de la página del mapa (se le agrega ?id= o ?placa=)
     data-coleccion     URL de la página de colección

   Si existe window.CL_DATOS ({ arboles, mapa }) se usa en lugar de pedir
   los JSON (vista local sin servidor). Sin JS, el contenedor muestra su
   texto de respaldo.
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  var PARTES = ["fruto", "flor", "hoja", "tronco", "arbol_completo"]; // de la médula hacia la corteza
  var NOM = { arbol_completo: "Árbol completo", tronco: "Tronco", hoja: "Hoja", flor: "Flor", fruto: "Fruto" };
  var RASGO = { altura: "Altura", tronco: "Tronco", copa: "Copa", ramas: "Ramas", hojas: "Hojas", flores: "Flores", frutos: "Frutos" };
  var MIX = { fruto: "92%", flor: "76%", hoja: "60%", tronco: "44%", arbol_completo: "30%" };
  // Floración por mes (aproximado; confirmar con jardinería). Cada id necesita su regla en cl-base.css.
  var FLOR = [
    { id: "clavellina", nom: "Clavellina", meses: [12, 1] },
    { id: "rosa-morada", nom: "Rosa morada", meses: [2] },
    { id: "jacaranda", nom: "Jacaranda", meses: [3] },
    { id: "primavera", nom: "Primavera", meses: [4] },
    { id: "tabachin", nom: "Tabachín", meses: [5, 6] },
    { id: "lluvias", nom: "Lluvias", meses: [7, 8, 9, 10] },
    { id: "galeana", nom: "Galeana", meses: [11] }
  ];
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var norm = function (s) { return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
  var hash = function (s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };
  var rng = function (seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
  var conParam = function (url, k, v) { return url + (url.indexOf("?") >= 0 ? "&" : "?") + k + "=" + encodeURIComponent(v); };
  var param = function (k) { return new URLSearchParams(location.search).get(k); };
  var mesFlor = function () { var m = new Date().getMonth() + 1; return FLOR.filter(function (f) { return f.meses.indexOf(m) >= 0; })[0].id; };

  /* ── Datos: se piden una sola vez por página aunque haya varios componentes ── */
  /* Se leen por partes para mostrar el avance: avance[url] = [bytes bajados, bytes totales (0 si el servidor no lo dice)] */
  var cache = {}, avance = {};
  function pedir(url) {
    if (!cache[url]) cache[url] = fetch(url, { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      var total = +r.headers.get("Content-Length") || 0, lector = r.body && r.body.getReader ? r.body.getReader() : null;
      if (!lector) return r.json();
      var trozos = [], n = 0;
      function leer() {
        return lector.read().then(function (x) {
          if (x.done) { var b = new Uint8Array(n), o = 0; trozos.forEach(function (t) { b.set(t, o); o += t.length; }); return JSON.parse(new TextDecoder().decode(b)); }
          trozos.push(x.value); n += x.value.length; avance[url] = [n, total];
          document.dispatchEvent(new CustomEvent("cl-avance"));
          return leer();
        });
      }
      return leer();
    });
    return cache[url];
  }
  /* Barra de carga: suma el avance de las URL que espera un componente */
  var CARGA = '<div class="cl-carga cl-indet" role="progressbar" aria-label="Cargando datos" aria-valuemin="0" aria-valuemax="100"><span class="cl-carga-t">Cargando datos…</span><span class="cl-carga-b"><i></i></span></div>';
  function seguirCarga(el, urls) {
    var mb = function (b) { return (b / 1048576).toFixed(1); };
    function pinta() {
      var n = 0, t = 0, sabe = true;
      urls.forEach(function (u) { var a = avance[u]; if (!a || !a[1]) sabe = false; else { n += a[0]; t += a[1]; } });
      if (!sabe || !t) return;
      var p = Math.min(100, Math.round(n / t * 100));
      el.classList.remove("cl-indet"); el.style.setProperty("--p", p + "%"); el.setAttribute("aria-valuenow", p);
      el.querySelector(".cl-carga-t").textContent = "Cargando datos · " + mb(n) + " de " + mb(t) + " MB (" + p + " %)";
    }
    document.addEventListener("cl-avance", pinta); pinta();
    return function () { document.removeEventListener("cl-avance", pinta); };
  }
  function cargar(cfg) {
    if (window.CL_DATOS) return Promise.resolve(window.CL_DATOS);
    return Promise.all([pedir(cfg.datos), pedir(cfg.mapa)]).then(function (r) { return { arboles: r[0], mapa: r[1] }; });
  }
  function preparar(D) {
    if (D._listo) return D;
    var esp = D.arboles.especies;
    D.byId = {}; esp.forEach(function (e) { e.partes = PARTES.filter(function (p) { return e.fotos[p]; }); D.byId[e.id] = e; });
    D.ptsOf = {}; D.placa = {};
    D.mapa.pts.forEach(function (p) { var e = esp[p[3]]; (D.ptsOf[e.id] = D.ptsOf[e.id] || []).push(p); D.placa[p[0]] = p; });
    D._listo = true; return D;
  }

  /* ═══ Componente: barra (modo y floración); sincroniza todos los .cl de la página ═══ */
  function todos() { return [].slice.call(document.querySelectorAll(".cl")); }
  function modoActual() { return store.get("cl-modo") || "claro"; } /* claro por defecto aunque el sistema esté en oscuro */
  function aplicarColor() {
    var f = store.get("cl-flor") || "auto", m = modoActual();
    todos().forEach(function (el) { el.dataset.floracion = f === "auto" ? mesFlor() : f; el.dataset.modo = m; });
  }
  var barra = {
    mount: function (el) {
      var auto = FLOR.filter(function (f) { return f.id === mesFlor(); })[0];
      el.innerHTML = '<label class="cl-flor-pick"><span class="cl-sr">Floración</span><select aria-label="Paleta de floración"><option value="auto">Floración del mes (' + auto.nom + ")</option>" +
        FLOR.map(function (f) { return '<option value="' + f.id + '">' + f.nom + "</option>"; }).join("") + '</select></label><button class="cl-btn" type="button"></button>';
      var sel = el.querySelector("select"), b = el.querySelector("button");
      var pinta = function () { var o = modoActual() === "oscuro"; b.textContent = o ? "Modo claro" : "Modo oscuro"; b.setAttribute("aria-label", o ? "Cambiar a modo claro" : "Cambiar a modo oscuro"); };
      sel.value = store.get("cl-flor") || "auto";
      sel.onchange = function () { store.set("cl-flor", sel.value); aplicarColor(); };
      b.onclick = function () { store.set("cl-modo", modoActual() === "oscuro" ? "claro" : "oscuro"); aplicarColor(); pinta(); document.dispatchEvent(new CustomEvent("cl-modo")); };
      document.addEventListener("cl-modo", function () { aplicarColor(); pinta(); }); /* el botón del Marco también avisa */
      pinta();
    }
  };

  /* ═══ Componente: anillos del tronco (5 partes) ═══ */
  var anillos = {
    mount: function (el, e, sel, onPick) {
      var R = rng(hash(e.id)), cx = 110, cy = 110, r0 = 20, dr = 17.5;
      var ondas = [1 + R() * 3, 2 + R() * 4, 3 + R() * 5].map(function (f) { return { f: Math.round(f), ph: R() * 6.28, a: 0.8 + R() * 1.6 }; });
      var radio = function (r, a) { return r + ondas.reduce(function (s, o) { return s + o.a * (r / 100) * Math.sin(o.f * a + o.ph); }, 0); };
      var curva = function (r) { var d = ""; for (var i = 0; i <= 72; i++) { var a = i / 72 * Math.PI * 2, rr = radio(r, a); d += (i ? "L" : "M") + (cx + rr * Math.cos(a)).toFixed(1) + "," + (cy + rr * Math.sin(a)).toFixed(1); } return d + "Z"; };
      var svg = "";
      for (var i = PARTES.length - 1; i >= 0; i--) {
        var p = PARTES[i], ro = r0 + dr * (i + 1), ri = r0 + dr * i, has = !!e.fotos[p], grains = "";
        if (has) for (var g = 1; g <= 2; g++) grains += '<path class="cl-grain" d="' + curva(ri + dr * g / 3) + '"/>';
        svg += '<g class="cl-ring ' + (has ? "cl-has" : "cl-no") + (p === sel ? " cl-sel" : "") + '" style="--mix:' + MIX[p] + '" data-parte="' + p + '"' +
          (has ? ' role="button" tabindex="0" aria-label="Ver foto de ' + NOM[p].toLowerCase() + '"' : ' aria-hidden="true"') + '><path class="cl-band" d="' + curva(ro) + '"/>' + grains + '<path class="cl-edge" d="' + curva(ro) + '"/></g>';
      }
      svg += '<path class="cl-medula" d="' + curva(r0) + '"/><text class="cl-medula-t" x="' + cx + '" y="' + cy + '">' + e.partes.length + "/5</text>";
      var leg = PARTES.slice().reverse().map(function (p) {
        var has = !!e.fotos[p];
        return '<li class="' + (has ? "" : "cl-no") + '" style="--mix:' + MIX[p] + '"><button type="button" data-parte="' + p + '" aria-pressed="' + (p === sel) + '"' + (has ? "" : " disabled") + '><span class="cl-sw"></span>' + NOM[p] + (has ? "" : " · falta foto") + "</button></li>";
      }).join("");
      el.innerHTML = '<svg viewBox="0 0 220 220" role="group" aria-label="Partes fotografiadas: ' + e.partes.length + ' de 5">' + svg + '</svg><ul class="cl-leyenda">' + leg + "</ul>";
      el.onclick = function (ev) { var t = ev.target.closest("[data-parte]"); if (t && e.fotos[t.dataset.parte]) onPick(t.dataset.parte); };
      el.onkeydown = function (ev) { if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches(".cl-ring[role=button]")) { ev.preventDefault(); onPick(ev.target.dataset.parte); } };
    }
  };

  /* ═══ Componente: mapa del campus ═══ */
  var mapa = {
    mount: function (el, D, o) {
      // o: { hi: [ids], foco, placa, zoom: "todo"|"hi", controles, onPick(placa), ar, label }
      var M = D.mapa, pts = M.pts, esp = D.arboles.especies, hiSet = {};
      (o.hi || []).forEach(function (id) { hiSet[id] = 1; });
      var base = "<g>" + M.bld.map(function (d) { return '<path class="cl-bld" d="' + d + '"/>'; }).join("") + "</g><g>" + M.cam.map(function (d) { return '<path class="cl-cam" d="' + d + '"/>'; }).join("") + "</g>";
      var dots = "", top = "";
      pts.forEach(function (p) { var on = hiSet[esp[p[3]].id], c = '<circle class="cl-pt' + (on ? " cl-hi" : "") + '" cx="' + p[1] + '" cy="' + p[2] + '" r="' + (on ? 5 : 2.1) + '"/>'; if (on) top += c; else dots += c; });
      var q = o.placa && D.placa[o.placa], yo = q ? '<circle class="cl-pt cl-hi" cx="' + q[1] + '" cy="' + q[2] + '" r="4"/><circle class="cl-yo" cx="' + q[1] + '" cy="' + q[2] + '" r="10"/>' : "";
      var caja = function (list) { var xs = list.map(function (p) { return p[1]; }).sort(function (a, b) { return a - b; }), ys = list.map(function (p) { return p[2]; }).sort(function (a, b) { return a - b; }); var k = function (a, f) { return a[Math.floor((a.length - 1) * f)]; }; return list.length > 40 ? [k(xs, .03), k(ys, .03), k(xs, .97), k(ys, .97)] : [xs[0], ys[0], xs[xs.length - 1], ys[ys.length - 1]]; };
      var ar = o.ar || 1.6;
      var vb = function (b) { var pad = 30, w = Math.max(b[2] - b[0] + pad * 2, 120), h = Math.max(b[3] - b[1] + pad * 2, 120 / ar); if (w / h > ar) h = w / ar; else w = h * ar; var cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2; return [cx - w / 2, cy - h / 2, w, h]; };
      var hiPts = pts.filter(function (p) { return hiSet[esp[p[3]].id]; });
      var todo = vb(caja(pts)), enfoque = q ? vb([q[1] - 110, q[2] - 80, q[1] + 110, q[2] + 80]) : (o.zoom === "hi" && hiPts.length ? vb(caja(hiPts)) : todo);
      el.classList.add("cl-mapa"); el.classList.toggle("cl-foco", !!o.foco); el.style.setProperty("--ar", ar);
      el.innerHTML = '<svg viewBox="' + enfoque.join(" ") + '" role="img" aria-label="' + esc(o.label || "Mapa del campus") + '">' + base + "<g>" + dots + "</g><g>" + top + "</g>" + yo + "</svg>" +
        (o.controles ? '<div class="cl-mapa-zoom"><button class="cl-btn" type="button" data-z="todo">Todo el campus</button>' + (hiPts.length || q ? '<button class="cl-btn" type="button" data-z="foco">Acercar</button>' : "") + "</div>" : "");
      var svg = el.querySelector("svg"), cur = enfoque.slice();
      var ir = function (dst) {
        if (reduce.matches) { cur = dst; svg.setAttribute("viewBox", dst.join(" ")); return; }
        var src = cur.slice(), t0 = performance.now();
        var step = function (now) { var t = Math.min((now - t0) / 260, 1), k = 1 - Math.pow(1 - t, 3); cur = src.map(function (v, i) { return v + (dst[i] - v) * k; }); svg.setAttribute("viewBox", cur.join(" ")); if (t < 1) requestAnimationFrame(step); };
        requestAnimationFrame(step);
      };
      el.onclick = function (ev) {
        var z = ev.target.closest("[data-z]"); if (z) { ir(z.dataset.z === "todo" ? todo : enfoque); return; }
        if (!o.onPick) return;
        var pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; var m = svg.getScreenCTM(); if (!m) return; var loc = pt.matrixTransform(m.inverse());
        var tol = cur[2] / svg.clientWidth * 14, best = null, bd = tol * tol;
        pts.forEach(function (p) { var dx = p[1] - loc.x, dy = p[2] - loc.y, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = p; } });
        if (best) o.onPick(best[0]);
      };
    }
  };

  /* ═══ Componente: mosaico (empacador tipo tetris de LinNeo, con azar sembrado para que no cambie en cada carga) ═══ */
  var FORMAS = {
    2: [[[0, 0], [1, 0]], [[0, 0], [0, 1]]],
    3: [[[0, 0], [1, 0], [0, 1]], [[0, 0], [1, 0], [1, 1]], [[0, 0], [0, 1], [1, 1]], [[1, 0], [0, 1], [1, 1]]],
    4: [[[0, 0], [1, 0], [0, 1], [1, 1]], [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 0], [0, 1], [0, 2], [1, 2]], [[1, 0], [2, 0], [0, 1], [1, 1]]],
    5: [[[0, 0], [0, 1], [0, 2], [0, 3], [1, 3]], [[0, 0], [1, 0], [2, 0], [3, 0], [0, 1]], [[0, 0], [1, 0], [1, 1], [1, 2], [1, 3]], [[3, 0], [0, 1], [1, 1], [2, 1], [3, 1]]]
  };
  function empacar(items, cols) {
    var occ = {}, out = [];
    var cabe = function (sh, x, y) { return sh.every(function (c) { return x + c[0] < cols && !occ[(x + c[0]) + "," + (y + c[1])]; }); };
    var busca = function (sh) { for (var y = 0; y < 4000; y++) for (var x = 0; x < cols; x++) if (cabe(sh, x, y)) return [x, y]; return null; };
    var orden = items.filter(function (e) { return e.partes.length === 4; }).concat(items.filter(function (e) { return e.partes.length !== 4; }));
    orden.forEach(function (e) {
      var R = rng(hash(e.id)), k = e.partes.length, sh;
      if (k <= 1) { sh = [[0, 0]]; if (k === 1 && R() < 0.35 && cols >= 6) { var big = [[0, 0], [1, 0], [0, 1], [1, 1]]; if (busca(big)) sh = big; } }
      else { var fs = FORMAS[Math.min(k, 5)]; sh = fs[Math.floor(R() * fs.length)]; }
      var pos = busca(sh); if (!pos) return;
      sh.forEach(function (c) { occ[(pos[0] + c[0]) + "," + (pos[1] + c[1])] = 1; });
      out.push({ e: e, x: pos[0], y: pos[1], sh: sh });
    });
    return out;
  }
  /* Contorno de cada especie. Sus casillas están separadas por huecos de 4 px, así que se unen en una retícula doble
     (casilla, hueco, casilla…): entra cada casilla, el hueco entre dos vecinas y el centro de un bloque de 2×2. Se trazan
     solo los lados que dan hacia afuera (las puntas cuadradas del trazo cierran esquinas y entrantes de las piezas en L)
     y los huecos internos se rellenan del mismo color, como la junta de un vitral: cada especie se lee como una pieza.
     El trazo se recorta a la forma de la pieza para que quede todo adentro y el hueco entre especies siga limpio */
  var nPieza = 0;
  function contornos(piezas, cell, gap) {
    var px = function (j) { return (Math.floor(j / 2) * (cell + gap) + (j % 2 ? cell : 0)).toFixed(1); };
    return piezas.filter(function (b) { return b.e.partes.length; }).map(function (b) {
      var c = {}, L = {}, d = "", junta = "", area = "", id = "cl-pz" + (nPieza++);
      b.sh.forEach(function (s) { c[(b.x + s[0]) + "," + (b.y + s[1])] = 1; });
      var en = function (x, y) { return c[x + "," + y]; };
      Object.keys(c).forEach(function (k) {
        var x = +k.split(",")[0], y = +k.split(",")[1];
        L[2 * x + "," + 2 * y] = 1;
        if (en(x + 1, y)) L[(2 * x + 1) + "," + 2 * y] = 1;
        if (en(x, y + 1)) L[2 * x + "," + (2 * y + 1)] = 1;
        if (en(x + 1, y) && en(x, y + 1) && en(x + 1, y + 1)) L[(2 * x + 1) + "," + (2 * y + 1)] = 1;
      });
      Object.keys(L).forEach(function (k) {
        var i = +k.split(",")[0], j = +k.split(",")[1], x0 = px(i), x1 = px(i + 1), y0 = px(j), y1 = px(j + 1);
        var r = "M" + x0 + " " + y0 + "H" + x1 + "V" + y1 + "H" + x0 + "Z";
        area += r; if (i % 2 || j % 2) junta += r;
        if (!L[i + "," + (j - 1)]) d += "M" + x0 + " " + y0 + "H" + x1;
        if (!L[i + "," + (j + 1)]) d += "M" + x0 + " " + y1 + "H" + x1;
        if (!L[(i - 1) + "," + j]) d += "M" + x0 + " " + y0 + "V" + y1;
        if (!L[(i + 1) + "," + j]) d += "M" + x1 + " " + y0 + "V" + y1;
      });
      return '<g data-id="' + esc(b.e.id) + '"><clipPath id="' + id + '"><path d="' + area + '"/></clipPath>' + (junta ? '<path class="cl-junta" d="' + junta + '"/>' : "") +
        '<path class="cl-borde" clip-path="url(#' + id + ')" d="' + d + '"/></g>';
    }).join("");
  }
  /* Al pasar el mouse o llegar con el teclado a cualquier foto, se resalta la pieza completa de su especie */
  function resaltarPieza(el) {
    var marca = function (ev) {
      var c = ev.type === "mouseleave" ? null : ev.target.closest("[data-id]"), id = c && c.dataset.id;
      [].forEach.call(el.querySelectorAll(".cl-mos-svg g"), function (g) { g.classList.toggle("cl-on", g.dataset.id === id); });
    };
    el.addEventListener("mouseover", marca); el.addEventListener("focusin", marca); el.addEventListener("mouseleave", marca); el.addEventListener("focusout", marca);
  }
  var mosaico = {
    mount: function (el, items, cfg) {
      var w = el.clientWidth || 800, cell = w < 520 ? 68 : Math.round(Math.min(120, Math.max(86, w / 16))), /* casillas más grandes en pantallas anchas */ cols = Math.max(4, Math.floor((w + 4) / (cell + 4))), lado = (w - (cols - 1) * 4) / cols;
      el.style.setProperty("--cols", cols); el.style.setProperty("--cell", lado.toFixed(1) + "px");
      if (!el.dataset.pieza) { el.dataset.pieza = "1"; resaltarPieza(el); }
      if (!items.length) { el.innerHTML = '<p class="cl-mos-vacio">Ninguna especie coincide. Prueba con el nombre común, la familia o un jardín.</p>'; return; }
      var piezas = empacar(items, cols), filas = piezas.reduce(function (m, b) { return Math.max(m, b.y + Math.max.apply(null, b.sh.map(function (s) { return s[1]; })) + 1); }, 0);
      el.innerHTML = '<svg class="cl-mos-svg" aria-hidden="true" width="' + w + '" height="' + (filas * (lado + 4) - 4).toFixed(1) + '">' + contornos(piezas, lado, 4) + "</svg>" + piezas.map(function (b) {
        var e = b.e, nombre = esc(e.com), href = esc(conParam(cfg.ficha, "id", e.id));
        if (!e.partes.length) return '<a class="cl-mos-c cl-falta" href="' + href + '" data-id="' + esc(e.id) + '" style="grid-area:' + (b.y + 1) + "/" + (b.x + 1) + '" aria-label="' + nombre + ', sin fotos todavía"><b>?</b>' + nombre + "</a>";
        var cells = b.sh.length === e.partes.length ? b.sh : b.sh.slice(0, 1);
        return cells.map(function (c, i) {
          var p = e.partes[i] || e.partes[0], area = (b.y + c[1] + 1) + "/" + (b.x + c[0] + 1) + (b.sh.length === 4 && e.partes.length === 1 ? "/span 2/span 2" : ""), first = i === 0;
          return '<a class="cl-mos-c' + (first ? " cl-lbl" : "") + '" href="' + href + '" data-id="' + esc(e.id) + '" data-nombre="' + (first ? nombre : "") + '" style="grid-area:' + area + '"' +
            (first ? ' aria-label="' + nombre + ", " + e.partes.length + ' de 5 partes"' : ' tabindex="-1" aria-hidden="true"') + '><img loading="lazy" src="' + esc(foto(cfg, e.fotos[p].f, "chica")) + '" alt=""></a>';
        }).join("");
      }).join("");
    }
  };

  function foto(cfg, nombre, tam) { return cfg.fotos + nombre + cfg.ext + (tam === "chica" ? cfg.chica : cfg.grande); }

  /* ═══ Vistas (una por página de Liferay) ═══ */
  function vColeccion(main, D, cfg) {
    var E = D.arboles.especies, S = { q: "", filtro: "todas" };
    var con = E.filter(function (e) { return e.partes.length; }).length, partes = E.reduce(function (s, e) { return s + e.partes.length; }, 0), tot = E.length * 5;
    main.innerHTML = '<section class="cl-coleccion"><div class="cl-col-head"><div><p class="cl-eyebrow">Itesodex · árboles</p><h1>' + E.length + ' especies en el inventario</h1></div>' +
      '<div class="cl-progreso"><p><b>' + con + "</b> con foto · <b>" + partes + "</b> de " + tot + ' partes fotografiadas</p><div class="cl-barra-p" aria-hidden="true"><i style="width:' + (100 * partes / tot).toFixed(1) + '%"></i></div></div></div>' +
      '<div class="cl-col-tools"><input class="cl-field" type="search" autocomplete="off" placeholder="Busca por nombre, familia o jardín" aria-label="Buscar especie">' +
      '<div class="cl-tabs" role="group" aria-label="Filtrar">' + [["todas", "Todas"], ["con", "Con foto"], ["faltan", "Les faltan partes"], ["sin", "Sin foto"]].map(function (f) { return '<button class="cl-btn" type="button" data-filtro="' + f[0] + '" aria-pressed="' + (S.filtro === f[0]) + '">' + f[1] + "</button>"; }).join("") + "</div></div>" +
      '<div class="cl-mosaico"></div></section>';
    var mos = main.querySelector(".cl-mosaico"), t;
    var lista = function () {
      var q = norm(S.q.trim());
      return E.filter(function (e) {
        var k = e.partes.length;
        if (S.filtro === "con" && !k) return false; if (S.filtro === "sin" && k) return false; if (S.filtro === "faltan" && (k === 0 || k === 5)) return false;
        return !q || [e.sci, e.com, e.fam].concat(Object.keys(e.jar)).some(function (x) { return norm(x).indexOf(q) >= 0; });
      }).sort(function (a, b) { return b.n - a.n; });
    };
    var pinta = function () { mosaico.mount(mos, lista(), cfg); };
    main.querySelector("input").oninput = function (ev) { S.q = ev.target.value; clearTimeout(t); t = setTimeout(pinta, 120); };
    main.querySelector(".cl-tabs").onclick = function (ev) { var b = ev.target.closest("[data-filtro]"); if (!b) return; S.filtro = b.dataset.filtro; main.querySelectorAll("[data-filtro]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); pinta(); };
    var tr; window.addEventListener("resize", function () { clearTimeout(tr); tr = setTimeout(pinta, 150); });
    pinta();
  }

  function vEspecie(main, D, cfg) {
    var e = D.byId[param("id") || ""];
    if (!e) { main.innerHTML = '<div class="cl-card cl-aviso"><b>No encontramos esa especie.</b><p class="cl-muted">Revisa el enlace o búscala en la colección.</p><a class="cl-btn cl-solid" href="' + esc(cfg.coleccion) + '">Ir a la colección</a></div>'; return; }
    var parte = e.partes[e.partes.length - 1] || null;
    var ras = Object.keys(e.ras).map(function (k) { return "<dt>" + RASGO[k] + "</dt><dd>" + esc(e.ras[k]) + "</dd>"; }).join("");
    var jar = Object.keys(e.jar);
    document.title = e.com + " (" + e.sci + ") · Campus Lab";
    main.innerHTML = '<article class="cl-especie"><div class="cl-esp-head"><p class="cl-eyebrow">' + esc(e.fam || "Familia por confirmar") + "</p><h1>" + esc(e.com) + '</h1><p class="cl-sci">' + esc(e.sci) + "</p></div>" +
      '<div class="cl-esp-main"><figure class="cl-foto"><div class="cl-frame"></div><figcaption></figcaption></figure>' +
      '<div class="cl-esp-side"><div class="cl-card cl-anillos"></div><dl class="cl-card cl-datos"><dt>Origen</dt><dd>' + esc(e.ori || "Sin dato todavía") + "</dd>" + ras + "</dl></div></div>" +
      '<section class="cl-card cl-donde"><div><h2>' + e.n + " " + (e.n === 1 ? "árbol" : "árboles") + " en el campus</h2><ul>" + jar.map(function (j) { return "<li><span>" + esc(j) + "</span><b>" + e.jar[j] + "</b></li>"; }).join("") +
      '</ul><a class="cl-btn" href="' + esc(conParam(cfg.paginaMapa, "id", e.id)) + '">Ver en el mapa</a></div><div class="cl-mini"></div></section></article>';
    var frame = main.querySelector(".cl-frame"), pie = main.querySelector("figcaption"), an = main.querySelector(".cl-anillos");
    var pintaFoto = function () {
      if (!parte) { frame.innerHTML = '<div class="cl-vacia"><b>Todavía no hay fotos de esta especie</b><span>Si tienes una, ayúdanos a completar el Itesodex.</span></div>'; pie.innerHTML = ""; return; }
      var f = e.fotos[parte];
      frame.innerHTML = '<img class="cl-in" src="' + esc(foto(cfg, f.f, "grande")) + '" alt="' + esc(NOM[parte] + " de " + e.com + " (" + e.sci + ")") + '">';
      pie.innerHTML = "<span>" + NOM[parte] + " · " + e.partes.length + " de 5 partes fotografiadas</span><span>Foto: " + esc(f.a || "Campus Lab ITESO") + "</span>";
    };
    var pick = function (p) { parte = p; pintaFoto(); anillos.mount(an, e, parte, pick); };
    pintaFoto(); anillos.mount(an, e, parte, pick);
    mapa.mount(main.querySelector(".cl-mini"), D, { hi: [e.id], foco: true, zoom: "hi", ar: 1.4, label: "Ubicación de los " + e.n + " árboles de " + e.com });
  }

  function vMapa(main, D, cfg) {
    var E = D.arboles.especies, S = { id: param("id"), placa: param("placa"), faltan: !param("id") && !param("placa") }; // sin especie ni placa: marca los árboles sin foto
    if (!D.byId[S.id]) S.id = null;
    var nFalt = D.mapa.pts.filter(function (p) { return !E[p[3]].partes.length; }).length;
    var pinta = function () {
      var e = S.id && D.byId[S.id], pl = S.placa && D.placa[S.placa], pe = pl && E[pl[3]];
      var hi = S.faltan ? E.filter(function (x) { return !x.partes.length; }).map(function (x) { return x.id; }) : (e ? [e.id] : []);
      main.innerHTML = '<section class="cl-lugar"><div class="cl-mapa-host"></div><aside class="cl-lugar-side">' +
        '<div class="cl-card"><label for="cl-placa-' + cfg.n + '"><b>Busca un árbol por su placa</b></label><input class="cl-field" id="cl-placa-' + cfg.n + '" inputmode="numeric" autocomplete="off" placeholder="Ej. 1229" value="' + esc(S.placa || "") + '">' +
        (S.placa && !pl ? '<p class="cl-muted">No encontramos la placa ' + esc(S.placa) + ". Revisa el número; las placas nuevas todavía no están en el mapa.</p>" : "") +
        (pe ? '<div class="cl-ficha-placa"><span class="cl-placa">' + pl[0] + "<small>placa</small></span><h3>" + esc(pe.com) + '</h3><p class="cl-sci cl-muted">' + esc(pe.sci) + '</p><a class="cl-btn cl-solid" href="' + esc(conParam(cfg.ficha, "id", pe.id)) + '">Ver ficha</a></div>' : "") + "</div>" +
        '<div class="cl-card"><b>Qué se marca</b><div class="cl-tabs" role="group" aria-label="Marcar en el mapa">' + (e ? '<button class="cl-btn" type="button" data-faltan="0" aria-pressed="' + !S.faltan + '">' + esc(e.com) + "</button>" : "") +
        '<button class="cl-btn" type="button" data-faltan="1" aria-pressed="' + S.faltan + '">Sin foto todavía</button></div>' +
        '<div class="cl-leyenda-mapa">' + (S.faltan ? '<span style="--c:var(--cl-fill)">' + nFalt + " árboles de especies sin foto</span>" : e ? '<span style="--c:var(--cl-fill)">' + esc(e.com) + " (" + e.n + ")</span>" : "") +
        '<span style="--c:color-mix(in srgb, var(--cl-ink2) 30%, var(--cl-sf))">Otros árboles</span></div><p class="cl-muted" style="font-size:.9rem">Toca un punto para ver su placa.' + (S.faltan ? " Cada punto marcado es un árbol cuya especie aún no tiene foto." : "") + "</p></div></aside></section>";
      mapa.mount(main.querySelector(".cl-mapa-host"), D, { hi: hi, foco: hi.length > 0, zoom: pl ? "placa" : "hi", placa: pl ? S.placa : null, controles: true, ar: window.innerWidth < 600 ? 1.1 : 1.5, label: "Mapa de árboles del campus",
        onPick: function (placa) { S.placa = String(placa); pinta(); } });
    };
    var t;
    main.addEventListener("input", function (ev) { if (!ev.target.matches(".cl-field")) return; var v = ev.target.value.replace(/\D/g, ""); clearTimeout(t); t = setTimeout(function () { S.placa = v || null; pinta(); var i = main.querySelector(".cl-field"); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }, 400); });
    main.addEventListener("click", function (ev) { var b = ev.target.closest("[data-faltan]"); if (b) { S.faltan = b.dataset.faltan === "1"; S.placa = null; pinta(); } });
    pinta();
  }

  var VISTAS = { coleccion: vColeccion, especie: vEspecie, mapa: vMapa };
  var n = 0;
  function montar(root) {
    var d = root.dataset;
    var cfg = { n: n++, datos: d.datos, mapa: d.mapa, fotos: d.fotos || "", ext: d.fotosExt || "", grande: d.fotoGrande || "", chica: d.fotoChica || "",
      ficha: d.ficha || "especie", paginaMapa: d.paginaMapa || "mapa", coleccion: d.coleccion || "coleccion" };
    var vista = VISTAS[d.cl]; if (!vista) return;
    root.innerHTML = '<div class="cl-shell"><div class="cl-barra"></div><div class="cl-main">' + CARGA + '<div class="cl-esqueleto" aria-hidden="true"><i style="width:40%"></i><i class="cl-g"></i><i style="width:70%"></i></div></div></div>';
    if (d.barra !== "no") barra.mount(root.querySelector(".cl-barra"));
    var main = root.querySelector(".cl-main"), soltar = seguirCarga(main.querySelector(".cl-carga"), [cfg.datos, cfg.mapa]);
    cargar(cfg).then(function (D) { soltar(); vista(main, preparar(D), cfg); })
      .catch(function (err) { soltar(); main.innerHTML = '<div class="cl-card cl-aviso"><b>No se pudieron cargar los datos.</b><p class="cl-muted">Vuelve a intentar en un momento. (' + esc(err.message) + ")</p></div>"; });
  }

  function iniciar() { aplicarColor(); [].forEach.call(document.querySelectorAll(".cl[data-cl]"), montar); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();
