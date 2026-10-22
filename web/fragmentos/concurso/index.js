/* Cuenta regresiva del concurso: cuántos días faltan para que abra (próxima edición) o para que cierre (abierta).
   Las fechas salen de la Configuración del fragmento; si están vacías o mal escritas no hay cuenta, y quien edita ve
   un aviso en el editor de páginas. Guía en README.md. */
(function () {
  var sec = fragmentElement.querySelector(".cl-con");
  if (!sec) return;
  var p = sec.querySelector(".cl-con-cuenta");
  var dia = function (s) {
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec((s || "").trim()), d = m && new Date(+m[1], m[2] - 1, +m[3]);
    return d && d.getMonth() === m[2] - 1 ? d : null; /* "2026-11-31" no existe: se avisa en vez de pasar al 1 de diciembre */
  };
  var hoy = new Date(); hoy.setHours(0, 0, 0, 0);
  var faltan = function (d) { return Math.round((d - hoy) / 864e5); };
  var MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var fecha = function (d) { return d.getDate() + " de " + MES[d.getMonth()]; };
  var e = sec.dataset.etapa, a = dia(sec.dataset.apertura), c = dia(sec.dataset.cierre), n;
  if (e === "abierta" && c && (n = faltan(c)) >= 0) p.textContent = n === 0 ? "Hoy es el último día para registrar tu foto" : "Quedan " + n + (n === 1 ? " día" : " días") + " para registrar: cierra el " + fecha(c);
  else if ((e === "proxima" || !e) && a && (n = faltan(a)) > 0) p.textContent = "Faltan " + n + (n === 1 ? " día" : " días") + " para la convocatoria: abre el " + fecha(a);
  if (p.textContent) p.classList.add("cl-con-cuenta-on");
  /* aviso solo visible en el editor de páginas: una fecha mal escrita no rompe nada, pero la cuenta no sale */
  var avisos = [];
  [["apertura", sec.dataset.apertura, a], ["cierre", sec.dataset.cierre, c]].forEach(function (x) {
    if (x[1] && x[1].trim() && !x[2]) avisos.push("la fecha de " + x[0] + " (\"" + x[1].trim() + "\") no es año-mes-día, por ejemplo 2026-11-23");
  });
  if (e === "abierta" && !(sec.dataset.cierre || "").trim()) avisos.push("con la convocatoria abierta conviene poner la fecha de cierre, para la cuenta regresiva");
  if (e === "abierta" && c && faltan(c) < 0) avisos.push("la fecha de cierre ya pasó: ¿cambiar la etapa a \"Cerrada, el jurado está revisando\"?");
  if (avisos.length) { var av = sec.querySelector(".cl-aviso-editor"); av.hidden = false; av.textContent = "Aviso para quien edita (Configuración del fragmento): " + avisos.join("; ") + "."; }
  /* una liga a #bases (de aquí o de otra sección) abre las bases plegadas */
  var bases = sec.querySelector("#bases");
  var abre = function () { if (location.hash === "#bases" && bases) bases.open = true; };
  document.addEventListener("click", function (ev) { var a = ev.target.closest('a[href="#bases"]'); if (a && bases) bases.open = true; });
  window.addEventListener("hashchange", abre); abre();
})();
