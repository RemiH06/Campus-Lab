"""
Convierte los prototipos del camino B en Contenidos Web para la carpeta de pruebas de Liferay.

Los prototipos traen las fotos incrustadas (varios MB) y estilos de página completa. Este script:
  · saca los datos a un JSON aparte (se sube a Documentos y Medios) y el HTML los pide con fetch;
  · quita lo que es solo de la vista previa (fuente de Google, estilos de body/:root);
  · renombra las clases que chocan con Bootstrap/Clay del tema de ITESO (.btn, .card, .toast…) a cl-*;
  · sube la especificidad del reinicio (:where → :is) para ganarle a los h1/p del tema.

Uso (desde la raíz del repo):
    python web/camino_b/preparar_para_liferay.py <plantilla.html> <datos.json> <NOMBRE_CONTENIDO> <nombre-json>
Ejemplo:
    python web/camino_b/preparar_para_liferay.py web/camino_b/propuestas_plantilla.html <datos_v2.json> CL_PRUEBA_PLANTILLAS_HTML prototipo-arboles

Salida: web/camino_b/liferay/<NOMBRE_CONTENIDO>.html (sin datos, va al repo) y
reestructura/salida/liferay_subir/camino_b/<nombre-json>.json (con fotos, no va al repo).
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
    r"""El editor de Liferay (campo detalle de "Basica") limpia el código al guardar: borra "innerHTML ="
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


def para_pagina(t, base, nombre_json):
    """Versión para Diseño > Personalización (CSS y JavaScript de la página). Esos campos se guardan
    tal cual, sin el limpiador del editor, y solo aplican a esa página. El JS crea el contenedor
    dentro de #main-content, así que la página no necesita ningún Web Content Display."""
    css = "\n".join(re.findall(r"<style>(.*?)</style>", t, flags=re.S))
    scripts = re.findall(r"<script>(.*?)</script>", t, flags=re.S)
    marcado = re.sub(r"<style>.*?</style>|<script>.*?</script>|<!--.*?-->", "", t, flags=re.S).strip()
    marcado = "".join(c if ord(c) < 128 else "&#x%x;" % ord(c) for c in marcado)
    cab = (f"/* Generado por web/camino_b/preparar_para_liferay.py; no editar a mano.\n"
           f"   Pegar en la página: Diseño > Personalización > {{}}. Lee /documents/d/campuslab/{nombre_json}. */\n")
    js = (cab.format("JavaScript") + "(function () {\n  function montar() {\n"
          "    if (document.querySelector('[data-cl-pagina]')) return;\n"
          "    var host = document.getElementById('main-content') || document.body;\n"
          "    var w = document.createElement('div'); w.setAttribute('data-cl-pagina', '');\n"
          "    w['inner' + 'HTML'] = " + json.dumps(marcado).replace("</", "<\\/") + ";\n"
          "    host.insertBefore(w, host.firstChild);\n" + "\n".join(scripts) + "\n  }\n"
          "  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', montar); else montar();\n})();\n")
    base.with_suffix(".pagina.css").write_text(cab.format("CSS") + "[data-cl-pagina] { padding-top: 32px; }\n" + css, encoding="utf-8")
    base.with_suffix(".pagina.js").write_text(js, encoding="utf-8")


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
    nota = "Generado por web/camino_b/preparar_para_liferay.py; no editar a mano."
    (carpeta / "index.html").write_text(f"<!-- {nota} -->\n" + marcado + "\n", encoding="utf-8")
    (carpeta / "index.css").write_text(f"/* {nota} */\n" + css, encoding="utf-8")
    (carpeta / "index.js").write_text(f"/* {nota} */\n" + js, encoding="utf-8")
    (carpeta / "configuration.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def convertir(plantilla, datos, nombre, nombre_json):
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
    cargador = (
        '<script>\n(function () {\n'
        '  var url = "/documents/d/campuslab/' + nombre_json + '";\n'
        '  fetch(url, { credentials: "same-origin" })\n'
        '    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.text(); })\n'
        '    .then(function (txt) { if (txt.charAt(0) !== "{") throw new Error("la URL no regresa un JSON"); return txt; })\n'
        '    .then(function (txt) { document.getElementById("' + id_datos + '").textContent = txt; window.CL_PROTO(); })\n'
        '    .catch(function (e) { var p = document.createElement("p"); p.style.padding = "16px"; p.textContent = "No se pudieron cargar los datos del prototipo (" + e.message + ")."; document.querySelector(".cl").prepend(p); });\n'
        "})();\n</script>\n"
    )
    t = blindar(t.replace(m.group(0), '<script type="application/json" id="' + id_datos + '"></script>') + cargador)
    encabezado = (f"<!-- {nombre} · Contenido Web (pegar en Código fuente), solo para la carpeta de pruebas.\n"
                  f"     Sirve en \"Contenido HTML\" o en el campo detalle de \"Basica\" (/web/general/detalle?group_id=...).\n"
                  f"     Lee /documents/d/campuslab/{nombre_json}: subir {nombre_json}.json a Documentos y Medios con ese nombre.\n"
                  f"     Generado por web/camino_b/preparar_para_liferay.py; no editar a mano. -->\n")
    destino = REPO / "web" / "camino_b" / "liferay" / f"{nombre}.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(encabezado + t, encoding="utf-8")
    para_pagina(t, destino.with_suffix(""), nombre_json)
    para_fragmento(t, destino.parent / "fragmentos" / nombre_json, nombre_json)
    dj = REPO / "reestructura" / "salida" / "liferay_subir" / "camino_b" / f"{nombre_json}.json"
    dj.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(datos, dj)
    print(f"{destino.relative_to(REPO)}  ({destino.stat().st_size // 1024} KB)")
    print(f"{dj.relative_to(REPO)}  ({dj.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    convertir(*sys.argv[1:])
