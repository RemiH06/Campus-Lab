/* Itesodex: todas las especies de la lista oficial y cuáles faltan por fotografiar. Lee itesodex-naturalista.csv, que
   se edita en Excel (guía en README.md): Grupo, Nombre común, Nombre científico, Estado (Fotografiada, Solo en
   iNaturalist o Se busca; sin importar mayúsculas ni acentos), y opcionales Fotos en Campus Lab, Observaciones en
   iNaturalist, Enlace a iNaturalist y Dónde buscar. La foto de referencia se pide a iNaturalist solo cuando alguien la
   abre. El CSV lo lee el Marco (window.clCSV, que también quita acentos a los encabezados); si este fragmento carga
   antes, lo espera. */
(function () {
  var sec = fragmentElement.querySelector(".cl-dex");
  if (!sec) return;
  var url = (sec.dataset.csv || "").trim() || "/documents/d/campuslab/itesodex-naturalista";
  var lista = sec.querySelector(".cl-dex-lista"), mas = sec.querySelector(".cl-dex-mas"), resumen = sec.querySelector(".cl-dex-resumen");
  var controles = sec.querySelector(".cl-dex-controles"), busca = sec.querySelector("input[type=search]"), aviso = sec.querySelector(".cl-aviso-editor");
  var POR_PAGINA = 30;
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var norm = function (s) { return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };
  var ESTADO = { con_foto: "Ya fotografiada", en_inaturalist: "Solo en iNaturalist", se_busca: "Se busca" };
  /* lo que alguien puede escribir en la columna Estado → el estado interno */
  var ALIAS = { fotografiada: "con_foto", "ya fotografiada": "con_foto", "con foto": "con_foto", con_foto: "con_foto",
    "solo en inaturalist": "en_inaturalist", "en inaturalist": "en_inaturalist", en_inaturalist: "en_inaturalist", "se busca": "se_busca", se_busca: "se_busca" };
  /* siluetas por grupo, trazadas a mano en 48×48 */
  var SIL = {
    "Árboles": '<path d="M24 6c-7 0-12 5-12 11-3 1.5-5 4.5-5 8 0 5 4 9 9 9h5v8h6v-8h5c5 0 9-4 9-9 0-3.5-2-6.5-5-8 0-6-5-11-12-11z"/>',
    "Aves": '<path d="M33 10a6 6 0 0 0-6 6v3c-6 0-13 3-17 9l9-1-6 7c6 1 12-1 15-5l5 9h4l-4-11c4-2 6-6 6-11v-1l5-1-5-3a6 6 0 0 0-6-1zm0 4.5a1.6 1.6 0 1 1 0 3.2 1.6 1.6 0 0 1 0-3.2z"/>',
    "Orquídeas": '<path d="M24 8c-3 0-5 4-5 8 0 1 0 2 .4 3-3-2-8-3-10-.5-2 2.5 1 7 5 8.5-3 2-4 6-2 8 2 2 6 0 9-3l1 13h3l1-13c3 3 7 5 9 3 2-2 1-6-2-8 4-1.5 7-6 5-8.5-2-2.5-7-1.5-10 .5.3-1 .4-2 .4-3 0-4-2-8-5-8zm0 16a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/>',
    "Suculentas": '<path d="M24 6c-3 4-4 9-3 13-3-3-7-5-12-5 1 5 4 9 8 11-4 0-8 2-11 5 4 2 9 2 13 0-1 3 0 7 2 10h6c2-3 3-7 2-10 4 2 9 2 13 0-3-3-7-5-11-5 4-2 7-6 8-11-5 0-9 2-12 5 1-4 0-9-3-13z"/>',
    "Flores de La Primavera": '<path d="M24 5a5 5 0 0 0-5 5c0 1.6.7 3 1.8 4-1.4-.9-3-1.3-4.7-.9a5 5 0 0 0-1 9.5c-1.7.3-3.2 1.3-4 2.9a5 5 0 0 0 7.5 6c-.3 1.6 0 3.4 1.1 4.7a5 5 0 0 0 8.6 0c1.1-1.3 1.4-3.1 1.1-4.7a5 5 0 0 0 7.5-6c-.8-1.6-2.3-2.6-4-2.9a5 5 0 0 0-1-9.5c-1.7-.4-3.3 0-4.7.9 1.1-1 1.8-2.4 1.8-4a5 5 0 0 0-5-5zm0 15a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9z"/>'
  };
  var SILN = {}; Object.keys(SIL).forEach(function (k) { SILN[norm(k)] = SIL[k]; }); /* "arboles" o "Árboles": la misma silueta */
  var inicial = sec.dataset.estado || "se_busca"; /* "todas" en la Configuración = sin filtro de estado */
  var F = { estado: inicial === "todas" ? "" : inicial, grupo: "", q: "" }, E = [], vistos = POR_PAGINA;

  function tarjeta(e) {
    var sil = '<svg viewBox="0 0 48 48" aria-hidden="true">' + (SILN[norm(e.grupo)] || SIL["Árboles"]) + "</svg>";
    var obs = +e.observaciones_en_inaturalist || 0, fotos = +e.fotos_en_campus_lab || 0;
    /* los conteos son opcionales: quien cambia el estado a mano no tiene que llenarlos */
    var det = e.estado === "con_foto" ? (fotos ? fotos + (fotos === 1 ? " foto" : " fotos") + " en Campus Lab" : "Ya tiene foto en Campus Lab")
      : e.estado === "en_inaturalist" ? (obs ? obs + (obs === 1 ? " observación" : " observaciones") + " en iNaturalist" : "Ya la observaron en el ITESO")
      : "Nadie la ha registrado en el ITESO";
    return '<li class="cl-dex-esp" data-estado="' + esc(e.estado) + '">' +
      '<div class="cl-dex-sil">' + sil + "</div>" +
      '<div class="cl-dex-datos"><span class="cl-dex-num">#' + String(e.n).padStart(3, "0") + " · " + esc(e.grupo) + "</span>" +
      "<b>" + esc(e.nombre_comun || e.nombre_cientifico) + '</b><i class="cl-sci">' + esc(e.nombre_cientifico) + "</i>" +
      '<span class="cl-dex-estado">' + ESTADO[e.estado] + "</span><span class=\"cl-dex-det\">" + det + "</span>" +
      (e.donde_buscar && e.estado !== "con_foto" ? '<span class="cl-dex-donde"><b>Dónde buscarla:</b> ' + esc(e.donde_buscar.replace(/ \((\d+)\)/g, function (m, k) { return " (" + k + (k === "1" ? " árbol)" : " árboles)"); })) + "</span>" : "") +
      (e.taxon ? '<span class="cl-dex-acciones"><button class="cl-dex-ref" type="button" data-taxon="' + esc(e.taxon) + '">Ver cómo es</button>' +
        '<a href="' + esc(e.enlace_a_inaturalist) + '" target="_blank" rel="noopener">Ficha en iNaturalist<span class="cl-sr"> (se abre en otra pestaña)</span></a></span>' : "") +
      "</div></li>";
  }
  function filtradas() {
    var q = norm(F.q);
    return E.filter(function (e) { return (!F.estado || e.estado === F.estado) && (!F.grupo || e.grupo === F.grupo) && (!q || e.clave.indexOf(q) >= 0); });
  }
  function pintar() {
    var L = filtradas();
    lista.innerHTML = L.slice(0, vistos).map(tarjeta).join("") || '<li class="cl-dex-vacio">Ninguna especie con esos filtros.</li>';
    var resto = L.length - vistos;
    mas.innerHTML = resto > 0 ? '<button class="cl-btn" type="button">Mostrar ' + Math.min(resto, POR_PAGINA) + " más (" + resto + " por ver)</button>" : "";
    controles.querySelectorAll("[data-filtro] button").forEach(function (b) { b.setAttribute("aria-pressed", String(F[b.parentNode.dataset.filtro] === b.dataset.v)); });
  }
  function resumir() {
    var por = {}, tot = { con_foto: 0, en_inaturalist: 0, se_busca: 0 };
    E.forEach(function (e) { var g = por[e.grupo] = por[e.grupo] || { con_foto: 0, en_inaturalist: 0, se_busca: 0, n: 0 }; g[e.estado]++; g.n++; tot[e.estado]++; });
    var barra = function (nombre, g, n) {
      var p = function (k) { return (100 * g[k] / n).toFixed(2) + "%"; };
      return '<li><span class="cl-dex-gnom">' + esc(nombre) + '</span><span class="cl-dex-gnum">' + g.con_foto + " de " + n + '</span><span class="cl-dex-barra" aria-hidden="true">' +
        '<i data-k="con_foto" style="width:' + p("con_foto") + '"></i><i data-k="en_inaturalist" style="width:' + p("en_inaturalist") + '"></i><i data-k="se_busca" style="width:' + p("se_busca") + '"></i></span></li>';
    };
    resumen.innerHTML = '<p class="cl-dex-total"><b>' + E.length + "</b> especies en la lista oficial: <b>" + tot.con_foto + "</b> ya fotografiadas, <b>" + tot.en_inaturalist + "</b> solo en iNaturalist y <b>" + tot.se_busca + "</b> que se buscan.</p>" +
      '<ul class="cl-dex-grupos">' + Object.keys(por).map(function (k) { return barra(k, por[k], por[k].n); }).join("") + "</ul>" +
      '<p class="cl-dex-leyenda" aria-hidden="true"><span data-k="con_foto">Ya fotografiadas</span><span data-k="en_inaturalist">Solo en iNaturalist</span><span data-k="se_busca">Se buscan</span></p>';
    var fila = controles.querySelector('[data-filtro="grupo"]');
    fila.innerHTML = '<button class="cl-btn" type="button" data-v="">Todos los grupos</button>' + Object.keys(por).map(function (k) { return '<button class="cl-btn" type="button" data-v="' + esc(k) + '">' + esc(k) + "</button>"; }).join("");
  }
  /* foto de referencia: la de iNaturalist para ese taxón, con su crédito */
  function referencia(b) {
    var caja = b.closest(".cl-dex-esp").querySelector(".cl-dex-sil");
    b.disabled = true; b.textContent = "Buscando foto…";
    fetch("https://api.inaturalist.org/v1/taxa/" + encodeURIComponent(b.dataset.taxon)).then(function (r) { return r.json(); }).then(function (j) {
      var t = j.results && j.results[0], f = t && t.default_photo;
      if (!f) { b.textContent = "Sin foto en iNaturalist"; return; }
      caja.innerHTML = '<img src="' + esc(f.medium_url || f.square_url) + '" alt="Foto de referencia de ' + esc(t.preferred_common_name || t.name) + '" loading="lazy">';
      caja.classList.add("cl-dex-con-ref");
      b.outerHTML = '<span class="cl-dex-credito">Foto: ' + esc(f.attribution) + "</span>";
    }).catch(function () { b.disabled = false; b.textContent = "Reintentar"; });
  }

  controles.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-filtro] button"); if (!b) return;
    F[b.parentNode.dataset.filtro] = b.dataset.v; vistos = POR_PAGINA; pintar();
  });
  var tb; busca.addEventListener("input", function () { clearTimeout(tb); tb = setTimeout(function () { F.q = busca.value; vistos = POR_PAGINA; pintar(); }, 120); });
  mas.addEventListener("click", function (ev) {
    if (!ev.target.closest("button")) return;
    var primera = vistos; vistos += POR_PAGINA; pintar();
    var nueva = lista.children[primera]; if (nueva) { nueva.setAttribute("tabindex", "-1"); nueva.focus({ preventScroll: true }); }
  });
  lista.addEventListener("click", function (ev) { var b = ev.target.closest(".cl-dex-ref"); if (b) referencia(b); });

  function cargar(filas) {
    var malas = [];
    E = filas.filter(function (r) {
      r.estado = ALIAS[norm(r.estado).trim()];
      var ok = r.nombre_cientifico && r.estado; if (!ok) malas.push(r._fila); return ok;
    });
    var grafia = {}; /* "arboles" y "Árboles" son el mismo grupo: se muestra como se escribió la primera vez */
    E.forEach(function (e, i) {
      var g = norm(e.grupo).trim(); e.grupo = grafia[g] = grafia[g] || (e.grupo || "Sin grupo").trim();
      e.n = i + 1; e.clave = norm(e.nombre_comun + " " + e.nombre_cientifico);
      var m = /inaturalist\.org\/taxa\/(\d+)/.exec(e.enlace_a_inaturalist || ""); e.taxon = m ? m[1] : ""; /* solo ligas a una especie de iNaturalist */
    });
    lista.removeAttribute("aria-busy"); controles.hidden = false;
    resumir(); pintar();
    if (malas.length) { aviso.hidden = false; var una = malas.length === 1; aviso.textContent = "Aviso para quien edita: en el CSV del Itesodex, " + (una ? "la fila " : "las filas ") + malas.slice(0, 20).join(", ") + (malas.length > 20 ? "…" : "") + (una ? " no tiene" : " no tienen") + " nombre científico o un estado que no es Fotografiada, Solo en iNaturalist ni Se busca. No se " + (una ? "muestra." : "muestran."); }
  }
  function error(e) {
    lista.innerHTML = '<li class="cl-dex-vacio">No se pudo cargar el Itesodex.</li>'; lista.removeAttribute("aria-busy");
    aviso.hidden = false; aviso.textContent = "Aviso para quien edita: " + e.message + ". Revisa la URL del CSV en la Configuración del fragmento.";
  }
  /* se carga cuando la sección está por verse: el CSV pesa unos 60 KB */
  var empezar = function () { window.clCSV(url).then(cargar, error); };
  new IntersectionObserver(function (en, io) {
    if (!en[0].isIntersecting) return; io.disconnect();
    if (window.clCSV) empezar(); else document.addEventListener("cl-base", empezar, { once: true });
  }, { rootMargin: "400px" }).observe(sec);
})();
