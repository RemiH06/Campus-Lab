/* Cifras del proyecto de iNaturalist (API abierta, sin cuenta): observaciones, especies y personas. Se guardan 24 h en el
   navegador para no pedirlas en cada visita. Sin JS o sin red quedan las del HTML (las de cuando se armó la página). */
(function () {
  var sec = fragmentElement.querySelector(".cl-cif");
  if (!sec) return;
  var id = (sec.dataset.proyecto || "146508").trim(), clave = "cl-cifras-" + id, DIA = 864e5;
  var MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fmt = function (n) { return Math.round(n).toLocaleString("es-MX"); };

  function poner(d) {
    Object.keys(d.n).forEach(function (k) {
      var dd = sec.querySelector('[data-cifra="' + k + '"]'); if (!dd) return;
      var fin = d.n[k], ini = parseInt(dd.textContent.replace(/\D/g, ""), 10) || 0;
      if (reduce || ini === fin) { dd.textContent = fmt(fin); return; }
      var t0 = performance.now(), paso = function (t) { var p = Math.min((t - t0) / 900, 1), k2 = 1 - Math.pow(1 - p, 3); dd.textContent = fmt(ini + (fin - ini) * k2); if (p < 1) requestAnimationFrame(paso); };
      requestAnimationFrame(paso);
    });
    var f = new Date(d.t);
    sec.querySelector(".cl-cif-fecha").textContent = "Datos de iNaturalist al " + f.getDate() + " de " + MES[f.getMonth()] + " de " + f.getFullYear();
  }
  var guardado = null;
  try { guardado = JSON.parse(localStorage.getItem(clave)); } catch (e) { /* sin almacenamiento: se piden */ }
  if (guardado && Date.now() - guardado.t < DIA) { poner(guardado); return; }
  var api = "https://api.inaturalist.org/v1/observations", q = "?project_id=" + encodeURIComponent(id) + "&per_page=0";
  var total = function (ruta) { return fetch(api + ruta + q).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (j) { return j.total_results; }); };
  /* se piden cuando la sección está por verse, no al cargar la página */
  new IntersectionObserver(function (en, io) {
    if (!en[0].isIntersecting) return; io.disconnect();
    Promise.all([total(""), total("/species_counts"), total("/observers")]).then(function (r) {
      var d = { t: Date.now(), n: { observaciones: r[0], especies: r[1], personas: r[2] } };
      try { localStorage.setItem(clave, JSON.stringify(d)); } catch (e) { /* no pasa nada: se piden la próxima vez */ }
      poner(d);
    }).catch(function () { if (guardado) poner(guardado); });
  }, { rootMargin: "200px" }).observe(sec);
})();
