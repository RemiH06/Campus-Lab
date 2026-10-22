/* Galería del concurso por edición. Lee un CSV editado en Excel: edicion, categoria, resultado, titulo, autor, especie,
   nombre_cientifico, foto, album (guía en README.md). "foto" es el nombre del archivo en Documentos y Medios (con o sin
   terminación) o una URL completa; vacía = la foto aún no se sube y se muestra la ficha sin foto. Se pide la versión
   de Adaptive Media de la Configuración (1000 px) y, si no existe, el archivo tal cual. "album" basta en una fila de
   la edición; una fila con solo edición y álbum sirve para ediciones sin resultados capturados.
   El CSV lo lee el Marco (window.clCSV); si este fragmento carga antes, lo espera. */
(function () {
  var sec = fragmentElement.querySelector(".cl-gal");
  if (!sec) return;
  var url = (sec.dataset.csv || "").trim() || "/documents/d/campuslab/galeria-naturalista";
  var base = sec.dataset.fotos || "/documents/d/campuslab/", ext = sec.dataset.ext || "", variante = sec.dataset.variante || "";
  var tabs = sec.querySelector(".cl-gal-pestanas"), cuerpo = sec.querySelector(".cl-gal-cuerpo"), aviso = sec.querySelector(".cl-aviso-editor");
  var visor = sec.querySelector(".cl-gal-visor"), vImg = visor.querySelector("img"), vPie = visor.querySelector("figcaption");
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  /* la URL corta de Documentos y Medios no lleva terminación: "mirlo.jpg" y "mirlo" son el mismo archivo */
  var original = function (r) { return /^https?:\/\//.test(r.foto) ? r.foto : base + encodeURIComponent(r.foto.replace(/\.(jpe?g|png|webp)$/i, "")) + ext; };
  var foto = function (r) { return /^https?:\/\//.test(r.foto) ? r.foto : original(r) + variante; };
  /* si Adaptive Media no tiene la versión (archivo recién subido o que no es imagen), el archivo tal cual */
  sec.addEventListener("error", function (ev) { var i = ev.target; if (i.tagName === "IMG" && i.dataset.original && !i.dataset.reintento) { i.dataset.reintento = "1"; i.src = i.dataset.original; } }, true);
  var GRUPOS = [["Premiadas", /lugar/i], ["Menciones honoríficas", /menci/i], ["Finalistas", /finalista/i], ["Otras seleccionadas", /./]];
  var ED = {}, actual = null, conFoto = [], iv = 0;

  function especie(r) { return esc(r.especie) + (r.nombre_cientifico ? ' (<i class="cl-sci">' + esc(r.nombre_cientifico) + "</i>)" : ""); }
  function pieza(r, grande) {
    var txt = '<figcaption><span class="cl-gal-res">' + esc(r.resultado) + (r.categoria ? " · " + esc(r.categoria) : "") + "</span><b>" + esc(r.titulo) + "</b><span>" + esc(r.autor) + "</span><span>" + especie(r) + "</span></figcaption>";
    if (!r.foto) return '<li class="cl-gal-pieza cl-gal-sinfoto"><figure><div class="cl-gal-marco"><span>Foto por subir</span></div>' + txt + "</figure></li>";
    var i = conFoto.push(r) - 1;
    return '<li class="cl-gal-pieza' + (grande ? " cl-gal-grande" : "") + '"><figure><button class="cl-gal-marco" type="button" data-i="' + i + '" aria-label="Ampliar ' + esc(r.titulo) + ", de " + esc(r.autor) + '">' +
      '<img src="' + esc(foto(r)) + '" data-original="' + esc(original(r)) + '" alt="' + esc(r.especie) + " en la foto " + esc(r.titulo) + '" loading="lazy" decoding="async"></button>' + txt + "</figure></li>";
  }
  function mostrar(k) {
    actual = k; conFoto = [];
    tabs.querySelectorAll("button").forEach(function (b) { var on = b.dataset.ed === k; b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1; });
    var e = ED[k], usadas = {}, html = "";
    GRUPOS.forEach(function (g, gi) {
      var rs = e.filas.filter(function (r, i) { if (usadas[i] || !g[1].test(r.resultado)) return false; usadas[i] = 1; return true; });
      if (rs.length) html += '<h3 class="cl-gal-grupo">' + g[0] + '</h3><ul class="cl-gal-rejilla' + (gi === 0 ? " cl-gal-premiadas" : "") + '">' + rs.map(function (r) { return pieza(r, gi === 0); }).join("") + "</ul>";
    });
    if (!e.filas.length) html = '<p class="cl-gal-vacio">Los resultados de ' + esc(k) + " todavía no están en esta página.</p>";
    if (e.album) html += '<p class="cl-gal-album"><a class="cl-btn" href="' + esc(e.album) + '" target="_blank" rel="noopener">Ver todas las fotos de ' + esc(k) + ' en Facebook<span class="cl-sr"> (se abre en otra pestaña)</span></a></p>';
    cuerpo.innerHTML = html;
  }
  function ver(i) {
    iv = (i + conFoto.length) % conFoto.length; var r = conFoto[iv];
    vImg.dataset.original = original(r); delete vImg.dataset.reintento; vImg.src = foto(r); vImg.alt = r.especie + " en la foto " + r.titulo + ", de " + r.autor;
    vPie.innerHTML = "<b>" + esc(r.titulo) + "</b> · " + esc(r.autor) + "<br>" + especie(r) + ' <span class="cl-gal-res">' + esc(r.resultado) + "</span>";
    if (!visor.open) visor.showModal();
  }
  cuerpo.addEventListener("click", function (ev) { var b = ev.target.closest(".cl-gal-marco[data-i]"); if (b) ver(+b.dataset.i); });
  visor.addEventListener("click", function (ev) {
    var b = ev.target.closest("button");
    if (ev.target === visor || (b && b.hasAttribute("data-cerrar"))) visor.close();
    else if (b && b.dataset.ir) ver(iv + +b.dataset.ir);
  });
  visor.addEventListener("keydown", function (ev) { if (ev.key === "ArrowRight") ver(iv + 1); if (ev.key === "ArrowLeft") ver(iv - 1); });
  tabs.addEventListener("click", function (ev) { var b = ev.target.closest("button"); if (b) mostrar(b.dataset.ed); });
  tabs.addEventListener("keydown", function (ev) {
    if (ev.key !== "ArrowRight" && ev.key !== "ArrowLeft") return;
    var bs = [].slice.call(tabs.querySelectorAll("button")), i = bs.findIndex(function (b) { return b.dataset.ed === actual; });
    var n = bs[(i + (ev.key === "ArrowRight" ? 1 : -1) + bs.length) % bs.length]; mostrar(n.dataset.ed); n.focus();
  });

  function cargar(filas) {
    var malas = [];
    filas.forEach(function (r) {
      if (!r.edicion) { malas.push(r._fila); return; }
      var e = ED[r.edicion] = ED[r.edicion] || { filas: [], album: "" };
      if (r.album && !e.album) e.album = r.album;
      if (r.titulo || r.autor) e.filas.push(r);
    });
    var ks = Object.keys(ED).sort().reverse(); /* la más reciente primero */
    if (!ks.length) { cuerpo.innerHTML = '<p class="cl-gal-vacio">Todavía no hay fotos.</p>'; return; }
    tabs.innerHTML = ks.map(function (k) { return '<button class="cl-btn" type="button" role="tab" data-ed="' + esc(k) + '">' + esc(k) + "</button>"; }).join("");
    mostrar(ks[0]);
    if (malas.length) { aviso.hidden = false; var una = malas.length === 1; aviso.textContent = "Aviso para quien edita: en el CSV de la galería, " + (una ? "la fila " + malas[0] + " no tiene edición y no se muestra." : "las filas " + malas.join(", ") + " no tienen edición y no se muestran."); }
  }
  function error(e) {
    cuerpo.innerHTML = '<p class="cl-gal-vacio">No se pudo cargar la galería.</p>';
    aviso.hidden = false; aviso.textContent = "Aviso para quien edita: " + e.message + ". Revisa la URL del CSV en la Configuración del fragmento.";
  }
  var empezar = function () { window.clCSV(url).then(cargar, error); };
  if (window.clCSV) empezar(); else document.addEventListener("cl-base", empezar, { once: true });
})();
