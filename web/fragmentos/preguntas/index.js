/* Preguntas frecuentes: en el texto editable, cada título (Encabezado 3) es una pregunta y lo que sigue hasta el
   siguiente título es su respuesta. En la página publicada se vuelven un acordeón; en el editor se dejan como texto
   para poder escribirlas. */
(function () {
  var caja = fragmentElement.querySelector(".cl-faq-texto");
  if (!caja || fragmentElement.closest(".page-editor")) return;
  var hijos = [].slice.call(caja.children), actual = null, armado = document.createDocumentFragment();
  hijos.forEach(function (h) {
    if (/^H[2-4]$/.test(h.tagName)) {
      actual = document.createElement("details"); actual.className = "cl-faq-item";
      var s = document.createElement("summary"); s.innerHTML = h.innerHTML; actual.appendChild(s);
      var r = document.createElement("div"); r.className = "cl-faq-resp"; actual.appendChild(r);
      armado.appendChild(actual);
    } else if (actual) actual.lastChild.appendChild(h);
    else armado.appendChild(h); /* texto antes de la primera pregunta: se queda como introducción */
  });
  caja.innerHTML = ""; caja.appendChild(armado); caja.classList.add("cl-faq-armado");
})();
