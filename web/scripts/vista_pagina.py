"""
Vista previa local de una página armada con fragmentos, sin Liferay: lee una receta (web/contenidos/<página>/pagina.json),
pinta cada fragmento como lo haría Liferay y deja un solo HTML que se abre con doble clic.

Qué imita de Liferay:
  · FreeMarker básico del fragmento: ${configuration.x}, ${fragmentEntryLinkNamespace} y [#if …][#elseif …][#else][/#if]
    con condiciones `configuration.x` o `configuration.x == "valor"` (lo único que usan nuestros fragmentos).
  · La Configuración: los valores por defecto de configuration.json, encima los de la receta.
  · Lo escrito en las zonas editables (data-lfr-editable-id): "textos" de la receta.
  · El JavaScript envuelto en una función con fragmentElement y configuration.
  · Documentos y Medios: los CSV se meten en window.CL_CSV (los lee el Marco) y las imágenes /documents/d/campuslab/X
    se cambian por la foto local X.jpg si existe.
Agrega una barra arriba para cambiar floración y modo (la del tema de ITESO no existe aquí).

Uso (desde la raíz del repo):  python web/scripts/vista_pagina.py web/contenidos/naturalista/pagina.json
Salida (gitignorada): catalogo/salida/vistas/<carpeta de la receta>.html
"""
import json
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parents[2]
FRAG = REPO / "web" / "fragmentos"
SALIDA = REPO / "catalogo" / "salida" / "vistas"
DOC = "/documents/d/campuslab/"


def configuracion(d, propia):
    p = d / "configuration.json"
    base = {f["name"]: f.get("defaultValue") for fs in json.loads(p.read_text(encoding="utf-8"))["fieldSets"] for f in fs["fields"]} if p.exists() else {}
    return {**base, **(propia or {})}


def condicion(texto, cfg):
    m = re.fullmatch(r'\s*configuration\.(\w+)\s*(?:(==|!=)\s*"([^"]*)")?\s*', texto)
    if not m:
        sys.exit(f"Condición FreeMarker que esta vista no entiende: {texto!r}")
    v = cfg.get(m.group(1))
    if not m.group(2):
        return bool(v) and v != "false"
    return (str(v) == m.group(3)) == (m.group(2) == "==")


def freemarker(html, cfg, ns):
    """Resuelve [#if]/[#elseif]/[#else]/[/#if] (anidables) y ${...}."""
    partes = re.split(r"(\[#if [^\]]+\]|\[#elseif [^\]]+\]|\[#else\]|\[/#if\])", html)
    salida, pila = [], []  # pila: [mostrar_rama_actual, ya_hubo_rama_verdadera, padre_visible]
    visible = lambda: all(p[0] for p in pila)  # noqa: E731
    for t in partes:
        if t.startswith("[#if "):
            padre = visible()
            c = padre and condicion(t[5:-1], cfg)
            pila.append([c, c, padre])
        elif t.startswith("[#elseif "):
            p = pila[-1]
            p[0] = p[2] and not p[1] and condicion(t[9:-1], cfg)
            p[1] = p[1] or p[0]
        elif t == "[#else]":
            p = pila[-1]
            p[0] = p[2] and not p[1]
            p[1] = True
        elif t == "[/#if]":
            pila.pop()
        elif visible():
            salida.append(t)
    html = "".join(salida)
    html = html.replace("${fragmentEntryLinkNamespace}", ns)
    return re.sub(r"\$\{configuration\.(\w+)\}", lambda m: str(cfg.get(m.group(1), "")).replace('"', "&quot;"), html)


def textos(html, propios, fotos, rel):
    sopa = BeautifulSoup(html, "html.parser")
    for k, v in (propios or {}).items():
        el = sopa.find(attrs={"data-lfr-editable-id": k})
        if el is None:
            sys.exit(f"La zona editable {k!r} no existe en el fragmento")
        if isinstance(v, dict):  # liga {texto, href} o imagen {src, alt}
            for a in ("href", "src", "alt"):
                if a in v:
                    el[a] = v[a]
            if "texto" in v:
                el.string = v["texto"]
        else:
            el.clear()
            el.append(BeautifulSoup(v, "html.parser"))
    for img in sopa.find_all("img", src=True):  # fotos de Documentos y Medios → las locales
        if img["src"].startswith(DOC) and (fotos / (img["src"][len(DOC):] + ".jpg")).exists():
            img["src"] = rel + "/" + img["src"][len(DOC):] + ".jpg"
    return str(sopa)


def main(receta):
    R = json.loads(receta.read_text(encoding="utf-8"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / (receta.parent.name + ".html")
    fotos = REPO / R.get("documentos", "")
    rel = Path(os.path.relpath(fotos, SALIDA)).as_posix()
    csv = {url: (REPO / ruta).read_text(encoding="utf-8-sig") for url, ruta in R.get("csv", {}).items()}
    css, cuerpo, js = [], [], []
    for i, f in enumerate(R["fragmentos"]):
        d = FRAG / f["fragmento"]
        cfg = configuracion(d, f.get("configuracion"))
        if f["fragmento"] == "galeria":  # la galería pide sus fotos por prefijo: en local, la carpeta con .jpg
            cfg.update({"fotos": rel + "/", "ext": ".jpg"})
        leer = lambda x: (d / f"index.{x}").read_text(encoding="utf-8") if (d / f"index.{x}").exists() else ""  # noqa: E731
        html = textos(freemarker(leer("html"), cfg, f"f{i}"), f.get("textos"), fotos, rel)
        css.append(f"/* ── {f['fragmento']} ── */\n" + leer("css"))
        cuerpo.append(f'<div class="lfr-fragmento" id="f{i}" data-fragmento="{f["fragmento"]}">{html}</div>')
        if leer("js"):
            js.append(f"(function(){{var fragmentElement=document.getElementById('f{i}');var configuration={json.dumps(cfg, ensure_ascii=False)};\n{leer('js')}\n}})();")
    barra = """<div class="vista-barra"><b>Vista previa local</b>
<label>Floración <select id="vista-flor"><option value="auto">La del mes</option><option value="clavellina">Clavellina</option><option value="rosa-morada">Rosa morada</option><option value="jacaranda">Jacaranda</option><option value="primavera">Primavera</option><option value="tabachin">Tabachín</option><option value="lluvias">Lluvias</option><option value="galeana">Galeana</option></select></label>
<button id="vista-modo" type="button">Cambiar modo</button></div>
<script>(function(){var s=document.getElementById("vista-flor"),g=function(k){try{return localStorage.getItem(k)}catch(e){return null}},p=function(k,v){try{localStorage.setItem(k,v)}catch(e){}};
s.value=g("cl-flor")||"auto";s.onchange=function(){p("cl-flor",s.value);document.dispatchEvent(new CustomEvent("cl-flor"))};
document.getElementById("vista-modo").onclick=function(){var o=g("cl-modo")||(matchMedia("(prefers-color-scheme: dark)").matches?"oscuro":"claro");p("cl-modo",o==="oscuro"?"claro":"oscuro");document.dispatchEvent(new CustomEvent("cl-modo"))};})();</script>"""
    pagina = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{R['titulo']} · vista previa</title>
<link rel="stylesheet" href="https://fonts.bunny.net/css?family=figtree:400,600,700&display=swap">
<style>
body {{ margin: 0; background: var(--cl-bg); color: var(--cl-ink); }}
.vista-barra {{ position: sticky; top: 0; z-index: 1001; display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; padding: 8px 16px; font: 14px system-ui, sans-serif;
  background: light-dark(#e9edec, #13222b); color: light-dark(#12283a, #e3ece9); border-bottom: 1px solid light-dark(#d2dcdb, #29404a); }}
{chr(10).join(css)}
</style>
</head>
<body>
{barra}
<main>
{chr(10).join(cuerpo)}
</main>
<script>window.CL_CSV = {json.dumps(csv, ensure_ascii=False)};</script>
<script>
{chr(10).join(j.replace("</script", "<\\/script") for j in js)}
</script>
</body>
</html>
"""
    destino.write_text(pagina, encoding="utf-8")
    print(f"Vista: {destino} ({len(pagina) // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
