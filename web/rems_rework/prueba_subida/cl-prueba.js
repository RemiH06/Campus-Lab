/* Prueba de subida: si este archivo carga, escribe en el renglón 2 y prueba las fotos. */
(function () {
  var box = document.getElementById("cl-prueba2"); if (!box) return;
  var $ = function (id) { return document.getElementById(id); };
  $("p2-js").textContent = "2. El .js subido a Documentos y Medios corre. ✔";
  var foto = box.dataset.foto;
  if (!foto || foto.indexOf("PEGAR") === 0) { $("p2-foto").textContent = "3. Falta pegar la URL de la foto."; return; }
  [["", "original"], ["?imagePreview=1", "1000 px"], ["?imageThumbnail=1", "300 px"]].forEach(function (v, i) {
    var img = new Image();
    img.onload = function () { $("p2-f" + i).textContent = v[1] + ": " + img.naturalWidth + "×" + img.naturalHeight + " ✔"; };
    img.onerror = function () { $("p2-f" + i).textContent = v[1] + ": no cargó ✘"; };
    img.src = foto + v[0];
  });
  $("p2-foto").textContent = "3. Tamaños de la foto:";
})();
