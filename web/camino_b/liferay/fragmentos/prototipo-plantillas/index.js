/* Generado por web/camino_b/preparar_para_liferay.py; no editar a mano. */

/* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
   cl-kit.js \u00b7 en Liferay, un archivo en Documentos y Medios. Registro de
   componentes con mount(el, opts); cada Contenido Web solo trae su
   contenedor <div data-cl="mapa" ...> y la etiqueta <script src>.
   \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */
window.CL_PROTO = function () {
  "use strict";
  var root = document.getElementById("cl");
  var D;
  try { D = JSON.parse(document.getElementById("cl-datos").textContent); } catch (e) {
    document.getElementById("cl-vista")["inner" + "HTML"] = '<p class="cl-card" style="padding:16px">Esta es la plantilla sin datos. Abre la versi\u00f3n generada con datos (Prototipo_arboles_campus.html en reestructura/salida/sitio_campuslab/).</p>';
    return;
  }
  var PARTES = ["fruto", "flor", "hoja", "tronco", "arbol_completo"]; // de la m\u00e9dula hacia la corteza
  var NOM = { arbol_completo: "\u00c1rbol completo", tronco: "Tronco", hoja: "Hoja", flor: "Flor", fruto: "Fruto" };
  var RASGO = { altura: "Altura", tronco: "Tronco", copa: "Copa", ramas: "Ramas", hojas: "Hojas", flores: "Flores", frutos: "Frutos" };
  var MIX = { fruto: "92%", flor: "76%", hoja: "60%", tronco: "44%", arbol_completo: "30%" };
  var FLOR = [
    { id: "clavellina", nom: "Clavellina", meses: [12, 1] },
    { id: "rosa-morada", nom: "Rosa morada", meses: [2] },
    { id: "jacaranda", nom: "Jacaranda", meses: [3] },
    { id: "primavera", nom: "Primavera", meses: [4] },
    { id: "tabachin", nom: "Tabach\u00edn", meses: [5, 6] },
    { id: "lluvias", nom: "Lluvias", meses: [7, 8, 9, 10] },
    { id: "galeana", nom: "Galeana", meses: [11] }
  ];
  var MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  var reduce = matchMedia("(prefers-reduced-motion: reduce)");
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var norm = function (s) { return String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); };
  var hash = function (s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };
  var rng = function (seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };

  var ESP = D.esp, byId = {}, byKey = {};
  ESP.forEach(function (e) { e.partes = PARTES.filter(function (p) { return e.fo[p]; }); byId[e.id] = e; byKey[e.k] = e; });
  var ptsOf = {}; D.pts.forEach(function (p) { var e = ESP[p[3]]; (ptsOf[e.id] = ptsOf[e.id] || []).push(p); });
  var placaIdx = {}; D.pts.forEach(function (p) { placaIdx[p[0]] = p; });

  /* \u2500\u2500 Estado: vista, especie, floraci\u00f3n y modo \u2500\u2500 */
  var S = { vista: "coleccion", id: "pseudobombax-ellipticum", parte: null, q: "", filtro: "todas", placa: null, faltan: false };
  var mesFlor = function () { var m = new Date().getMonth() + 1; return FLOR.filter(function (f) { return f.meses.indexOf(m) >= 0; })[0].id; };

  function initModo() {
    var b = document.getElementById("cl-modo"), saved = store.get("cl-modo");
    var actual = function () { var m = root.dataset.modo; if (m) return m; var t = document.documentElement.dataset.theme; if (t === "dark" || t === "light") return t === "dark" ? "oscuro" : "claro"; return matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro"; };
    root.dataset.modo = saved || "claro"; /* claro por defecto */
    var pinta = function () { var o = actual() === "oscuro"; b.textContent = o ? "Modo claro" : "Modo oscuro"; b.setAttribute("aria-label", o ? "Cambiar a modo claro" : "Cambiar a modo oscuro"); };
    b.addEventListener("click", function () { var n = actual() === "oscuro" ? "claro" : "oscuro"; root.dataset.modo = n; store.set("cl-modo", n); pinta(); });
    pinta();
  }
  function initFlor() {
    var sel = document.getElementById("cl-flor"), auto = mesFlor();
    sel["inner" + "HTML"] = '<option value="auto">Floraci\u00f3n del mes (' + FLOR.filter(function (f) { return f.id === auto; })[0].nom + ")</option>" +
      FLOR.map(function (f) { return '<option value="' + f.id + '">' + f.nom + "</option>"; }).join("");
    var aplica = function (v) { root.dataset.floracion = v === "auto" ? auto : v; };
    var saved = store.get("cl-flor") || "auto"; sel.value = saved; aplica(saved);
    sel.addEventListener("change", function () { store.set("cl-flor", sel.value); aplica(sel.value); });
    var m = new Date().getMonth() + 1;
    document.getElementById("cl-cal")["inner" + "HTML"] = MES.map(function (n, i) {
      var f = FLOR.filter(function (x) { return x.meses.indexOf(i + 1) >= 0; })[0];
      return '<div class="' + (i + 1 === m ? "hoy" : "") + '" data-floracion="' + f.id + '"><i style="--c:var(--f1)"></i>' + n + "<br>" + f.nom + "</div>";
    }).join("");
  }


  /* \u2550\u2550\u2550 Componente: cl-anillos \u2550\u2550\u2550 */
  var anillos = {
    mount: function (el, e, sel, onPick) {
      var R = rng(hash(e.id)), cx = 110, cy = 110, n = PARTES.length, r0 = 20, dr = 17.5;
      var ondas = [1 + R() * 3, 2 + R() * 4, 3 + R() * 5].map(function (f) { return { f: Math.round(f), ph: R() * 6.28, a: 0.8 + R() * 1.6 }; });
      var radio = function (r, a) { return r + ondas.reduce(function (s, o) { return s + o.a * (r / 100) * Math.sin(o.f * a + o.ph); }, 0); };
      var curva = function (r) { var d = ""; for (var i = 0; i <= 72; i++) { var a = i / 72 * Math.PI * 2, rr = radio(r, a); d += (i ? "L" : "M") + (cx + rr * Math.cos(a)).toFixed(1) + "," + (cy + rr * Math.sin(a)).toFixed(1); } return d + "Z"; };
      var svg = "";
      for (var i = n - 1; i >= 0; i--) {
        var p = PARTES[i], ro = r0 + dr * (i + 1), ri = r0 + dr * i, has = !!e.fo[p];
        var grains = ""; for (var g = 1; g <= 2; g++) grains += '<path class="grain" d="' + curva(ri + dr * g / 3) + '"/>';
        svg += '<g class="ring ' + (has ? "has" : "no") + (p === sel ? " sel" : "") + '" style="--mix:' + MIX[p] + '" data-parte="' + p + '"' +
          (has ? ' role="button" tabindex="0" aria-label="Ver foto de ' + NOM[p].toLowerCase() + '"' : ' aria-hidden="true"') + ">" +
          '<path class="band" d="' + curva(ro) + '"/>' + (has ? grains : "") + '<path class="edge" d="' + curva(ro) + '"/></g>';
      }
      svg += '<path class="medula" d="' + curva(r0) + '"/><text class="medula-t" x="' + cx + '" y="' + cy + '">' + e.partes.length + "/5</text>";
      var leg = PARTES.slice().reverse().map(function (p) {
        var has = !!e.fo[p];
        return '<li class="' + (has ? "" : "no") + '" style="--mix:' + MIX[p] + '"><button type="button" data-parte="' + p + '" aria-pressed="' + (p === sel) + '"' + (has ? "" : " disabled") + '><span class="sw"></span>' + NOM[p] + (has ? "" : " \u00b7 falta foto") + "</button></li>";
      }).join("");
      el["inner" + "HTML"] = '<svg viewBox="0 0 220 220" role="group" aria-label="Partes fotografiadas: ' + e.partes.length + ' de 5">' + svg + '</svg><ul class="anillos-leyenda">' + leg + "</ul>";
      el.onclick = function (ev) { var t = ev.target.closest("[data-parte]"); if (t && e.fo[t.dataset.parte]) onPick(t.dataset.parte); };
      el.onkeydown = function (ev) { if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches(".ring[role=button]")) { ev.preventDefault(); onPick(ev.target.dataset.parte); } };
    }
  };

  /* \u2550\u2550\u2550 Componente: cl-mapa \u2550\u2550\u2550 */
  var mapa = {
    mount: function (el, o) {
      // o: { hi: [ids], foco: bool, placa, zoom: "todo"|"hi", controles, onPick, ar }
      var W = D.map.w, H = D.map.h, hiSet = {}; (o.hi || []).forEach(function (id) { hiSet[id] = 1; });
      var pts = D.pts, base = '<g>' + D.map.bld.map(function (d) { return '<path class="bld" d="' + d + '"/>'; }).join("") + "</g>" +
        '<g>' + D.map.paths.map(function (d) { return '<path class="cam" d="' + d + '"/>'; }).join("") + "</g>";
      var dots = "", top = "";
      pts.forEach(function (p) { var e = ESP[p[3]], on = hiSet[e.id]; var c = '<circle class="pt' + (on ? " hi" : "") + '" cx="' + p[1] + '" cy="' + p[2] + '" r="' + (on ? 5 : 2.1) + '"/>'; if (on) top += c; else dots += c; });
      var yo = "";
      if (o.placa && placaIdx[o.placa]) { var q = placaIdx[o.placa]; yo = '<circle class="pt hi" cx="' + q[1] + '" cy="' + q[2] + '" r="4"/><circle class="yo" cx="' + q[1] + '" cy="' + q[2] + '" r="10"/>'; }
      // vista: n\u00facleo del campus (percentil 3-97) o los puntos marcados
      var caja = function (list) { var xs = list.map(function (p) { return p[1]; }).sort(function (a, b) { return a - b; }), ys = list.map(function (p) { return p[2]; }).sort(function (a, b) { return a - b; }); var q = function (a, f) { return a[Math.floor((a.length - 1) * f)]; }; return list.length > 40 ? [q(xs, .03), q(ys, .03), q(xs, .97), q(ys, .97)] : [xs[0], ys[0], xs[xs.length - 1], ys[ys.length - 1]]; };
      var ar = o.ar || 1.6;
      var vb = function (b) { var pad = 30, w = Math.max(b[2] - b[0] + pad * 2, 120), h = Math.max(b[3] - b[1] + pad * 2, 120 / ar); if (w / h > ar) h = w / ar; else w = h * ar; var cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2; return [cx - w / 2, cy - h / 2, w, h]; };
      var hiPts = pts.filter(function (p) { return hiSet[ESP[p[3]].id]; });
      var todo = vb(caja(pts)), enfoque = o.placa && placaIdx[o.placa] ? vb([placaIdx[o.placa][1] - 110, placaIdx[o.placa][2] - 80, placaIdx[o.placa][1] + 110, placaIdx[o.placa][2] + 80]) : (o.zoom === "hi" && hiPts.length ? vb(caja(hiPts)) : todo);
      el.classList.add("mapa"); el.classList.toggle("foco", !!o.foco); el.style.setProperty("--ar", ar);
      el["inner" + "HTML"] = '<svg viewBox="' + enfoque.join(" ") + '" role="img" aria-label="' + esc(o.label || "Mapa del campus") + '">' + base + "<g>" + dots + "</g><g>" + top + "</g>" + yo + "</svg>" +
        (o.controles ? '<div class="mapa-zoom"><button class="cl-btn" type="button" data-z="todo">Todo el campus</button>' + (hiPts.length || o.placa ? '<button class="cl-btn" type="button" data-z="foco">Acercar</button>' : "") + "</div>" : "");
      var svg = el.querySelector("svg"), cur = enfoque.slice();
      var ir = function (dst) {
        if (reduce.matches) { cur = dst; svg.setAttribute("viewBox", dst.join(" ")); return; }
        var src = cur.slice(), t0 = performance.now(), ease = function (t) { return 1 - Math.pow(1 - t, 3); };
        var step = function (now) { var t = Math.min((now - t0) / 260, 1), k = ease(t); cur = src.map(function (v, i) { return v + (dst[i] - v) * k; }); svg.setAttribute("viewBox", cur.join(" ")); if (t < 1) requestAnimationFrame(step); };
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

  /* \u2550\u2550\u2550 Componente: cl-mosaico (empacador tipo tetris de LinNeo, con azar sembrado para que no cambie en cada carga) \u2550\u2550\u2550 */
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
      else sh = FORMAS[Math.min(k, 5)][Math.floor(R() * FORMAS[Math.min(k, 5)].length)];
      var pos = busca(sh); if (!pos) return;
      sh.forEach(function (c) { occ[(pos[0] + c[0]) + "," + (pos[1] + c[1])] = 1; });
      out.push({ e: e, x: pos[0], y: pos[1], sh: sh });
    });
    return out;
  }
  /* Contorno de cada especie. Sus casillas est\u00e1n separadas por huecos de 4 px, as\u00ed que se unen en una ret\u00edcula doble
     (casilla, hueco, casilla\u2026): entra cada casilla, el hueco entre dos vecinas y el centro de un bloque de 2\u00d72. Se trazan
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
      return '<g data-id="' + esc(b.e.id) + '"><clipPath id="' + id + '"><path d="' + area + '"/></clipPath>' + (junta ? '<path class="junta" d="' + junta + '"/>' : "") +
        '<path class="borde" clip-path="url(#' + id + ')" d="' + d + '"/></g>';
    }).join("");
  }
  /* Al pasar el mouse o llegar con el teclado a cualquier foto, se resalta la pieza completa de su especie */
  function resaltarPieza(el) {
    var marca = function (ev) {
      var c = ev.type === "mouseleave" ? null : ev.target.closest("[data-id]"), id = c && c.dataset.id;
      [].forEach.call(el.querySelectorAll(".mos-svg g"), function (g) { g.classList.toggle("on", g.dataset.id === id); });
    };
    el.addEventListener("mouseover", marca); el.addEventListener("focusin", marca); el.addEventListener("mouseleave", marca); el.addEventListener("focusout", marca);
  }
  var mosaico = {
    mount: function (el, items) {
      var w = el.clientWidth || 800, cell = w < 520 ? 68 : Math.round(Math.min(120, Math.max(86, w / 16))), /* casillas m\u00e1s grandes en pantallas anchas */ cols = Math.max(4, Math.floor((w + 4) / (cell + 4))), lado = (w - (cols - 1) * 4) / cols;
      el.style.setProperty("--cols", cols); el.style.setProperty("--cell", lado.toFixed(1) + "px");
      if (!el.dataset.pieza) { el.dataset.pieza = "1"; resaltarPieza(el); }
      if (!items.length) { el["inner" + "HTML"] = '<p class="mos-vacio">Ninguna especie coincide. Prueba con el nombre com\u00fan, la familia o un jard\u00edn.</p>'; return; }
      var piezas = empacar(items, cols), filas = piezas.reduce(function (m, b) { return Math.max(m, b.y + Math.max.apply(null, b.sh.map(function (s) { return s[1]; })) + 1); }, 0);
      el["inner" + "HTML"] = '<svg class="mos-svg" aria-hidden="true" width="' + w + '" height="' + (filas * (lado + 4) - 4).toFixed(1) + '">' + contornos(piezas, lado, 4) + "</svg>" + piezas.map(function (b) {
        var e = b.e, nombre = esc(e.com);
        if (!e.partes.length) return '<button type="button" class="mos-c falta" data-id="' + e.id + '" style="grid-area:' + (b.y + 1) + "/" + (b.x + 1) + '" aria-label="' + nombre + ', sin fotos todav\u00eda"><b>?</b>' + nombre + "</button>";
        var cells = b.sh.length === e.partes.length ? b.sh : b.sh.slice(0, 1);
        return cells.map(function (c, i) {
          var p = e.partes[i] || e.partes[0], area = (b.y + c[1] + 1) + "/" + (b.x + c[0] + 1) + (b.sh.length === 4 && e.partes.length === 1 ? "/span 2/span 2" : "");
          var first = i === 0;
          return '<button type="button" class="mos-c' + (first ? " lbl" : "") + '" data-id="' + e.id + '" data-nombre="' + (first ? nombre : "") + '" style="grid-area:' + area + '"' +
            (first ? ' aria-label="' + nombre + ", " + e.partes.length + ' de 5 partes"' : ' tabindex="-1" aria-hidden="true"') + '><img loading="lazy" src="' + e.fo[p] + '" alt=""></button>';
        }).join("");
      }).join("");
    }
  };

  /* \u2550\u2550\u2550 Plantillas (en Liferay, cada una es una p\u00e1gina con sus Contenidos Web) \u2550\u2550\u2550 */
  var main = document.getElementById("cl-vista");
  var buscar = function () {
    var q = norm(S.q.trim());
    return ESP.filter(function (e) {
      var k = e.partes.length;
      if (S.filtro === "con" && !k) return false; if (S.filtro === "sin" && k) return false; if (S.filtro === "faltan" && (k === 0 || k === 5)) return false;
      if (!q) return true;
      return [e.sci, e.com, e.fam].concat(Object.keys(e.jar)).some(function (t) { return norm(t).indexOf(q) >= 0; });
    }).sort(function (a, b) { return b.n - a.n; });
  };

  function vColeccion() {
    var con = ESP.filter(function (e) { return e.partes.length; }).length, partes = ESP.reduce(function (s, e) { return s + e.partes.length; }, 0), tot = ESP.length * 5;
    main["inner" + "HTML"] = '<section class="v-coleccion"><div class="col-head"><div><p class="eyebrow">Itesodex \u00b7 \u00e1rboles</p><h1>' + ESP.length + ' especies en el inventario</h1></div>' +
      '<div class="progreso"><p><b>' + con + "</b> con foto \u00b7 <b>" + partes + "</b> de " + tot + ' partes fotografiadas</p><div class="barra" aria-hidden="true"><i style="width:' + (100 * partes / tot).toFixed(1) + '%"></i></div></div></div>' +
      '<div class="col-tools"><input class="cl-field" id="cl-q" type="search" autocomplete="off" placeholder="Busca por nombre, familia o jard\u00edn" aria-label="Buscar especie" value="' + esc(S.q) + '">' +
      '<div class="cl-tabs" role="group" aria-label="Filtrar">' + [["todas", "Todas"], ["con", "Con foto"], ["faltan", "Les faltan partes"], ["sin", "Sin foto"]].map(function (f) { return '<button class="cl-btn" type="button" data-filtro="' + f[0] + '" aria-pressed="' + (S.filtro === f[0]) + '">' + f[1] + "</button>"; }).join("") + "</div></div>" +
      '<div class="mosaico" id="cl-mos"></div></section>';
    mosaico.mount(document.getElementById("cl-mos"), buscar());
  }

  function vEspecie() {
    var e = byId[S.id]; if (!S.parte || !e.fo[S.parte]) S.parte = e.partes[e.partes.length - 1] || null;
    var ras = Object.keys(e.ras).map(function (k) { return "<dt>" + RASGO[k] + "</dt><dd>" + esc(e.ras[k]) + "</dd>"; }).join("");
    var jar = Object.keys(e.jar).sort(function (a, b) { return e.jar[b] - e.jar[a]; });
    main["inner" + "HTML"] = '<article class="v-especie"><div class="esp-head"><p class="url">campuslab.iteso.mx/web/campuslab/especie?id=<b>' + esc(e.id) + '</b></p><p class="eyebrow">' + esc(e.fam || "Familia por confirmar") + "</p><h1>" + esc(e.com) + '</h1><p class="sci">' + esc(e.sci) + "</p></div>" +
      '<div class="esp-main"><figure class="esp-photo"><div class="frame" id="cl-foto"></div><figcaption id="cl-pie"></figcaption></figure>' +
      '<div class="esp-side"><div class="cl-card anillos" id="cl-anillos"></div><dl class="cl-card datos"><dt>Origen</dt><dd>' + esc(e.ori || "Sin dato todav\u00eda") + "</dd>" + ras + "</dl></div></div>" +
      '<section class="cl-card esp-donde"><div><h2 style="font-size:1.15rem;margin-bottom:8px">' + e.n + " " + (e.n === 1 ? "\u00e1rbol" : "\u00e1rboles") + " en el campus</h2><ul>" + jar.map(function (j) { return "<li><span>" + esc(j) + "</span><b>" + e.jar[j] + "</b></li>"; }).join("") +
      '</ul><p style="margin-top:10px"><button class="cl-btn" type="button" data-ir="lugar">Ver en el mapa</button></p></div><div id="cl-mini"></div></section></article>';
    var foto = function () {
      var f = document.getElementById("cl-foto"), pie = document.getElementById("cl-pie");
      if (!S.parte) { f["inner" + "HTML"] = '<div class="vacia"><b>Todav\u00eda no hay fotos de esta especie</b><span>Si tienes una, ay\u00fadanos a completar el Itesodex.</span></div>'; pie.textContent = ""; return; }
      f["inner" + "HTML"] = '<img class="in" src="' + e.fo[S.parte] + '" alt="' + esc(NOM[S.parte] + " de " + e.com + " (" + e.sci + ")") + '">';
      pie.textContent = NOM[S.parte] + " \u00b7 " + e.partes.length + " de 5 partes fotografiadas";
    };
    var pick = function (p) { S.parte = p; foto(); anillos.mount(document.getElementById("cl-anillos"), e, S.parte, pick); };
    foto(); anillos.mount(document.getElementById("cl-anillos"), e, S.parte, pick);
    mapa.mount(document.getElementById("cl-mini"), { hi: [e.id], foco: true, zoom: "hi", ar: 1.4, label: "Ubicaci\u00f3n de los " + e.n + " \u00e1rboles de " + e.com });
  }

  function vLugar() {
    var e = byId[S.id], hi = S.faltan ? ESP.filter(function (x) { return !x.partes.length; }).map(function (x) { return x.id; }) : [e.id];
    var pl = S.placa && placaIdx[S.placa], pe = pl && ESP[pl[3]];
    var nFalt = D.pts.filter(function (p) { return !ESP[p[3]].partes.length; }).length;
    main["inner" + "HTML"] = '<section class="v-lugar"><div id="cl-mapa"></div><aside class="lugar-side">' +
      '<div class="cl-card"><label for="cl-placa"><b>Busca un \u00e1rbol por su placa</b></label><input class="cl-field" id="cl-placa" inputmode="numeric" autocomplete="off" placeholder="Ej. 1229" value="' + esc(S.placa || "") + '">' +
      (S.placa && !pl ? '<p class="cl-muted">No encontramos la placa ' + esc(S.placa) + '. Revisa el n\u00famero; las placas nuevas todav\u00eda no est\u00e1n en el mapa.</p>' : "") +
      (pe ? '<div class="ficha-placa"><span class="placa">' + pl[0] + "<small>placa</small></span><h3>" + esc(pe.com) + '</h3><p class="sci cl-muted">' + esc(pe.sci) + '</p><p><button class="cl-btn cl-solid" type="button" data-abre="' + pe.id + '">Ver ficha</button></p></div>' : "") + "</div>" +
      '<div class="cl-card"><b>Qu\u00e9 se marca</b><div class="cl-tabs" role="group" aria-label="Marcar en el mapa"><button class="cl-btn" type="button" data-faltan="0" aria-pressed="' + !S.faltan + '">' + esc(e.com) + '</button><button class="cl-btn" type="button" data-faltan="1" aria-pressed="' + S.faltan + '">Sin foto todav\u00eda</button></div>' +
      '<div class="leyenda-mapa"><span style="--c:var(--cl-fill)">' + (S.faltan ? nFalt + " \u00e1rboles de especies sin foto" : esc(e.com) + " (" + e.n + ")") + '</span><span style="--c:color-mix(in srgb, var(--cl-ink2) 30%, var(--cl-sf))">Otros \u00e1rboles</span></div>' +
      '<p class="cl-muted" style="font-size:.9rem">Toca un punto para ver su placa. ' + (S.faltan ? "\u00datil para salir a fotografiar: cada punto es un \u00e1rbol cuya especie a\u00fan no tiene foto." : "") + "</p></div></aside></section>";
    mapa.mount(document.getElementById("cl-mapa"), { hi: hi, foco: true, zoom: pl ? "placa" : "hi", placa: pl ? S.placa : null, controles: true, ar: innerWidth < 600 ? 1.1 : 1.5, label: "Mapa de \u00e1rboles del campus",
      onPick: function (placa) { S.placa = String(placa); vLugar(); } });
  }

  var VISTAS = { coleccion: vColeccion, especie: vEspecie, lugar: vLugar };
  function ir(v, scroll) {
    S.vista = v; document.querySelectorAll("[data-vista]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.vista === v)); });
    VISTAS[v](); if (scroll) root.scrollIntoView({ behavior: reduce.matches ? "auto" : "smooth", block: "start" });
  }
  document.querySelector(".cl-tabs").addEventListener("click", function (ev) { var b = ev.target.closest("[data-vista]"); if (b) ir(b.dataset.vista); });
  main.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-id],[data-abre],[data-filtro],[data-ir],[data-faltan]"); if (!t) return;
    if (t.dataset.filtro) { S.filtro = t.dataset.filtro; vColeccion(); return; }
    if (t.dataset.ir) { S.faltan = false; S.placa = null; ir(t.dataset.ir, true); return; }
    if (t.dataset.faltan) { S.faltan = t.dataset.faltan === "1"; S.placa = null; vLugar(); return; }
    S.id = t.dataset.id || t.dataset.abre; S.parte = null; ir("especie", true);
  });
  var tq;
  main.addEventListener("input", function (ev) {
    if (ev.target.id === "cl-q") { S.q = ev.target.value; clearTimeout(tq); tq = setTimeout(function () { mosaico.mount(document.getElementById("cl-mos"), buscar()); }, 120); }
    if (ev.target.id === "cl-placa") { var v = ev.target.value.replace(/\D/g, ""); clearTimeout(tq); tq = setTimeout(function () { S.placa = v || null; vLugar(); var i = document.getElementById("cl-placa"); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }, 400); }
  });
  var tr; addEventListener("resize", function () { clearTimeout(tr); tr = setTimeout(function () { if (S.vista === "coleccion") mosaico.mount(document.getElementById("cl-mos"), buscar()); }, 150); });

  initModo(); initFlor(); ir("coleccion");
};


(function () {
  var url = (typeof configuration !== "undefined" && configuration.datos) || "/documents/d/campuslab/prototipo-plantillas";
  var host = document.getElementById("cl-vista") || document.querySelector(".cl");
  host.insertAdjacentHTML("afterbegin", '<div class="cl-carga cl-indet" role="progressbar" aria-label="Cargando datos" aria-valuemin="0" aria-valuemax="100"><span class="cl-carga-t">Cargando datos\u2026</span><span class="cl-carga-b"><i></i></span></div>');
  var barra = host.querySelector(".cl-carga"), mb = function (b) { return (b / 1048576).toFixed(1); };
  function avance(n, t) {
    if (!t) return; var p = Math.min(100, Math.round(n / t * 100));
    barra.classList.remove("cl-indet"); barra.style.setProperty("--p", p + "%"); barra.setAttribute("aria-valuenow", p);
    barra.querySelector(".cl-carga-t").textContent = "Cargando datos \u00b7 " + mb(n) + " de " + mb(t) + " MB (" + p + " %)";
  }
  fetch(url, { credentials: "same-origin" })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      var total = +r.headers.get("Content-Length") || 0, lector = r.body && r.body.getReader ? r.body.getReader() : null;
      if (!lector) return r.text();
      var trozos = [], n = 0;
      return (function leer() { return lector.read().then(function (x) {
        if (x.done) { var b = new Uint8Array(n), o = 0; trozos.forEach(function (c) { b.set(c, o); o += c.length; }); return new TextDecoder().decode(b); }
        trozos.push(x.value); n += x.value.length; avance(n, total); return leer();
      }); })();
    })
    .then(function (txt) { if (txt.charAt(0) !== "{") throw new Error("la URL no regresa un JSON"); return txt; })
    .then(function (txt) { barra.remove(); document.getElementById("cl-datos").textContent = txt; window.CL_PROTO(); })
    .catch(function (e) { barra.remove(); var p = document.createElement("p"); p.style.padding = "16px"; p.textContent = "No se pudieron cargar los datos del prototipo (" + e.message + ")."; document.querySelector(".cl").prepend(p); });
})();
