/* Generado por web/scripts/preparar_para_liferay.py; no editar a mano. */

window.CL_PROTO = function () {
  "use strict";
  var root = document.getElementById("cl"), D;
  try { D = JSON.parse(document.getElementById("datos").textContent); } catch (e) { document.getElementById("grupos")["inner" + "HTML"] = '<p class="cl-card" style="padding:16px">Esta es la plantilla sin datos. Abre Componentes_campuslab.html en catalogo/salida/sitio_campuslab/.</p>'; return; }
  var reduce = matchMedia("(prefers-reduced-motion: reduce)");
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var norm = function (s) { return String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); };
  var NOM = { arbol_completo: "\u00c1rbol completo", tronco: "Tronco", hoja: "Hoja", flor: "Flor", fruto: "Fruto" };
  var PARTES = ["arbol_completo", "tronco", "hoja", "flor", "fruto"];
  var FLOR = [["clavellina", "Clavellina", [12, 1]], ["rosa-morada", "Rosa morada", [2]], ["jacaranda", "Jacaranda", [3]], ["primavera", "Primavera", [4]], ["tabachin", "Tabach\u00edn", [5, 6]], ["lluvias", "Lluvias", [7, 8, 9, 10]], ["galeana", "Galeana", [11]]];
  var florMes = function (m) { return FLOR.filter(function (f) { return f[2].indexOf(m) >= 0; })[0]; };
  var by = {}; D.sel.forEach(function (e) { by[e.id] = e; });
  var rosa = by["tabebuia-rosea"], ceiba = by["ceiba-speciosa"], jac = by["jacaranda-mimosifolia"];

  /* \u2500\u2500 modo y floraci\u00f3n (igual que en las plantillas) \u2500\u2500 */
  (function () {
    var b = document.getElementById("modo"), s = store.get("cl-modo");
    var actual = function () { var m = root.dataset.modo; if (m) return m; var t = document.documentElement.dataset.theme; if (t) return t === "dark" ? "oscuro" : "claro"; return matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro"; };
    if (s) root.dataset.modo = s; /* sin elecci\u00f3n guardada, el del dispositivo */
    var pinta = function () { var o = actual() === "oscuro"; b.textContent = o ? "Modo claro" : "Modo oscuro"; b.setAttribute("aria-label", o ? "Cambiar a modo claro" : "Cambiar a modo oscuro"); };
    b.onclick = function () { var n = actual() === "oscuro" ? "claro" : "oscuro"; root.dataset.modo = n; store.set("cl-modo", n); pinta(); document.dispatchEvent(new CustomEvent("cl-modo")); };
    /* "cl-modo": el Marco y los dem\u00e1s fragmentos avisan cuando alguien cambia el modo; todos leen la misma elecci\u00f3n guardada */
    document.addEventListener("cl-modo", function () { var s = store.get("cl-modo"); if (s) root.dataset.modo = s; else delete root.dataset.modo; pinta(); document.dispatchEvent(new Event("cl:color")); });
    pinta();
    var sel = document.getElementById("flor"), auto = florMes(new Date().getMonth() + 1);
    sel["inner" + "HTML"] = '<option value="auto">Floraci\u00f3n del mes (' + auto[1] + ")</option>" + FLOR.map(function (f) { return '<option value="' + f[0] + '">' + f[1] + "</option>"; }).join("");
    var ap = function (v) { root.dataset.floracion = v === "auto" ? auto[0] : v; document.dispatchEvent(new Event("cl:color")); };
    sel.value = store.get("cl-flor") || "auto"; ap(sel.value);
    sel.onchange = function () { store.set("cl-flor", sel.value); ap(sel.value); document.dispatchEvent(new CustomEvent("cl-flor")); };
    document.addEventListener("cl-flor", function () { sel.value = store.get("cl-flor") || "auto"; ap(sel.value); }); /* la floraci\u00f3n vale para todo el sitio */
  })();

  /* \u2500\u2500 cat\u00e1logo de muestras \u2500\u2500 */
  var G = [
    ["Entrada y scroll", "aparecen cuando llegas a ellas", [
      [1, "Revelado de foto", "La foto se descubre de abajo hacia arriba con un acercamiento suave.", "Foto principal de la ficha, portada de cada jard\u00edn.", "Solo CSS", "rev"],
      [2, "Cifras que cuentan", "Los n\u00fameros suben desde cero al verse.", "Portada del Itesodex, p\u00e1gina de Campus Lab.", "CSS + JS m\u00ednimo", "cifras"],
      [3, "Anillos que crecen", "Los anillos del tronco crecen uno por uno, del centro hacia afuera. Toca un anillo para ver qu\u00e9 parte es.", "Ficha de especie, al abrirla.", "Solo CSS (SVG)", "grow"]
    ]],
    ["Fotos", "para ver m\u00e1s de una especie", [
      [4, "Comparador", "Arrastra la l\u00ednea para pasar de una foto a otra.", "\u00c1rbol completo contra flor; secas contra lluvias; antes y despu\u00e9s de una poda.", "CSS + JS m\u00ednimo", "cmp"],
      [5, "Carrusel de partes", "Desliza con el dedo; los puntos dicen en cu\u00e1l vas.", "Fotos por parte en la ficha, en celular.", "CSS + JS m\u00ednimo", "carr"],
      [6, "Tarjeta que se voltea", "Al frente la foto; atr\u00e1s los datos y las partes que tiene.", "Itesodex y juegos para visitas escolares.", "Solo CSS", "flip"]
    ]],
    ["B\u00fasqueda y filtros", "para encontrar r\u00e1pido", [
      [7, "B\u00fasqueda con sugerencias", "Sugiere mientras escribes, sin importar acentos. Se maneja con flechas y Enter.", "Buscador general de especies (las 247).", "JS peque\u00f1o", "ac"],
      [8, "Filtro con reacomodo", "Al filtrar, las tarjetas se mueven a su lugar nuevo en vez de saltar.", "Colecci\u00f3n e Itesodex.", "JS peque\u00f1o", "fg"],
      [9, "Placa tipo tablero", "El n\u00famero de placa cae d\u00edgito por d\u00edgito, como un tablero de estaci\u00f3n.", "B\u00fasqueda por placa, letreros de jard\u00edn.", "Solo CSS", "flap"]
    ]],
    ["Mapa", "", [
      [10, "Puntos que aparecen y pulso", "Los \u00e1rboles aparecen en orden y el elegido late suave para encontrarlo.", "Mapa de jardines y la ficha de especie.", "Solo CSS (SVG)", "mapa"]
    ]],
    ["Temporada", "cambian con la floraci\u00f3n del mes", [
      [11, "P\u00e9talos o lluvia", "Caen p\u00e9talos del color de la floraci\u00f3n; en lluvias, gotas. Se detiene fuera de pantalla.", "Portada del sitio o encabezado de temporada.", "Canvas, sin librer\u00edas", "temp"],
      [12, "Recorrido del a\u00f1o", "Pasa por los doce meses y muestra c\u00f3mo cambia la paleta.", "P\u00e1gina de Campus Lab o calendario de floraci\u00f3n.", "CSS + JS m\u00ednimo", "anio"]
    ]],
    ["Letreros y placas", "para llevar el sitio al jard\u00edn", [
      [15, "\u00c1rbol con su QR", "Un \u00e1rbol de cubos parado sobre el QR de su ficha. Al tocarlo se pliega y queda el c\u00f3digo, listo para escanear o descargar e imprimir.", "Letreros de jard\u00edn, placas de \u00e1rbol y la ficha de especie. Idea de ICQR, de Louis Raill\u00e9.", "Canvas, sin librer\u00edas", "qr"]
    ]],
    ["Estados", "mientras carga o al compartir", [
      [13, "Esqueleto de carga", "Mientras llega el JSON, se ve la forma de la ficha en vez de un c\u00edrculo girando.", "Todas las piezas que leen datos.", "Solo CSS", "skel"],
      [14, "Copiar enlace y aviso", "Copia el enlace de la ficha y confirma con un aviso corto.", "Bot\u00f3n de compartir en cada ficha.", "JS peque\u00f1o", "share"]
    ]]
  ];
  var REPLAY = { rev: 1, cifras: 1, grow: 1, flap: 1, mapa: 1, anio: 1, skel: 1 };
  document.getElementById("grupos")["inner" + "HTML"] = G.map(function (g) {
    return '<section class="grupo"><h2>' + g[0] + (g[1] ? " <small>" + g[1] + "</small>" : "") + '</h2><div class="demos">' + g[2].map(function (d) {
      return '<article class="cl-card demo" id="d' + d[0] + '"><div class="stage" data-demo="' + d[5] + '"></div><div class="info"><h3><span class="n">' + d[0] + "</span>" + d[1] + "</h3><p>" + d[2] + "</p><p><b>D\u00f3nde:</b> " + d[3] + '</p></div><div class="pie"><span class="peso">' + d[4] + "</span>" +
        (REPLAY[d[5]] ? '<button class="cl-btn" type="button" data-replay="' + d[5] + '">Repetir</button>' : "") + "</div></article>";
    }).join("") + "</div></section>";
  }).join("");
  var st = function (k) { return document.querySelector('[data-demo="' + k + '"]'); };
  var M = {};

  /* 1 */ M.rev = function (el) { el["inner" + "HTML"] = '<div class="rev"><img src="' + rosa.fo.flor + '" alt="Flor de rosa morada (Tabebuia rosea)"></div>'; var r = el.firstChild; if (reduce.matches) return; r.classList.add("pre"); r.getBoundingClientRect(); requestAnimationFrame(function () { r.classList.add("go"); r.classList.remove("pre"); }); };
  /* 2 */ M.cifras = function (el) {
    var datos = [[247, "especies"], [3569, "\u00e1rboles con placa"], [373, "partes con foto"]];
    el["inner" + "HTML"] = '<div class="cifras">' + datos.map(function (d) { return '<div class="cifra"><b data-n="' + d[0] + '">' + d[0].toLocaleString("es-MX") + "</b><span>" + d[1] + "</span></div>"; }).join("") + "</div>";
    if (reduce.matches) return;
    el.querySelectorAll("[data-n]").forEach(function (b) { var n = +b.dataset.n, t0 = performance.now(); var tick = function (t) { var p = Math.min((t - t0) / 1100, 1); b.textContent = Math.round(n * (1 - Math.pow(1 - p, 3))).toLocaleString("es-MX"); if (p < 1) requestAnimationFrame(tick); }; requestAnimationFrame(tick); });
  };
  /* 3 */ M.grow = function (el) {
    var e = by["pseudobombax-ellipticum"], mix = { fruto: "92%", flor: "76%", hoja: "60%", tronco: "44%", arbol_completo: "30%" }, orden = ["fruto", "flor", "hoja", "tronco", "arbol_completo"];
    /* contorno ondulado de tronco, el mismo para todos los anillos (no se cruzan) y fijo por especie */
    var h = 2166136261; for (var k = 0; k < e.id.length; k++) { h ^= e.id.charCodeAt(k); h = Math.imul(h, 16777619); }
    var R = function () { h = Math.imul(h ^ h >>> 15, 2246822507) + 0x6D2B79F5 | 0; return (h >>> 0) / 4294967296; };
    var ondas = [2, 3, 5].map(function (f) { return { f: f, ph: R() * 6.28, a: 0.8 + R() * 1.4 }; });
    var curva = function (r) { var d = ""; for (var i = 0; i <= 72; i++) { var a = i / 72 * Math.PI * 2, rr = r + ondas.reduce(function (s, o) { return s + o.a * (r / 90) * Math.sin(o.f * a + o.ph); }, 0); d += (i ? "L" : "M") + (100 + rr * Math.cos(a)).toFixed(1) + "," + (100 + rr * Math.sin(a)).toFixed(1); } return d + "Z"; };
    var r0 = 22, dr = 15, n = Object.keys(e.fo).length;
    el["inner" + "HTML"] = '<div class="grow' + (reduce.matches ? "" : " pre") + '"><svg viewBox="0 0 200 200" role="group" aria-label="Anillos de ' + esc(e.com) + ": " + n + ' de 5 partes con foto">' +
      orden.map(function (p, i) { var has = !!e.fo[p]; return '<g class="ring ' + (has ? "has" : "no") + '" role="button" tabindex="0" aria-pressed="false" data-parte="' + p + '" aria-label="' + NOM[p] + (has ? ", con foto" : ", falta foto") + '" style="--mix:' + mix[p] + ";--d:" + i * 110 + 'ms"><path d="' + curva(r0 + dr * (i + 1)) + curva(r0 + dr * i) + '"/></g>'; }).join("") +
      '<path class="medula" d="' + curva(r0) + '"/><text x="100" y="100">' + n + '/5</text></svg><output aria-live="polite">Toca un anillo</output></div>';
    var g = el.firstChild, out = g.querySelector("output");
    var elige = function (r) { g.querySelectorAll(".ring").forEach(function (x) { x.setAttribute("aria-pressed", String(x === r)); }); out.textContent = NOM[r.dataset.parte] + (e.fo[r.dataset.parte] ? " \u00b7 con foto" : " \u00b7 falta foto"); };
    g.onclick = function (ev) { var r = ev.target.closest(".ring"); if (r) elige(r); };
    g.onkeydown = function (ev) { var r = ev.target.closest(".ring"); if (r && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); elige(r); } };
    if (!reduce.matches) { g.getBoundingClientRect(); requestAnimationFrame(function () { g.classList.add("go"); g.classList.remove("pre"); }); }
  };
  /* 4 */ M.cmp = function (el) {
    el["inner" + "HTML"] = '<div class="cmp" style="--x:50%"><img src="' + ceiba.fo.arbol_completo + '" alt="Ceiba brasile\u00f1a, \u00e1rbol completo"><img class="b" src="' + ceiba.fo.flor + '" alt="Ceiba brasile\u00f1a, flor"><span class="linea"></span><span class="et l">\u00c1rbol</span><span class="et r">Flor</span>' +
      '<input type="range" min="0" max="100" value="50" aria-label="Mover la l\u00ednea entre \u00e1rbol completo y flor"></div>';
    var c = el.firstChild; c.querySelector("input").oninput = function (ev) { c.style.setProperty("--x", ev.target.value + "%"); };
  };
  /* 5 */ M.carr = function (el) {
    var e = by["magnolia-grandiflora"], ps = PARTES.filter(function (p) { return e.fo[p]; });
    el["inner" + "HTML"] = '<div class="carr"><div class="carr-track" tabindex="0" aria-label="Fotos por parte de ' + esc(e.com) + '">' + ps.map(function (p) { return '<figure><img src="' + e.fo[p] + '" alt="' + NOM[p] + " de " + esc(e.com) + '"><figcaption>' + NOM[p] + "</figcaption></figure>"; }).join("") +
      '</div><div class="carr-nav"><div class="carr-dots">' + ps.map(function (p, i) { return '<button type="button" aria-label="Ir a ' + NOM[p].toLowerCase() + '" aria-current="' + (i === 0) + '"></button>'; }).join("") + "</div></div></div>";
    var tr = el.querySelector(".carr-track"), dots = el.querySelectorAll(".carr-dots button"), figs = tr.querySelectorAll("figure");
    dots.forEach(function (d, i) { d.onclick = function () { tr.scrollTo({ left: figs[i].offsetLeft - (tr.clientWidth - figs[i].clientWidth) / 2, behavior: reduce.matches ? "auto" : "smooth" }); }; });
    /* el punto activo es el de la foto m\u00e1s cercana al centro (con dos fotos a la vista, "la m\u00e1s visible" fallaba) */
    var marca = function () {
      var c = tr.scrollLeft + tr.clientWidth / 2, i = 0, mejor = Infinity;
      figs.forEach(function (f, j) { var d = Math.abs(f.offsetLeft + f.clientWidth / 2 - c); if (d < mejor) { mejor = d; i = j; } });
      dots.forEach(function (d, j) { d.setAttribute("aria-current", String(i === j)); });
    };
    var raf; tr.addEventListener("scroll", function () { cancelAnimationFrame(raf); raf = requestAnimationFrame(marca); }, { passive: true });
    marca();
  };
  /* 6 */ M.flip = function (el) {
    var e = by["delonix-regia"];
    el["inner" + "HTML"] = '<button class="flip" type="button" aria-pressed="false" aria-label="Voltear la tarjeta de ' + esc(e.com) + '"><span class="flip-in"><span class="cara frente"><img src="' + e.fo.flor + '" alt=""><span>' + esc(e.com) + '</span></span><span class="cara dorso"><b>' + esc(e.com) + '</b><span class="sci cl-muted">' + esc(e.sci) + "</span><span>" + e.n + " \u00e1rboles en el campus</span><span>" + esc(e.fam) + '</span><span class="dots">' + PARTES.map(function (p) { return '<i class="' + (e.fo[p] ? "on" : "") + '" title="' + NOM[p] + '"></i>'; }).join("") + "</span><span class=\"muted\">" + Object.keys(e.fo).length + " de 5 partes</span></span></span></button>";
    var b = el.firstChild; b.onclick = function () { b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true")); };
  };
  /* 7 */ M.ac = function (el) {
    el["inner" + "HTML"] = '<div class="ac"><label class="cl-sr" for="ac-q">Buscar especie</label><input class="cl-field" id="ac-q" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="ac-l" autocomplete="off" placeholder="Busca una especie"><ul id="ac-l" role="listbox" hidden></ul>' +
      '<p class="ac-pista">Prueba con <button type="button">tabach</button> <button type="button">ceiba</button> <button type="button">quercus</button></p></div>';
    var q = el.querySelector("input"), ul = el.querySelector("ul"), sel = -1, res = [], t;
    var marca = function (txt, k) { var n = norm(txt), i = n.indexOf(k); return i < 0 ? esc(txt) : esc(txt.slice(0, i)) + "<mark>" + esc(txt.slice(i, i + k.length)) + "</mark>" + esc(txt.slice(i + k.length)); };
    var pinta = function () {
      var k = norm(q.value.trim()); if (!k) { ul.hidden = true; q.setAttribute("aria-expanded", "false"); return; }
      res = D.nombres.filter(function (n) { return norm(n[1]).indexOf(k) >= 0 || norm(n[2]).indexOf(k) >= 0; }).slice(0, 8); sel = res.length ? 0 : -1;
      ul["inner" + "HTML"] = res.length ? res.map(function (n, i) { return '<li role="option" id="ac-' + i + '" aria-selected="' + (i === sel) + '"><span>' + marca(n[1], k) + "</span><small>" + marca(n[2], k) + "</small></li>"; }).join("") : '<li class="vacio" role="option" aria-disabled="true">Sin coincidencias. Prueba con el nombre cient\u00edfico.</li>';
      ul.hidden = false; q.setAttribute("aria-expanded", "true"); q.setAttribute("aria-activedescendant", sel >= 0 ? "ac-" + sel : "");
    };
    var mueve = function (d) { if (!res.length) return; sel = (sel + d + res.length) % res.length; ul.querySelectorAll("li").forEach(function (li, i) { li.setAttribute("aria-selected", String(i === sel)); }); q.setAttribute("aria-activedescendant", "ac-" + sel); ul.children[sel].scrollIntoView({ block: "nearest" }); };
    var elige = function (i) { if (!res[i]) return; q.value = res[i][1]; ul.hidden = true; q.setAttribute("aria-expanded", "false"); };
    q.oninput = function () { clearTimeout(t); t = setTimeout(pinta, 150); };
    q.onkeydown = function (ev) { if (ev.key === "ArrowDown") { ev.preventDefault(); mueve(1); } else if (ev.key === "ArrowUp") { ev.preventDefault(); mueve(-1); } else if (ev.key === "Enter") { ev.preventDefault(); elige(sel); } else if (ev.key === "Escape") { ul.hidden = true; q.setAttribute("aria-expanded", "false"); } };
    ul.onclick = function (ev) { var li = ev.target.closest("li[id]"); if (li) elige(+li.id.slice(3)); };
    /* sin nada escrito, unas palabras de ejemplo para que el recuadro no quede vac\u00edo */
    el.querySelector(".ac-pista").onclick = function (ev) { var b = ev.target.closest("button"); if (!b) return; q.value = b.textContent; q.focus(); pinta(); };
  };
  /* 8 */ M.fg = function (el) {
    var items = D.sel, filtro = "todas";
    el["inner" + "HTML"] = '<div class="flipgrid"><div class="fg-chips" role="group" aria-label="Filtrar">' + [["todas", "Todas"], ["con", "Con foto"], ["sin", "Sin foto"]].map(function (f) { return '<button class="cl-btn" type="button" data-f="' + f[0] + '" aria-pressed="' + (f[0] === filtro) + '">' + f[1] + "</button>"; }).join("") + '</div><div class="fg"></div></div>';
    var g = el.querySelector(".fg"), nodos = {};
    items.forEach(function (e) { var k = Object.keys(e.fo), d = document.createElement("div"); d.className = k.length ? "f" : ""; d["inner" + "HTML"] = k.length ? '<img src="' + e.fo[k[0]] + '" alt="' + esc(e.com) + '">' : esc(e.com); nodos[e.id] = d; g.appendChild(d); });
    el.querySelector(".fg-chips").onclick = function (ev) {
      var b = ev.target.closest("[data-f]"); if (!b) return; filtro = b.dataset.f;
      el.querySelectorAll("[data-f]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      var antes = {}; items.forEach(function (e) { if (nodos[e.id].isConnected) antes[e.id] = nodos[e.id].getBoundingClientRect(); });
      items.forEach(function (e) { var k = Object.keys(e.fo).length, ok = filtro === "todas" || (filtro === "con" ? k : !k); if (ok && !nodos[e.id].isConnected) g.appendChild(nodos[e.id]); if (!ok && nodos[e.id].isConnected) g.removeChild(nodos[e.id]); });
      items.forEach(function (e) { if (nodos[e.id].isConnected) g.appendChild(nodos[e.id]); });
      if (reduce.matches) return;
      items.forEach(function (e, i) { var n = nodos[e.id]; if (!n.isConnected) return; var r = n.getBoundingClientRect(), a = antes[e.id];
        if (a) n.animate([{ transform: "translate(" + (a.left - r.left) + "px," + (a.top - r.top) + "px)" }, { transform: "none" }], { duration: 320, easing: "cubic-bezier(0.77, 0, 0.175, 1)" });
        else n.animate([{ opacity: 0, transform: "scale(.95)" }, { opacity: 1, transform: "none" }], { duration: 220, delay: i * 20, easing: "cubic-bezier(0.23, 1, 0.32, 1)", fill: "backwards" }); });
    };
  };
  /* 9 */ var flapN = 0; M.flap = function (el) {
    var placas = [1229, 3011, 562, 1982, 2905], p = String(placas[flapN++ % placas.length]).padStart(4, "0");
    el["inner" + "HTML"] = '<div class="flap-wrap"><div class="flap" role="img" aria-label="Placa ' + +p + '">' + p.split("").map(function (c, i) { return '<span class="d" style="--d:' + i * 80 + 'ms"><span>' + c + "</span></span>"; }).join("") + '</div><span class="placa">' + +p + ' <small style="font-weight:500;letter-spacing:0">placa</small></span></div>';
    requestAnimationFrame(function () { el.querySelectorAll(".d").forEach(function (d) { d.classList.add("go"); }); });
  };
  /* 10 */ M.mapa = function (el) {
    var pts = D.pts, cx = 0, cy = 0; pts.forEach(function (p) { cx += p[1]; cy += p[2]; }); cx /= pts.length; cy /= pts.length;
    var w = 360, h = 202, x0 = cx - w / 2, y0 = cy - h / 2, dentro = pts.filter(function (p) { return p[1] > x0 && p[1] < x0 + w && p[2] > y0 && p[2] < y0 + h; });
    var yo = dentro[Math.floor(dentro.length / 2)];
    el["inner" + "HTML"] = '<div class="minimapa"><svg viewBox="' + [x0, y0, w, h].join(" ") + '" role="img" aria-label="Mapa del campus con un \u00e1rbol marcado">' + D.map.bld.map(function (d) { return '<path class="bld" d="' + d + '"/>'; }).join("") + D.map.paths.map(function (d) { return '<path class="cam" d="' + d + '"/>'; }).join("") +
      dentro.map(function (p) { return '<circle class="pt" cx="' + p[1] + '" cy="' + p[2] + '" r="1.8" style="--d:' + Math.round((p[1] - x0) * 2.4) + 'ms"/>'; }).join("") +
      '<circle class="pulso" cx="' + yo[1] + '" cy="' + yo[2] + '" r="4"/><circle class="yo" cx="' + yo[1] + '" cy="' + yo[2] + '" r="3.2"/></svg></div>';
    var m = el.firstChild; requestAnimationFrame(function () { m.classList.add("go"); });
  };
  /* 11 */ M.temp = function (el) {
    el["inner" + "HTML"] = '<div class="temp"><canvas aria-hidden="true"></canvas><p id="temp-n"></p></div>';
    var cv = el.querySelector("canvas"), cx = cv.getContext("2d"), parts = [], raf = 0, vis = false, W = 0, H = 0, col = "#888", col2 = "#888", lluvia = false;
    var lee = function () { var cs = getComputedStyle(el.firstChild); var probe = document.createElement("span"); el.appendChild(probe); probe.style.color = "var(--f1)"; col = getComputedStyle(probe).color; probe.style.color = "var(--f2)"; col2 = getComputedStyle(probe).color; probe.remove(); lluvia = root.dataset.floracion === "lluvias"; var f = FLOR.filter(function (x) { return x[0] === root.dataset.floracion; })[0]; document.getElementById("temp-n").textContent = f ? f[1] : ""; };
    var size = function () { var r = cv.getBoundingClientRect(), d = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height; cv.width = W * d; cv.height = H * d; cx.setTransform(d, 0, 0, d, 0, 0); };
    var semilla = function () { parts = []; for (var i = 0; i < 46; i++) parts.push({ x: Math.random() * W, y: Math.random() * H, s: 4 + Math.random() * 6, v: lluvia ? 3 + Math.random() * 3 : .35 + Math.random() * .6, a: Math.random() * 6.28, w: .01 + Math.random() * .02, c: Math.random() < .8 }); };
    var dibuja = function () {
      cx.clearRect(0, 0, W, H);
      parts.forEach(function (p) {
        if (lluvia) { cx.strokeStyle = p.c ? col2 : col; cx.globalAlpha = .55; cx.lineWidth = 1.4; cx.beginPath(); cx.moveTo(p.x, p.y); cx.lineTo(p.x - 1.5, p.y + p.s * 2.2); cx.stroke(); }
        else { cx.fillStyle = p.c ? col : col2; cx.globalAlpha = .85; cx.save(); cx.translate(p.x, p.y); cx.rotate(p.a); cx.beginPath(); cx.ellipse(0, 0, p.s, p.s * .55, 0, 0, 6.28); cx.fill(); cx.restore(); }
      }); cx.globalAlpha = 1;
    };
    var paso = function () { parts.forEach(function (p) { p.y += p.v; p.a += p.w; p.x += lluvia ? -.4 : Math.sin(p.a) * .5; if (p.y > H + 12) { p.y = -12; p.x = Math.random() * W; } }); dibuja(); raf = vis && !reduce.matches && !document.hidden ? requestAnimationFrame(paso) : 0; };
    var arranca = function () { if (!raf && vis && !reduce.matches && !document.hidden) raf = requestAnimationFrame(paso); };
    new IntersectionObserver(function (e) { vis = e[0].isIntersecting; if (vis) arranca(); }, { rootMargin: "80px" }).observe(cv);
    document.addEventListener("visibilitychange", arranca);
    document.addEventListener("cl:color", function () { lee(); semilla(); dibuja(); });
    addEventListener("resize", function () { size(); semilla(); dibuja(); });
    size(); lee(); semilla(); dibuja();
  };
  /* 12 */ var anioT = 0; M.anio = function (el) {
    el["inner" + "HTML"] = '<div class="anio"><div class="anio-ficha" data-floracion="lluvias"><span class="sw" aria-hidden="true"></span><div><span class="cl-muted" id="anio-m"></span><br><b id="anio-f"></b></div></div><div class="meses" aria-hidden="true">' + Array(12).join(".").split(".").map(function () { return "<span></span>"; }).join("") + "</div></div>";
    var fi = el.querySelector(".anio-ficha"), ms = el.querySelectorAll(".meses span"), MES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], m = 0;
    var pon = function (i) { var f = florMes(i + 1); fi.dataset.floracion = f[0]; document.getElementById("anio-m").textContent = MES[i]; document.getElementById("anio-f").textContent = f[1]; ms.forEach(function (s, j) { s.className = j <= i ? "on" : ""; s.parentNode.dataset.floracion = f[0]; }); };
    clearInterval(anioT); if (reduce.matches) { pon(new Date().getMonth()); return; }
    pon(0); anioT = setInterval(function () { m++; if (m > 11) { clearInterval(anioT); return; } pon(m); }, 750);
  };
  /* 13 */ var skT = 0; M.skel = function (el) {
    var e = by["olea-europaea"];
    el["inner" + "HTML"] = '<div class="skel" aria-busy="true"><div class="b foto"></div><div class="lineas"><div class="b" style="width:70%"></div><div class="b" style="width:90%"></div><div class="b" style="width:55%"></div></div></div>';
    clearTimeout(skT); skT = setTimeout(function () { el["inner" + "HTML"] = '<div class="skel"><img src="' + e.fo.hoja + '" alt="Hoja de ' + esc(e.com) + '"><div class="txt"><b>' + esc(e.com) + '</b><span class="sci cl-muted">' + esc(e.sci) + "</span><span>" + e.n + " \u00e1rboles en el campus</span></div></div>"; }, 1600);
  };
  /* 14 */ M.share = function (el) {
    var url = "https://campuslab.iteso.mx/web/campuslab/especie?id=" + jac.id;
    el["inner" + "HTML"] = '<div class="share"><button class="cl-btn cl-solid" type="button">Compartir ficha</button><code id="sh-url">' + url + '</code></div><div class="cl-toast" role="status" aria-live="polite"></div>';
    var t = el.querySelector(".cl-toast"), tt;
    var avisa = function (m) { t.textContent = m; t.classList.add("on"); clearTimeout(tt); tt = setTimeout(function () { t.classList.remove("on"); }, 1800); };
    el.querySelector("button").onclick = function () {
      var sel = function () { var r = document.createRange(); r.selectNodeContents(document.getElementById("sh-url")); var s = getSelection(); s.removeAllRanges(); s.addRange(r); avisa("Enlace seleccionado: c\u00f3pialo con Ctrl+C"); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { avisa("Enlace copiado"); }, sel); else sel();
    };
  };

  /* C\u00f3digo QR (ISO 18004): modo byte, correcci\u00f3n M, versiones 1 a 10, m\u00e1scara con menor penalizaci\u00f3n. Sin librer\u00edas */
  var qrCodigo = function (texto) {
    var ECC = [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26], BLQ = [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5];
    var bytes = [].slice.call(new TextEncoder().encode(texto));
    var crudos = function (v) { var r = (16 * v + 128) * v + 64; if (v >= 2) { var n = Math.floor(v / 7) + 2; r -= (25 * n - 10) * n - 55; if (v >= 7) r -= 36; } return r; };
    var ver = 1; while (ver <= 10 && 4 + (ver < 10 ? 8 : 16) + 8 * bytes.length > (Math.floor(crudos(ver) / 8) - ECC[ver] * BLQ[ver]) * 8) ver++;
    if (ver > 10) throw new Error("texto demasiado largo para el QR");
    var cap = (Math.floor(crudos(ver) / 8) - ECC[ver] * BLQ[ver]) * 8, bits = [];
    var pon = function (v, n) { for (var i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1); };
    pon(4, 4); pon(bytes.length, ver < 10 ? 8 : 16); bytes.forEach(function (b) { pon(b, 8); });
    pon(0, Math.min(4, cap - bits.length)); pon(0, (8 - bits.length % 8) % 8);
    for (var p = 0xEC; bits.length < cap; p ^= 0xEC ^ 0x11) pon(p, 8);
    var datos = []; for (var i = 0; i < bits.length; i += 8) datos.push(parseInt(bits.slice(i, i + 8).join(""), 2));
    /* Reed-Solomon sobre GF(256), polinomio 0x11D */
    var mul = function (x, y) { var z = 0; for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11D); z ^= ((y >>> i) & 1) * x; } return z; };
    var grado = ECC[ver], div = []; for (i = 0; i < grado - 1; i++) div.push(0); div.push(1);
    for (var r = 1, k = 0; k < grado; k++) { for (var j = 0; j < div.length; j++) { div[j] = mul(div[j], r); if (j + 1 < div.length) div[j] ^= div[j + 1]; } r = mul(r, 2); }
    var resto = function (d) { var res = div.map(function () { return 0; }); d.forEach(function (b) { var f = b ^ res.shift(); res.push(0); div.forEach(function (c, i) { res[i] ^= mul(c, f); }); }); return res; };
    var nb = BLQ[ver], total = Math.floor(crudos(ver) / 8), cortos = nb - total % nb, largoC = Math.floor(total / nb), bloques = [];
    for (i = 0, k = 0; i < nb; i++) { var d = datos.slice(k, k + largoC - grado + (i < cortos ? 0 : 1)); k += d.length; var e = resto(d); if (i < cortos) d.push(0); bloques.push(d.concat(e)); }
    var cw = []; for (i = 0; i < bloques[0].length; i++) bloques.forEach(function (b, j) { if (i !== largoC - grado || j >= cortos) cw.push(b[i]); });
    /* matriz y patrones fijos */
    var n = ver * 4 + 17, M = [], F = [];
    for (i = 0; i < n; i++) { M.push(new Array(n).fill(false)); F.push(new Array(n).fill(false)); }
    var fija = function (x, y, v) { M[y][x] = v; F[y][x] = true; };
    for (i = 0; i < n; i++) { fija(6, i, i % 2 === 0); fija(i, 6, i % 2 === 0); }
    [[3, 3], [n - 4, 3], [3, n - 4]].forEach(function (c) { for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) { var x = c[0] + dx, y = c[1] + dy, m = Math.max(Math.abs(dx), Math.abs(dy)); if (x >= 0 && x < n && y >= 0 && y < n) fija(x, y, m !== 2 && m !== 4); } });
    var al = [];
    if (ver > 1) { var na = Math.floor(ver / 7) + 2, paso = Math.ceil((ver * 4 + 4) / (na * 2 - 2)) * 2; al = [6]; for (var q = n - 7; al.length < na; q -= paso) al.splice(1, 0, q); }
    al.forEach(function (a, ia) { al.forEach(function (b, ib) {
      if ((ia === 0 && ib === 0) || (ia === 0 && ib === al.length - 1) || (ia === al.length - 1 && ib === 0)) return;
      for (var dy = -2; dy <= 2; dy++) for (var dx = -2; dx <= 2; dx++) fija(a + dx, b + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
    }); });
    var formato = function (mask) {
      var dd = mask, rem = dd; for (var i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537); /* nivel M = 00 */
      var b = ((dd << 10) | rem) ^ 0x5412, bit = function (i) { return ((b >>> i) & 1) === 1; };
      for (i = 0; i <= 5; i++) fija(8, i, bit(i)); fija(8, 7, bit(6)); fija(8, 8, bit(7)); fija(7, 8, bit(8));
      for (i = 9; i < 15; i++) fija(14 - i, 8, bit(i));
      for (i = 0; i < 8; i++) fija(n - 1 - i, 8, bit(i)); for (i = 8; i < 15; i++) fija(8, n - 15 + i, bit(i)); fija(8, n - 8, true);
    };
    formato(0);
    if (ver >= 7) { var rv = ver; for (i = 0; i < 12; i++) rv = (rv << 1) ^ ((rv >>> 11) * 0x1F25); var vb = (ver << 12) | rv; for (i = 0; i < 18; i++) { var bv = ((vb >>> i) & 1) === 1, a2 = n - 11 + i % 3, b2 = Math.floor(i / 3); fija(a2, b2, bv); fija(b2, a2, bv); } }
    /* datos en zigzag desde la esquina de abajo a la derecha */
    for (var der = n - 1, t = 0; der >= 1; der -= 2) {
      if (der === 6) der = 5;
      for (var v = 0; v < n; v++) for (j = 0; j < 2; j++) {
        var x = der - j, y = ((der + 1) & 2) === 0 ? n - 1 - v : v;
        if (!F[y][x] && t < cw.length * 8) { M[y][x] = ((cw[t >>> 3] >>> (7 - (t & 7))) & 1) === 1; t++; }
      }
    }
    var MASC = [function (x, y) { return (x + y) % 2 === 0; }, function (x, y) { return y % 2 === 0; }, function (x) { return x % 3 === 0; }, function (x, y) { return (x + y) % 3 === 0; },
      function (x, y) { return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; }, function (x, y) { return x * y % 2 + x * y % 3 === 0; },
      function (x, y) { return (x * y % 2 + x * y % 3) % 2 === 0; }, function (x, y) { return ((x + y) % 2 + x * y % 3) % 2 === 0; }];
    var aplica = function (m) { for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) if (!F[y][x] && MASC[m](x, y)) M[y][x] = !M[y][x]; };
    /* penalizaci\u00f3n (reglas 1, 2 y 4 de la norma): racha de 5+ iguales, bloques 2\u00d72, proporci\u00f3n de oscuros */
    var castigo = function () {
      var s = 0, osc = 0, y, x, c;
      for (y = 0; y < n; y++) for (x = 0, c = 1; x < n; x++) { if (M[y][x]) osc++; if (x && M[y][x] === M[y][x - 1]) { c++; if (c === 5) s += 3; else if (c > 5) s++; } else c = 1; }
      for (x = 0; x < n; x++) for (y = 0, c = 1; y < n; y++) { if (y && M[y][x] === M[y - 1][x]) { c++; if (c === 5) s += 3; else if (c > 5) s++; } else c = 1; }
      for (y = 0; y < n - 1; y++) for (x = 0; x < n - 1; x++) if (M[y][x] === M[y][x + 1] && M[y][x] === M[y + 1][x] && M[y][x] === M[y + 1][x + 1]) s += 3;
      return s + Math.floor(Math.abs(osc * 20 - n * n * 10) / (n * n)) * 10;
    };
    var mejor = 0, menor = Infinity;
    for (var m = 0; m < 8; m++) { aplica(m); formato(m); var c2 = castigo(); if (c2 < menor) { menor = c2; mejor = m; } aplica(m); }
    aplica(mejor); formato(mejor);
    return M;
  };
  /* 15 */ M.qr = function (el) {
    /* especies que florecen en el campus: [id de la ficha, nombre, color de la flor, meses] */
    var ESP = [["tabebuia-rosea", "Rosa morada", "#e46fb2", [2]], ["jacaranda-mimosifolia", "Jacaranda", "#8d6ee0", [3]], ["roseodendron-donnell-smithii", "Primavera", "#f5c02a", [4]],
      ["delonix-regia", "Tabach\u00edn", "#ea4b23", [5, 6]], ["spathodea-campanulata", "Galeana", "#f2862a", [11]], ["pseudobombax-ellipticum", "Clavellina", "#ef6f95", [12, 1]]];
    var TEMP = [["flor", "Floraci\u00f3n"], ["lluvias", "Lluvias"], ["secas", "Secas"]];
    var mes = new Date().getMonth() + 1, S = { e: 0, temp: mes >= 7 && mes <= 10 ? "lluvias" : "flor", t: 0 };
    ESP.forEach(function (x, i) { if (x[3].indexOf(mes) >= 0) S.e = i; });
    el["inner" + "HTML"] = '<div class="qrv"><canvas></canvas><p class="qrv-pista" aria-live="polite"></p>' +
      '<div class="qrv-fila qrv-esp" role="group" aria-label="Especie">' + ESP.map(function (x, i) { return '<button type="button" data-e="' + i + '" aria-pressed="' + (i === S.e) + '" style="--c:' + x[2] + '" title="' + x[1] + '"><span class="cl-sr">' + x[1] + "</span></button>"; }).join("") + "</div>" +
      '<div class="qrv-fila" role="group" aria-label="Temporada">' + TEMP.map(function (x) { return '<button class="cl-btn" type="button" data-t="' + x[0] + '" aria-pressed="' + (x[0] === S.temp) + '">' + x[1] + "</button>"; }).join("") + "</div>" +
      '<div class="qrv-fila"><button class="cl-btn" type="button" data-accion="ver">Ver su QR</button><button class="cl-btn cl-solid" type="button" data-accion="bajar">Descargar QR</button></div></div>';
    var cv = el.querySelector("canvas"), pista = el.querySelector(".qrv-pista"), fondo = document.createElement("canvas");
    var cajas = [], n = 0, url = "", alto = 0, techo = 0, W = 0, H = 0, dpr = 1, vista = null;
    var sem = function (s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return function () { h = Math.imul(h ^ h >>> 15, 2246822507) + 0x6D2B79F5 | 0; return (h >>> 0) / 4294967296; }; };
    var rgb = function (h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; };
    var tono = function (c, k) { return "rgb(" + Math.round(Math.min(255, c[0] * k)) + "," + Math.round(Math.min(255, c[1] * k)) + "," + Math.round(Math.min(255, c[2] * k)) + ")"; };
    var caja = function (x, y, z, w, h, d, c, arbol) { cajas.push({ x: x, y: y, z: z, w: w, h: h, d: d, arbol: arbol, f: [tono(c, 1), tono(c, .84), tono(c, .7)] }); };

    /* la escena: el suelo es el QR (pasto = m\u00f3dulo oscuro, piedra = claro, con 2 de margen) y encima el \u00e1rbol de cubos */
    function construir() {
      var es = ESP[S.e], R = sem(es[0] + S.temp), secas = S.temp === "secas", Q, x, y, z;
      url = "https://campuslab.iteso.mx/w/" + es[0]; Q = qrCodigo(url); n = Q.length + 4; cajas = [];
      var pasto = secas ? ["#55622a", "#4d5a26", "#5e6b2f"] : ["#2f7a3c", "#2a6f36", "#378443"], piedra = ["#efe9dc", "#e7e0d1", "#f4efe6"];
      for (z = 0; z < n; z++) for (x = 0; x < n; x++) {
        var osc = x >= 2 && z >= 2 && x < n - 2 && z < n - 2 && Q[z - 2][x - 2];
        caja(x, 0, z, 1, osc ? .55 : .3, 1, rgb((osc ? pasto : piedra)[Math.floor(R() * 3)]), false);
      }
      var c0 = n / 2 - .5, corteza = rgb("#6b4a32"); alto = Math.round(n * .34);
      for (y = 0; y < alto; y++) caja(c0, .3 + y, c0, 1, 1, 1, corteza, true);
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(function (d, i) { for (var k = 1; k <= 3; k++) caja(c0 + d[0] * k, alto - 3.7 + k + i % 2, c0 + d[1] * k, 1, 1, 1, corteza, true); });
      var rx = n * (secas ? .26 : .31), ry = n * (secas ? .19 : .23), cy = alto + ry * .55, flor = rgb(es[2]), lleno = {};
      var verdes = (secas ? ["#a8802f", "#b8913a", "#8f6a2a", "#c9a24a", "#7a5a2e", "#6f8a3a"] /* en secas, copa m\u00e1s chica y ocre */ : ["#3f9a4c", "#4aa857", "#358a42", "#5bb866"]).map(rgb);
      var en = function (x, y, z) { return lleno[x + "," + y + "," + z]; };
      for (x = Math.floor(c0 - rx); x <= Math.ceil(c0 + rx); x++) for (y = Math.floor(cy - ry); y <= Math.ceil(cy + ry); y++) for (z = Math.floor(c0 - rx); z <= Math.ceil(c0 + rx); z++)
        if (Math.pow((x - c0) / rx, 2) + Math.pow((y - cy) / ry, 2) + Math.pow((z - c0) / rx, 2) + (R() - .5) * .35 < 1) lleno[x + "," + y + "," + z] = 1;
      techo = 0;
      Object.keys(lleno).forEach(function (k) {
        var p = k.split(",").map(Number), x = p[0], y = p[1], z = p[2];
        if (en(x + 1, y, z) && en(x - 1, y, z) && en(x, y + 1, z) && en(x, y - 1, z) && en(x, y, z + 1) && en(x, y, z - 1)) return; /* por dentro no se ve */
        var c = S.temp === "flor" && R() < .82 ? flor : verdes[Math.floor(R() * verdes.length)], k2 = .88 + R() * .24;
        caja(x, y, z, 1, 1, 1, c.map(function (v) { return v * k2; }), true); techo = Math.max(techo, y + 1);
      });
    }

    /* proyecci\u00f3n: de isom\u00e9trica (giro 45\u00b0, inclinaci\u00f3n 32\u00b0) a cenital (0\u00b0, 90\u00b0); el \u00e1rbol se pliega hacia el suelo antes de llegar */
    var suave = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
    function pintar(t) {
      var e = suave(t), th = (45 - 45 * e) * Math.PI / 180, ph = (32 + 58 * e) * Math.PI / 180, s = Math.max(0, 1 - e * 1.3);
      var ct = Math.cos(th), st = Math.sin(th), cp = Math.cos(ph), sp = Math.sin(ph), c0 = n / 2, base = .3;
      var P = function (x, y, z) { x -= c0; z -= c0; var x1 = x * ct - z * st, z1 = x * st + z * ct; return [x1, -y * cp + z1 * sp, z1 * cp + y * sp]; };
      var lista = [];
      cajas.forEach(function (b) {
        var x = b.x, y = b.y, z = b.z, w = b.w, h = b.h, d = b.d;
        if (b.arbol) { if (s < .03) return; var mx = x + w / 2, mz = z + d / 2; w *= s; h *= s; d *= s; x = c0 + (mx - c0) * s - w / 2; z = c0 + (mz - c0) * s - d / 2; y = base + (y - base) * s; }
        lista.push([P(x + w / 2, y + h / 2, z + d / 2)[2], x, y, z, w, h, d, b.f]);
      });
      lista.sort(function (a, b) { return a[0] - b[0]; });
      /* encuadre: la losa y la copa caben con margen; al final el QR llena el lienzo */
      var pts = [], r = n * .3 * s, top = base + (techo - base) * s;
      [0, n].forEach(function (x) { [0, n].forEach(function (z) { pts.push(P(x, -1.4, z), P(x, .55, z)); }); });
      if (s > .03) [[c0 - r, c0 - r], [c0 + r, c0 - r], [c0 - r, c0 + r], [c0 + r, c0 + r]].forEach(function (q) { pts.push(P(q[0], top, q[1])); });
      var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
      var k = Math.min((W - 16) / (x1 - x0), (H - 16) / (y1 - y0)), ox = W / 2 - (x0 + x1) / 2 * k, oy = H / 2 - (y0 + y1) / 2 * k;
      vista = { P: P, k: k, ox: ox, oy: oy };
      fondo.width = cv.width; fondo.height = cv.height;
      var g = fondo.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.lineJoin = "round"; g.lineWidth = .8;
      var cara = function (q, c) { g.beginPath(); q.forEach(function (p, i) { var X = ox + p[0] * k, Y = oy + p[1] * k; if (i) g.lineTo(X, Y); else g.moveTo(X, Y); }); g.closePath(); g.fillStyle = g.strokeStyle = c; g.fill(); g.stroke(); };
      /* losa de base, debajo de todo */
      cara([P(n, -1.4, 0), P(n, .3, 0), P(n, .3, n), P(n, -1.4, n)], "#cdbfa8"); cara([P(0, -1.4, n), P(0, .3, n), P(n, .3, n), P(n, -1.4, n)], "#b6a890");
      lista.forEach(function (b) {
        var x = b[1], y = b[2], z = b[3], w = b[4], h = b[5], d = b[6], f = b[7];
        if (st * cp > .02) cara([P(x + w, y, z), P(x + w, y + h, z), P(x + w, y + h, z + d), P(x + w, y, z + d)], f[1]);
        if (ct * cp > .02) cara([P(x, y, z + d), P(x, y + h, z + d), P(x + w, y + h, z + d), P(x + w, y, z + d)], f[2]);
        cara([P(x, y + h, z), P(x + w, y + h, z), P(x + w, y + h, z + d), P(x, y + h, z + d)], f[0]);
      });
      componer();
    }

    /* p\u00e9talos (floraci\u00f3n) u hojas secas que caen de la copa, encima de la escena ya pintada */
    var caen = [], visible = false, raf = 0;
    function componer() {
      var g = cv.getContext("2d"); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cv.width, cv.height); g.drawImage(fondo, 0, 0);
      if (S.t || !caen.length) return;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      caen.forEach(function (p) {
        var q = vista.P(p.x, p.y, p.z), l = vista.k * .55;
        g.save(); g.translate(vista.ox + q[0] * vista.k, vista.oy + q[1] * vista.k); g.rotate(p.r); g.fillStyle = p.c; g.fillRect(-l / 2, -l / 2, l, l * .7); g.restore();
      });
    }
    function sembrar() {
      var R = sem("caen" + S.e), es = ESP[S.e], c0 = n / 2; caen = [];
      if (S.temp === "lluvias" || reduce.matches) return;
      for (var i = 0; i < 16; i++) caen.push({ x: c0 + (R() - .5) * n * .5, y: R() * techo, z: c0 + (R() - .5) * n * .5, v: .025 + R() * .03, r: R() * 6, vr: (R() - .5) * .08, c: S.temp === "flor" ? es[2] : ["#a8802f", "#c9a24a", "#8f6a2a"][i % 3] });
    }
    function animar() {
      raf = 0; if (!visible || S.t || !caen.length) return;
      caen.forEach(function (p) { p.y -= p.v; p.r += p.vr; p.x += Math.sin(p.y * .7) * .02; if (p.y < .6) p.y = techo * (.55 + Math.random() * .4); });
      componer(); raf = requestAnimationFrame(animar);
    }
    var sigue = function () { if (!raf && visible && !S.t && caen.length) raf = requestAnimationFrame(animar); };

    function medir() { W = cv.clientWidth || 320; H = Math.round(W * 1.02); dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + "px"; }
    function rotulo() {
      var es = ESP[S.e];
      pista.textContent = S.t ? "Escan\u00e9alo con la c\u00e1mara del celular \u00b7 toca para volver al \u00e1rbol" : "Toca el \u00e1rbol para ver el QR de su ficha";
      el.querySelector('[data-accion="ver"]').textContent = S.t ? "Ver el \u00e1rbol" : "Ver su QR";
      cv.setAttribute("role", "img");
      cv.setAttribute("aria-label", S.t ? "C\u00f3digo QR que lleva a la ficha de " + es[1] + " (" + url.replace("https://", "") + ")" : "\u00c1rbol de cubos de " + es[1] + " parado sobre el c\u00f3digo QR de su ficha");
    }
    var girando = false;
    function voltear() {
      if (girando) return; girando = true;
      var desde = S.t, hacia = S.t ? 0 : 1, t0 = performance.now(), dur = reduce.matches ? 1 : 1100;
      var paso = function (ahora) { var p = Math.min((ahora - t0) / dur, 1); S.t = desde + (hacia - desde) * p; pintar(S.t); if (p < 1) requestAnimationFrame(paso); else { S.t = hacia; girando = false; rotulo(); sigue(); } };
      requestAnimationFrame(paso);
    }
    function rehacer() { construir(); sembrar(); pintar(S.t); rotulo(); sigue(); }
    /* QR plano para imprimir: m\u00f3dulos de 16 px, margen de 4 m\u00f3dulos y el nombre debajo */
    function descargar() {
      var es = ESP[S.e], Q = qrCodigo(url), m = 16, q = 4, lado = (Q.length + 2 * q) * m, c = document.createElement("canvas"), g = c.getContext("2d"), fam = getComputedStyle(el).fontFamily;
      c.width = lado; c.height = lado + 70; g.fillStyle = "#ffffff"; g.fillRect(0, 0, c.width, c.height); g.fillStyle = "#1b2a1f";
      Q.forEach(function (fila, y) { fila.forEach(function (v, x) { if (v) g.fillRect((x + q) * m, (y + q) * m, m, m); }); });
      g.textAlign = "center"; g.font = "600 30px " + fam; g.fillText(es[1], lado / 2, lado + 18);
      g.font = "20px " + fam; g.fillStyle = "#4a5d69"; g.fillText(url.replace("https://", ""), lado / 2, lado + 50);
      c.toBlob(function (b) { var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "qr-" + es[0] + ".png"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000); });
    }

    cv.addEventListener("click", voltear);
    el.querySelector(".qrv").addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      if (b.dataset.e) { S.e = +b.dataset.e; el.querySelectorAll("[data-e]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); rehacer(); }
      if (b.dataset.t) { S.temp = b.dataset.t; el.querySelectorAll("[data-t]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); rehacer(); }
      if (b.dataset.accion === "ver") voltear();
      if (b.dataset.accion === "bajar") descargar();
    });
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; sigue(); }).observe(el);
    var rt; if (window.ResizeObserver) new ResizeObserver(function () { clearTimeout(rt); rt = setTimeout(function () { var w = cv.clientWidth; if (w && Math.abs(w - W) > 1) { medir(); pintar(S.t); } }, 100); }).observe(cv);
    medir(); rehacer();
  };

  /* las que se animan arrancan al verse (una vez); las dem\u00e1s se montan de inmediato */
  var montar = function (k) { M[k](st(k)); };
  var io = new IntersectionObserver(function (en) { en.forEach(function (x) { if (x.isIntersecting) { io.unobserve(x.target); montar(x.target.dataset.demo); } }); }, { threshold: .35 });
  Object.keys(M).forEach(function (k) { if (REPLAY[k]) { st(k)["inner" + "HTML"] = ""; io.observe(st(k)); } else montar(k); });
  document.addEventListener("click", function (ev) { var b = ev.target.closest("[data-replay]"); if (b) montar(b.dataset.replay); });
};


(function () {
  var url = (typeof configuration !== "undefined" && configuration.datos) || "/documents/d/campuslab/prototipo-componentes";
  try { var modo = localStorage.getItem("cl-modo"); if (modo) document.querySelector(".cl").dataset.modo = modo; } catch (e) {}
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
    .then(function (txt) { barra.remove(); document.getElementById("datos").textContent = txt; window.CL_PROTO(); })
    .catch(function (e) { barra.remove(); var p = document.createElement("p"); p.style.padding = "16px"; p.textContent = "No se pudieron cargar los datos del prototipo (" + e.message + ")."; document.querySelector(".cl").prepend(p); });
})();
