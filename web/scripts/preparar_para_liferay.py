"""
Convierte un prototipo (web/fuentes/prototipos/*_plantilla.html) en un fragmento de Liferay.

Los prototipos traen las fotos incrustadas (varios MB) y estilos de página completa. Este script:
  · saca los datos a un JSON aparte (se sube a Documentos y Medios) y el HTML los pide con fetch;
  · quita lo que es solo de la vista previa (fuente de Google, estilos de body/:root);
  · renombra las clases que chocan con Bootstrap/Clay del tema de ITESO (.btn, .card, .toast…) a cl-*;
  · sube la especificidad del reinicio (:where → :is) para ganarle a los h1/p del tema.

Uso (desde la raíz del repo):
    python web/scripts/preparar_para_liferay.py <plantilla.html> <datos.json> <nombre-fragmento>
Ejemplos:
    python web/scripts/preparar_para_liferay.py web/fuentes/prototipos/propuestas_plantilla.html <datos.json> prototipo-plantillas
    python web/scripts/preparar_para_liferay.py web/fuentes/prototipos/componentes_plantilla.html <datos.json> prototipo-componentes

Salida: web/fragmentos/<nombre-fragmento>/ (sin datos, va al repo) y
catalogo/salida/liferay_subir/prototipos/<nombre-fragmento>.json (con fotos, no va al repo; se sube con ese nombre).

Vista previa local (para ver los cambios sin pegarlos en Liferay): agregar --vista-previa al final. Escribe además
catalogo/salida/sitio_campuslab/<nombre-fragmento>.html, la plantilla con los datos dentro; se abre con doble clic.
"""
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHOCAN = ["btn", "card", "field", "muted", "solid", "sr", "toast"]


def renombrar_clases(t):
    # selectores CSS: .btn → .cl-btn (no toca .btn-algo ni .sr-only)
    t = re.sub(r"\.(%s)\b(?![-\w])" % "|".join(CHOCAN), r".cl-\1", t)

    # atributos class="..." (también dentro de cadenas de JS)
    def cls(m):
        toks = [("cl-" + x) if x in CHOCAN else x for x in m.group(2).split(" ")]
        return m.group(1) + " ".join(toks) + m.group(3)
    t = re.sub(r'(class=")([^"<>+]*)(")', cls, t)
    t = re.sub(r'(class=")([^"<>]*?)(\'|"\s*\+)', cls, t)
    # querySelector(".toast"), className = "..."
    t = re.sub(r'(querySelector(?:All)?\(")\.(%s)\b' % "|".join(CHOCAN), r"\1.cl-\2", t)
    return t


def blindar(t):
    r"""Viene de cuando esto se pegaba en un Contenido Web; en un fragmento no hace falta pero no estorba.
    El editor de Liferay (campo detalle de "Basica") limpia el código al guardar: borra "innerHTML ="
    y cambia los caracteres no ASCII dentro de <script> y <style>. Se evita escribiendo la propiedad por
    partes y escapando todo lo que no sea ASCII (\uXXXX en JS, \XXXXXX en CSS)."""
    def js(m):
        s = re.sub(r"\.innerHTML\s*=", '["inner" + "HTML"] =', m.group(2))
        s = "".join(c if ord(c) < 128 else ("\\u%04x" % ord(c) if ord(c) < 0x10000 else "\\u{%x}" % ord(c)) for c in s)
        return m.group(1) + s + m.group(3)

    def css(m):
        return m.group(1) + "".join(c if ord(c) < 128 else "\\%06x" % ord(c) for c in m.group(2)) + m.group(3)
    t = re.sub(r"(<script>)(.*?)(</script>)", js, t, flags=re.S)
    t = re.sub(r"(<style>)(.*?)(</style>)", css, t, flags=re.S)
    assert not re.search(r"innerHTML\s*=", t)
    return t


def para_fragmento(t, carpeta, nombre_json):
    """Versión Fragmento (Diseño > Fragmentos): pestañas HTML, CSS, JavaScript y Configuración.
    Se guardan como código, sin el limpiador del editor de Contenido Web, y el fragmento se arrastra
    a cualquier página de contenido. La URL del JSON queda como opción editable del fragmento."""
    css = "\n".join(re.findall(r"<style>(.*?)</style>", t, flags=re.S))
    scripts = re.findall(r"<script>(.*?)</script>", t, flags=re.S)
    marcado = re.sub(r"<style>.*?</style>|<script>.*?</script>|<!--.*?-->", "", t, flags=re.S).strip()
    # el contenedor de datos va como <div hidden>: el HTML del fragmento no debe llevar <script>
    marcado = re.sub(r'<script type="application/json" id="([\w-]+)"></script>', r'<div id="\1" hidden></div>', marcado)
    marcado = "".join(c if ord(c) < 128 else "&#x%x;" % ord(c) for c in marcado)
    js = "\n".join(scripts).replace(
        f'var url = "/documents/d/campuslab/{nombre_json}";',
        f'var url = (typeof configuration !== "undefined" && configuration.datos) || "/documents/d/campuslab/{nombre_json}";')
    config = {"fieldSets": [{"fields": [{
        "name": "datos", "label": "URL del JSON de datos", "type": "text",
        "typeOptions": {"placeholder": f"/documents/d/campuslab/{nombre_json}"},
        "defaultValue": f"/documents/d/campuslab/{nombre_json}"}]}]}
    carpeta.mkdir(parents=True, exist_ok=True)
    nota = "Generado por web/scripts/preparar_para_liferay.py; no editar a mano."
    (carpeta / "index.html").write_text(f"<!-- {nota} -->\n" + marcado + "\n", encoding="utf-8")
    (carpeta / "index.css").write_text(f"/* {nota} */\n" + css, encoding="utf-8")
    (carpeta / "index.js").write_text(f"/* {nota} */\n" + js, encoding="utf-8")
    (carpeta / "configuration.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def convertir(plantilla, datos, nombre_json):
    t = Path(plantilla).read_text(encoding="utf-8")
    # 1. fuera lo que es solo de la vista previa
    t = re.sub(r"<title>.*?</title>\n|<meta name=\"claude[^>]*>\n|<link rel=\"(?:preconnect|stylesheet)\" href=\"https://fonts[^>]*>\n", "", t)
    t = re.sub(r":root \{ --page:.*?\nbody \{ background: var\(--page\); \}\n", "", t, flags=re.S)
    t = t.replace(" min-height: 100vh;", "")
    t = t.replace(":where(", ":is(")
    # Dentro de /web/general/detalle (estructura "Basica", campo detalle) la plantilla Detalle BN6
    # le pone 17.5% de margen lateral, letra a 1.3em y los botones de compartir encima: se anulan.
    t = t.replace("</style>", "#detalle:has(.cl) { padding-left: 0 !important; padding-right: 0 !important; font-size: 16px !important; min-height: 0 !important; }\n"
                  "#detalle:has(.cl) > #share-media { display: none; }\n</style>", 1)
    t = renombrar_clases(t)
    # 2. los datos llegan por fetch: la función principal se registra y corre cuando llegan
    m = re.search(r'<script type="application/json" id="([\w-]+)">/\*__DATOS__\*/</script>', t)
    assert m, "no encontré el bloque de datos /*__DATOS__*/"
    id_datos = m.group(1)
    assert t.count('(function () {\n  "use strict";') == 1 and t.rstrip().endswith("})();\n</script>".strip())
    t = t.replace('(function () {\n  "use strict";', 'window.CL_PROTO = function () {\n  "use strict";')
    t = t[: t.rstrip().rfind("})();")] + "};\n</script>\n"
    # barra de carga: el CSS sale de cl-base.css (bloque carga:inicio … carga:fin) para no tener dos versiones
    base_css = (REPO / "web" / "fuentes" / "comun" / "cl-base.css").read_text(encoding="utf-8")
    t = t.replace("</style>", re.search(r"/\* carga:inicio.*?/\* carga:fin \*/", base_css, re.S).group(0) + "\n</style>", 1)
    cargador = (
        '<script>\n(function () {\n'
        '  var url = "/documents/d/campuslab/' + nombre_json + '";\n'
        '  try { var modo = localStorage.getItem("cl-modo"); if (modo) document.querySelector(".cl").dataset.modo = modo; } catch (e) {}\n'
        '  var host = document.getElementById("cl-vista") || document.querySelector(".cl");\n'
        '  host.insertAdjacentHTML("afterbegin", \'<div class="cl-carga cl-indet" role="progressbar" aria-label="Cargando datos" aria-valuemin="0" aria-valuemax="100"><span class="cl-carga-t">Cargando datos…</span><span class="cl-carga-b"><i></i></span></div>\');\n'
        '  var barra = host.querySelector(".cl-carga"), mb = function (b) { return (b / 1048576).toFixed(1); };\n'
        '  function avance(n, t) {\n'
        '    if (!t) return; var p = Math.min(100, Math.round(n / t * 100));\n'
        '    barra.classList.remove("cl-indet"); barra.style.setProperty("--p", p + "%"); barra.setAttribute("aria-valuenow", p);\n'
        '    barra.querySelector(".cl-carga-t").textContent = "Cargando datos · " + mb(n) + " de " + mb(t) + " MB (" + p + " %)";\n'
        '  }\n'
        '  fetch(url, { credentials: "same-origin" })\n'
        '    .then(function (r) {\n'
        '      if (!r.ok) throw new Error("HTTP " + r.status);\n'
        '      var total = +r.headers.get("Content-Length") || 0, lector = r.body && r.body.getReader ? r.body.getReader() : null;\n'
        '      if (!lector) return r.text();\n'
        '      var trozos = [], n = 0;\n'
        '      return (function leer() { return lector.read().then(function (x) {\n'
        '        if (x.done) { var b = new Uint8Array(n), o = 0; trozos.forEach(function (c) { b.set(c, o); o += c.length; }); return new TextDecoder().decode(b); }\n'
        '        trozos.push(x.value); n += x.value.length; avance(n, total); return leer();\n'
        '      }); })();\n'
        '    })\n'
        '    .then(function (txt) { if (txt.charAt(0) !== "{") throw new Error("la URL no regresa un JSON"); return txt; })\n'
        '    .then(function (txt) { barra.remove(); document.getElementById("' + id_datos + '").textContent = txt; window.CL_PROTO(); })\n'
        '    .catch(function (e) { barra.remove(); var p = document.createElement("p"); p.style.padding = "16px"; p.textContent = "No se pudieron cargar los datos del prototipo (" + e.message + ")."; document.querySelector(".cl").prepend(p); });\n'
        "})();\n</script>\n"
    )
    t = blindar(t.replace(m.group(0), '<script type="application/json" id="' + id_datos + '"></script>') + cargador)
    carpeta = REPO / "web" / "fragmentos" / nombre_json
    para_fragmento(t, carpeta, nombre_json)
    dj = REPO / "catalogo" / "salida" / "liferay_subir" / "prototipos" / f"{nombre_json}.json"
    dj.parent.mkdir(parents=True, exist_ok=True)
    if Path(datos).resolve() != dj.resolve():
        shutil.copyfile(datos, dj)
    print(f"{carpeta.relative_to(REPO)}/  ({(carpeta / 'index.js').stat().st_size // 1024} KB de JS)")
    print(f"{dj.relative_to(REPO)}  ({dj.stat().st_size // 1024} KB)")


def vista_previa(plantilla, datos, nombre):
    """La plantilla tal cual, con el JSON en su bloque /*__DATOS__*/: la misma página que el fragmento, sin Liferay."""
    t = Path(plantilla).read_text(encoding="utf-8")
    j = Path(datos).read_text(encoding="utf-8").replace("</", "<\\/")
    assert "/*__DATOS__*/" in t, "no encontré el bloque de datos /*__DATOS__*/"
    destino = REPO / "catalogo" / "salida" / "sitio_campuslab" / f"{nombre}.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    t = t.replace("/*__DATOS__*/", j, 1)
    if "charset" not in t[:500].lower():  # sin esto, abierta con doble clic se lee como Windows-1252 y los acentos rompen el JS
        t = '<meta charset="utf-8">\n' + t
    destino.write_text(t, encoding="utf-8")
    print(f"{destino.relative_to(REPO)}  (vista previa con datos)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--vista-previa"]
    if len(args) != 3:
        sys.exit(__doc__)
    convertir(*args)
    if "--vista-previa" in sys.argv:
        vista_previa(*args)
