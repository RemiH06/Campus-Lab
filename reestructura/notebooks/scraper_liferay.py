# -*- coding: utf-8 -*-
"""Prototipo de scraper de campuslab.iteso.mx (Liferay) que entiende QUE parte es editable.

Idea clave: en Liferay cada bloque editable de una pagina es un "Contenido Web" renderizado
dentro de <div class="journal-content-article" data-analytics-asset-id=... data-analytics-asset-title=...>.
Ese ID/titulo es exactamente lo que se busca en Panel de control > Contenido Web para editarlo.
Todo lo que queda FUERA de esos bloques (cabecera, plantilla del tema, scripts) pertenece al tema
y no se cambia desde el editor de contenido.

Solo lee paginas publicas. No guarda credenciales.
Uso: python scraper_liferay.py            # recorre el sitemap y los enlaces internos
"""
import html as html_lib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
# Otro sitio de ITESO con la misma plataforma: SCRAPER_BASE_URL=https://bosque.iteso.mx python scraper_liferay.py
BASE_URL = os.environ.get("SCRAPER_BASE_URL", "https://campuslab.iteso.mx").rstrip("/")
NOMBRE_SITIO = urllib.parse.urlparse(BASE_URL).netloc.split(".")[0]          # campuslab, bosque...
SALIDA = Path(__file__).resolve().parents[1] / "salida" / f"sitio_{NOMBRE_SITIO}"
SALIDA.mkdir(parents=True, exist_ok=True)

ABRE_BLOQUE = re.compile(r'<div class="journal-content-article\s*"([^>]*)>')


def descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CampusLab-scraper)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def atributo(attrs, nombre):
    m = re.search(rf'{nombre}="([^"]*)"', attrs)
    return html_lib.unescape(m.group(1)) if m else None


def cerrar_div(h, inicio):
    """Devuelve el indice justo despues del </div> que cierra el <div> abierto en `inicio`."""
    prof = 0
    for m in re.finditer(r"<div\b|</div>", h[inicio:]):
        prof += 1 if m.group(0).startswith("<div") else -1
        if prof == 0:
            return inicio + m.end()
    return len(h)


def extraer_bloques(h):
    bloques = []
    for m in ABRE_BLOQUE.finditer(h):
        fin = cerrar_div(h, m.start())
        crudo = h[m.start():fin]
        interior = crudo[m.end() - m.start():-len("</div>")]
        sin_estilo = re.sub(r"<(style|script)\b.*?</\1>", " ", interior, flags=re.S | re.I)
        texto = re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", sin_estilo))).strip()
        attrs = m.group(1)
        bloques.append({
            "article_id": atributo(attrs, "data-analytics-asset-id"),
            "titulo": atributo(attrs, "data-analytics-asset-title"),
            "resource_pk": atributo(attrs, "data-analytics-web-content-resource-pk"),
            "tamano_html": len(interior),
            "texto": texto,
            "iframes": re.findall(r'<iframe[^>]+src="([^"]+)"', interior),
            "imagenes": re.findall(r'<img[^>]+src="([^"]+)"', interior),
            "enlaces": re.findall(r'<a[^>]+href="([^"]+)"', interior),
            "tiene_estilo_propio": bool(re.search(r"<style\b", interior, re.I)),
            "html": interior,
        })
    return bloques


def enlaces_internos(h, url_base):
    salida = set()
    for href in re.findall(r'href="([^"#]+)"', h):
        url = urllib.parse.urljoin(url_base, html_lib.unescape(href))
        p = urllib.parse.urlparse(url)
        # descarta rutas de sistema y basura que sale de cadenas de JavaScript (comillas, llaves, +)
        es_sistema = re.match(r"^/(en/)?(o|c|documents|combo)(/|$)|^/(en/)?web/iteso(/|$)", p.path)
        es_basura = re.search(r"""['"{}+\s]""", p.path)
        if p.netloc == urllib.parse.urlparse(BASE_URL).netloc and not re.search(r"\.(css|js|png|jpe?g|svg|ico|pdf|woff2?)$", p.path, re.I) \
                and not es_sistema and not es_basura:
            salida.add(urllib.parse.urlunparse((p.scheme, p.netloc, p.path.rstrip("/") or "/", "", "", "")))
    return salida


def urls_sitemap():
    idx = descargar(f"{BASE_URL}/sitemap.xml")
    urls = set()
    for sub in re.findall(r"<loc>([^<]+)</loc>", idx):
        for u in re.findall(r"<loc>([^<]+)</loc>", descargar(html_lib.unescape(sub))):
            urls.add(html_lib.unescape(u).rstrip("/"))
    return urls


def main():
    pendientes = deque(sorted(urls_sitemap()))
    vistas, paginas = set(), {}
    while pendientes:
        url = pendientes.popleft()
        if url in vistas:
            continue
        vistas.add(url)
        try:
            h = descargar(url)
        except Exception as e:
            paginas[url] = {"error": str(e)}
            print("ERROR", url, e)
            continue
        titulo = re.search(r"<title>(.*?)</title>", h, re.S)
        bloques = extraer_bloques(h)
        paginas[url] = {"titulo_pagina": html_lib.unescape(titulo.group(1)).strip() if titulo else None,
                        "bloques": bloques}
        nuevos = enlaces_internos(h, url) - vistas
        for n in sorted(nuevos):
            pendientes.append(n)
        print(f"{url}  bloques={len(bloques)}  enlaces_nuevos={len(nuevos)}")
        time.sleep(0.4)
    ruta = SALIDA / f"sitio_{NOMBRE_SITIO}.json"
    ruta.write_text(json.dumps(paginas, ensure_ascii=False, indent=1), encoding="utf-8")
    print("guardado:", ruta, "| paginas:", len(paginas))


def nombre_seguro(texto):
    """Nombre de archivo sin acentos ni enie: 'Navegación' -> 'Navegacion', 'ñ' -> 'n'."""
    plano = unicodedata.normalize("NFKD", texto or "sin_titulo").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "_", plano).strip("_")[:60]


def canonica(url):
    """/web/campuslab/x es la misma pagina que /x: se deja una sola."""
    return url.replace("/web/campuslab", "").rstrip("/")


def exportar(paginas, carpeta):
    """Guarda cada Contenido Web como .html (su codigo tal como lo publica Liferay) y un
    mapa del sitio que dice que pagina usa que componente, en que orden."""
    comp_dir = carpeta / "componentes"
    comp_dir.mkdir(parents=True, exist_ok=True)
    mapa, usos, guardados = {}, {}, {}
    for url, pag in sorted(paginas.items()):
        if "bloques" not in pag or canonica(url) != url:
            continue
        mapa[url] = {"titulo_pagina": pag["titulo_pagina"], "componentes": []}
        for orden, b in enumerate(pag["bloques"], 1):
            cid = b["article_id"]
            archivo = f"{cid}__{nombre_seguro(b['titulo'])}.html"
            if cid not in guardados:
                (comp_dir / archivo).write_text(b["html"], encoding="utf-8")
                guardados[cid] = {"archivo": f"componentes/{archivo}", "titulo": b["titulo"],
                                  "resource_pk": b["resource_pk"], "tamano_html": b["tamano_html"],
                                  "iframes": b["iframes"], "paginas": []}
            guardados[cid]["paginas"].append(url)
            mapa[url]["componentes"].append({"orden": orden, "article_id": cid, "titulo": b["titulo"],
                                             "archivo": f"componentes/{archivo}"})
    (carpeta / "mapa_del_sitio.json").write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    (carpeta / "componentes_indice.json").write_text(json.dumps(guardados, ensure_ascii=False, indent=1), encoding="utf-8")
    return mapa, guardados


if __name__ == "__main__":
    main()
    paginas = json.loads((SALIDA / f"sitio_{NOMBRE_SITIO}.json").read_text(encoding="utf-8"))
    destino = Path(__file__).resolve().parents[2] / "web" / ("liferay_actual" if NOMBRE_SITIO == "campuslab" else f"liferay_actual_{NOMBRE_SITIO}")
    mapa, comps = exportar(paginas, destino)
    print(f"exportado a {destino}: {len(mapa)} paginas, {len(comps)} componentes")
