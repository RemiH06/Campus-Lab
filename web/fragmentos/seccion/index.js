/* Sección Campus Lab. Paleta "auto": la floración que eligió quien visita en cualquier selector del sitio (clave "cl-flor",
   la misma del kit y de los prototipos) o, si no eligió, la del mes. El modo claro/oscuro no necesita JavaScript:
   lo pone el Marco en <html> y la sección lo hereda. */
(function () {
  var sec = fragmentElement.querySelector(".cl-sec");
  if (!sec || sec.dataset.paleta !== "auto") return;
  var porMes = { 12: "clavellina", 1: "clavellina", 2: "rosa-morada", 3: "jacaranda", 4: "primavera", 5: "tabachin", 6: "tabachin", 11: "galeana" };
  var aplica = function () {
    var f = null; try { f = localStorage.getItem("cl-flor"); } catch (e) { /* sin almacenamiento: la del mes */ }
    sec.dataset.paleta = f && f !== "auto" ? f : porMes[new Date().getMonth() + 1] || "lluvias";
  };
  aplica();
  document.addEventListener("cl-flor", aplica); /* otro fragmento de la misma página cambió la floración */
  window.addEventListener("storage", function (e) { if (e.key === "cl-flor") aplica(); }); /* o se cambió en otra pestaña */
})();
