/* Cuenta regresiva del concurso: cuántos días faltan para que abra (próxima edición) o para que cierre (abierta).
   Las fechas salen de la Configuración del fragmento; si están vacías o mal escritas, no se muestra nada. */
(function () {
  var sec = fragmentElement.querySelector(".cl-con");
  if (!sec) return;
  var p = sec.querySelector(".cl-con-cuenta");
  var dia = function (s) { var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec((s || "").trim()); return m ? new Date(+m[1], m[2] - 1, +m[3]) : null; };
  var hoy = new Date(); hoy.setHours(0, 0, 0, 0);
  var faltan = function (d) { return Math.round((d - hoy) / 864e5); };
  var MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var fecha = function (d) { return d.getDate() + " de " + MES[d.getMonth()]; };
  var e = sec.dataset.etapa, a = dia(sec.dataset.apertura), c = dia(sec.dataset.cierre), n;
  if (e === "abierta" && c && (n = faltan(c)) >= 0) p.textContent = n === 0 ? "Hoy es el último día para registrar tu foto" : "Quedan " + n + (n === 1 ? " día" : " días") + " para registrar: cierra el " + fecha(c);
  else if ((e === "proxima" || !e) && a && (n = faltan(a)) > 0) p.textContent = "Faltan " + n + (n === 1 ? " día" : " días") + " para la convocatoria: abre el " + fecha(a);
  if (p.textContent) p.classList.add("cl-con-cuenta-on");
  /* una liga a #bases (de aquí o de otra sección) abre las bases plegadas */
  var bases = sec.querySelector("#bases");
  var abre = function () { if (location.hash === "#bases" && bases) bases.open = true; };
  document.addEventListener("click", function (ev) { var a = ev.target.closest('a[href="#bases"]'); if (a && bases) bases.open = true; });
  window.addEventListener("hashchange", abre); abre();
})();
