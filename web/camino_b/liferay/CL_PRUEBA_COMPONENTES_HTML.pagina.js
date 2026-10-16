/* Generado por web/camino_b/preparar_para_liferay.py; no editar a mano.
   Pegar en la página: Diseño > Personalización > JavaScript. Lee /documents/d/campuslab/prototipo-componentes. */
(function () {
  function montar() {
    if (document.querySelector('[data-cl-pagina]')) return;
    var host = document.getElementById('main-content') || document.body;
    var w = document.createElement('div'); w.setAttribute('data-cl-pagina', '');
    w['inner' + 'HTML'] = "<div class=\"cl\" id=\"cl\">\n  <div class=\"shell\">\n    <header class=\"top\">\n      <div><h1>Componentes y efectos<\/h1><p>Piezas sueltas para escoger. Todas usan la paleta de la floraci&#xf3;n y funcionan en claro y oscuro. Pide las que te gusten por su n&#xfa;mero.<\/p><\/div>\n      <div class=\"tools\">\n        <label class=\"flor-pick\"><span class=\"cl-sr\">Floraci&#xf3;n<\/span><select id=\"flor\" aria-label=\"Paleta de floraci&#xf3;n\"><\/select><\/label>\n        <button class=\"cl-btn\" type=\"button\" id=\"modo\"><\/button>\n      <\/div>\n    <\/header>\n    <div id=\"grupos\"><\/div>\n  <\/div>\n<\/div>\n\n<script type=\"application/json\" id=\"datos\"><\/script>";
    host.insertBefore(w, host.firstChild);

window.CL_PROTO = function () {
  "use strict";
  var root = document.getElementById("cl"), D;
  try { D = JSON.parse(document.getElementById("datos").textContent); } catch (e) { document.getElementById("grupos")["inner" + "HTML"] = '<p class="cl-card" style="padding:16px">Esta es la plantilla sin datos. Abre Componentes_campuslab.html en reestructura/salida/sitio_campuslab/.</p>'; return; }
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
    root.dataset.modo = s || "claro"; /* claro por defecto */
    var pinta = function () { var o = actual() === "oscuro"; b.textContent = o ? "Modo claro" : "Modo oscuro"; b.setAttribute("aria-label", o ? "Cambiar a modo claro" : "Cambiar a modo oscuro"); };
    b.onclick = function () { var n = actual() === "oscuro" ? "claro" : "oscuro"; root.dataset.modo = n; store.set("cl-modo", n); pinta(); document.dispatchEvent(new Event("cl:color")); };
    pinta();
    var sel = document.getElementById("flor"), auto = florMes(new Date().getMonth() + 1);
    sel["inner" + "HTML"] = '<option value="auto">Floraci\u00f3n del mes (' + auto[1] + ")</option>" + FLOR.map(function (f) { return '<option value="' + f[0] + '">' + f[1] + "</option>"; }).join("");
    var ap = function (v) { root.dataset.floracion = v === "auto" ? auto[0] : v; document.dispatchEvent(new Event("cl:color")); };
    sel.value = store.get("cl-flor") || "auto"; ap(sel.value);
    sel.onchange = function () { store.set("cl-flor", sel.value); ap(sel.value); };
  })();

  /* \u2500\u2500 cat\u00e1logo de muestras \u2500\u2500 */
  var G = [
    ["Entrada y scroll", "aparecen cuando llegas a ellas", [
      [1, "Revelado de foto", "La foto se descubre de abajo hacia arriba con un acercamiento suave.", "Foto principal de la ficha, portada de cada jard\u00edn.", "Solo CSS", "rev"],
      [2, "Cifras que cuentan", "Los n\u00fameros suben desde cero al verse.", "Portada del Itesodex, p\u00e1gina de Campus Lab.", "CSS + JS m\u00ednimo", "cifras"],
      [3, "Anillos que crecen", "Los anillos del tronco se dibujan uno por uno, del centro hacia afuera.", "Ficha de especie, al abrirla.", "Solo CSS (SVG)", "grow"]
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
    var circ = function (r) { return "M" + (100 + r) + ",100 A" + r + "," + r + " 0 1,1 " + (100 - r) + ",100 A" + r + "," + r + " 0 1,1 " + (100 + r) + ",100"; };
    el["inner" + "HTML"] = '<div class="grow"><svg viewBox="0 0 200 200" role="img" aria-label="Anillos de ' + esc(e.com) + ": " + Object.keys(e.fo).length + ' de 5 partes con foto">' +
      orden.map(function (p, i) { var has = !!e.fo[p]; return '<path class="' + (has ? "has" : "no") + '" pathLength="1" d="' + circ(28 + i * 15) + '" style="--mix:' + mix[p] + ";--d:" + i * 90 + 'ms"/>'; }).join("") + '<text x="100" y="100">' + Object.keys(e.fo).length + "/5</text></svg></div>";
    var g = el.firstChild; requestAnimationFrame(function () { g.classList.add("go"); });
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
    var io = new IntersectionObserver(function (en) { en.forEach(function (x) { if (x.intersectionRatio > .6) { var i = [].indexOf.call(figs, x.target); dots.forEach(function (d, j) { d.setAttribute("aria-current", String(i === j)); }); } }); }, { root: tr, threshold: [.6] });
    figs.forEach(function (f) { io.observe(f); });
  };
  /* 6 */ M.flip = function (el) {
    var e = by["delonix-regia"];
    el["inner" + "HTML"] = '<button class="flip" type="button" aria-pressed="false" aria-label="Voltear la tarjeta de ' + esc(e.com) + '"><span class="flip-in"><span class="cara frente"><img src="' + e.fo.flor + '" alt=""><span>' + esc(e.com) + '</span></span><span class="cara dorso"><b>' + esc(e.com) + '</b><span class="sci cl-muted">' + esc(e.sci) + "</span><span>" + e.n + " \u00e1rboles en el campus</span><span>" + esc(e.fam) + '</span><span class="dots">' + PARTES.map(function (p) { return '<i class="' + (e.fo[p] ? "on" : "") + '" title="' + NOM[p] + '"></i>'; }).join("") + "</span><span class=\"muted\">" + Object.keys(e.fo).length + " de 5 partes</span></span></span></button>";
    var b = el.firstChild; b.onclick = function () { b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true")); };
  };
  /* 7 */ M.ac = function (el) {
    el["inner" + "HTML"] = '<div class="ac"><label class="cl-sr" for="ac-q">Buscar especie</label><input class="cl-field" id="ac-q" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="ac-l" autocomplete="off" placeholder="Prueba con \u00abtabach\u00bb o \u00abceiba\u00bb"><ul id="ac-l" role="listbox" hidden></ul></div>';
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

  /* las que se animan arrancan al verse (una vez); las dem\u00e1s se montan de inmediato */
  var montar = function (k) { M[k](st(k)); };
  var io = new IntersectionObserver(function (en) { en.forEach(function (x) { if (x.isIntersecting) { io.unobserve(x.target); montar(x.target.dataset.demo); } }); }, { threshold: .35 });
  Object.keys(M).forEach(function (k) { if (REPLAY[k]) { st(k)["inner" + "HTML"] = ""; io.observe(st(k)); } else montar(k); });
  document.addEventListener("click", function (ev) { var b = ev.target.closest("[data-replay]"); if (b) montar(b.dataset.replay); });
};


(function () {
  var url = "/documents/d/campuslab/prototipo-componentes";
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

  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', montar); else montar();
})();
