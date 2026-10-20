/* Sección Campus Lab: con "La del mes", la paleta cambia sola según la floración del calendario. */
(function () {
  var sec = fragmentElement.querySelector(".cl-sec");
  if (!sec || sec.dataset.paleta !== "auto") return;
  var mes = new Date().getMonth() + 1;
  var porMes = { 12: "clavellina", 1: "clavellina", 2: "rosa-morada", 3: "jacaranda", 4: "primavera", 5: "tabachin", 6: "tabachin", 11: "galeana" };
  sec.dataset.paleta = porMes[mes] || "lluvias";
})();
