/* Línea de tiempo: lee un CSV (edicion, desde, hasta, etapa, detalle) editado en Excel y lo pinta por edición, con
   lo ya pasado relleno, lo que viene punteado y una marca de "hoy". Fechas: año-mes-día (2025-04-22) o año-mes (2026-11)
   si todavía no hay día. El CSV lo lee el Marco (window.clCSV); si este fragmento carga antes, lo espera. */
(function () {
  var sec = fragmentElement.querySelector(".cl-lt");
  if (!sec) return;
  var lista = sec.querySelector(".cl-lt-ediciones"), aviso = sec.querySelector(".cl-aviso-editor");
  var url = (sec.dataset.csv || "").trim() || "/documents/d/campuslab/fechas-naturalista";
  var MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  var MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  /* "2025-04-22" → día exacto; "2026-11" → todo el mes (fin = último día) */
  var fecha = function (s) {
    var m = /^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$/.exec((s || "").trim()); if (!m) return null;
    var a = +m[1], me = +m[2] - 1, d = m[3] ? +m[3] : 0;
    return { ini: new Date(a, me, d || 1), fin: d ? new Date(a, me, d) : new Date(a, me + 1, 0), dia: !!d, a: a, m: me, d: d };
  };
  var txt = function (f, conAnio) { return (f.dia ? f.d + " " + MES[f.m] : MESL[f.m]) + (conAnio ? " " + f.a : ""); };
  var rango = function (a, b) { return b ? txt(a, a.a !== b.a) + " al " + txt(b, true) : txt(a, true); };
  var hoy = new Date(); hoy.setHours(0, 0, 0, 0);

  function pintar(filas) {
    var malas = [], ed = {};
    filas.forEach(function (r) {
      var a = fecha(r.desde), b = r.hasta ? fecha(r.hasta) : null;
      if (!r.edicion || !a || (r.hasta && !b)) { malas.push(r._fila); return; }
      (ed[r.edicion] = ed[r.edicion] || []).push({ a: a, b: b, etapa: r.etapa, detalle: r.detalle, fin: (b || a).fin });
    });
    var anios = Object.keys(ed).sort();
    var hoyPuesto = false, html = anios.map(function (k) {
      var et = ed[k].sort(function (x, y) { return x.a.ini - y.a.ini; });
      var pasada = et.every(function (e) { return e.fin < hoy; }), futura = et[0].a.ini > hoy;
      var items = et.map(function (e) {
        var estado = e.fin < hoy ? "pasado" : e.a.ini > hoy ? "futuro" : "ahora", marca = "";
        if (!hoyPuesto && estado !== "pasado") {
          hoyPuesto = true;
          if (estado === "futuro") marca = '<li class="cl-lt-hoy" aria-label="Hoy"><span class="cl-lt-fecha">Hoy, ' + hoy.getDate() + " " + MES[hoy.getMonth()] + " " + hoy.getFullYear() + "</span><b>Estás aquí</b></li>";
        }
        return marca + '<li class="cl-lt-etapa" data-estado="' + estado + '"><span class="cl-lt-fecha">' + esc(rango(e.a, e.b)) + "</span><b>" + esc(e.etapa) +
          (estado === "ahora" ? ' <span class="cl-lt-ahora">ahora</span>' : "") + "</b>" + (e.detalle ? "<span>" + esc(e.detalle) + "</span>" : "") + "</li>";
      }).join("");
      return '<li class="cl-lt-ed" data-estado="' + (pasada ? "pasada" : futura ? "proxima" : "actual") + '"><h3 class="cl-lt-anio">' + esc(k) +
        '<span class="cl-sr">' + (pasada ? ", edición pasada" : futura ? ", próxima edición" : ", edición en curso") + "</span></h3><ol class=\"cl-lt-etapas\">" + items + "</ol></li>";
    }).join("");
    lista.innerHTML = html || '<li class="cl-lt-cargando">Todavía no hay fechas.</li>';
    lista.removeAttribute("aria-busy");
    if (malas.length) { aviso.hidden = false; var una = malas.length === 1; aviso.textContent = "Aviso para quien edita: en el CSV de fechas, " + (una ? "la fila " : "las filas ") + malas.join(", ") + (una ? " no tiene" : " no tienen") + " edición o una fecha que no es año-mes-día (2025-04-22) ni año-mes (2026-11). No se " + (una ? "muestra." : "muestran."); }
  }
  function error(e) {
    lista.innerHTML = '<li class="cl-lt-cargando">No se pudieron cargar las fechas.</li>'; lista.removeAttribute("aria-busy");
    aviso.hidden = false; aviso.textContent = "Aviso para quien edita: " + e.message + ". Revisa la URL del CSV en la Configuración del fragmento.";
  }
  var empezar = function () { window.clCSV(url).then(pintar, error); };
  /* sin el Marco nuevo (el que trae window.clCSV) la lista nunca llegaría: al terminar de cargar la página se avisa */
  var sinMarco = function () { if (!window.clCSV) error(new Error("en esta página falta el Marco Campus Lab con la base de los fragmentos (la versión de octubre de 2026): sin él no hay colores ni listas")); };
  if (document.readyState === "complete") setTimeout(sinMarco, 0); else window.addEventListener("load", sinMarco, { once: true });
  if (window.clCSV) empezar(); else document.addEventListener("cl-base", empezar, { once: true });
})();
