# -*- coding: utf-8 -*-
"""Baja las fichas de campuslab.iteso.mx (/web/general/detalle?group_id=ID) y las convierte
en datos estructurados.

Hallazgo (8-oct): una ficha NO es un contenido con campos. Es HTML pegado a mano dentro del
Contenido Web (tablas `div.tablaN` con `#tit_tabla` y <table>, ids repetidos, estilos en linea);
la plantilla 'Detalle BN6' solo agrega encabezado, miga de pan y botones de compartir. Hay al
menos dos "formatos" de ficha (orquideas y arboles) con etiquetas distintas, y el listado de
arboles (group_id 8514082) es otra tabla con 261 enlaces. Por eso el parser lee las tablas de
forma generica en vez de depender de etiquetas fijas.

Salidas (catalogo/salida/sitio_campuslab/):
  fichas_html/<group_id>.html   HTML crudo del bloque de la ficha (respaldo, se reusa si existe)
  fichas.json                   campos estructurados por ficha
Solo lee paginas publicas. Resumible.
"""
import html as html_lib
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import scraper_liferay as s

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parents[2]
CARPETA = BASE / "catalogo" / "salida" / "sitio_campuslab"
CRUDO = CARPETA / "sitio_campuslab.json"
SALIDA = CARPETA / "fichas.json"
HTML_DIR = CARPETA / "fichas_html"
SEMILLAS = {"8514082"}  # Listado de Arboles de Casa: no esta enlazado desde las paginas publicas

ENLACE_FICHA = re.compile(r'<a[^>]+href="https?://campuslab\.iteso\.mx/web/general/detalle\?group_id=(\d+)"[^>]*>(.*?)</a>', re.S)
SECCION = re.compile(r'<div class="tabla\d*"[^>]*>(.*?)(?=<div class="tabla\d*"|<!-{3,}CATEGORIES|\Z)', re.S)


def clave(texto):
    """Etiqueta -> clave: sin acentos ni enie, minusculas, guion bajo."""
    plano = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_") or "campo"


def limpio(fragmento):
    t = re.sub(r"<(style|script)\b.*?</\1>", " ", fragmento, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</p>|</li>", " ", t)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", t))).replace("\xa0", " ").strip()


def ids_de_fichas():
    paginas = json.loads(CRUDO.read_text(encoding="utf-8"))
    ids = set(SEMILLAS)
    for pag in paginas.values():
        for b in pag.get("bloques", []):
            ids |= set(re.findall(r"detalle\?group_id=(\d+)", b["html"]))
    return sorted(ids, key=int)


def enlaces_a_fichas(interior):
    return [(limpio(t), gid) for gid, t in ENLACE_FICHA.findall(interior)]


def parsear(interior):
    """Devuelve (campos_planos, secciones). Cada seccion es un div.tablaN con titulo y tabla."""
    secciones, campos = [], {}

    def poner(k, v):
        if not v:
            return
        base, n = k, 2
        while k in campos:           # etiquetas repetidas (ej. 'Hojas' dos veces) no se pisan
            k, n = f"{base}_{n}", n + 1
        campos[k] = v

    for m in SECCION.finditer(interior):
        bloque = m.group(1)
        titulo = re.search(r'id="tit_tabla"[^>]*>(.*?)</div>', bloque, re.S)
        titulo = limpio(titulo.group(1)) if titulo else ""
        thead = re.search(r"<thead>(.*?)</thead>", bloque, re.S)
        sin_thead = re.sub(r"<thead>.*?</thead>", "", bloque, flags=re.S)
        filas = [re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", sin_thead, re.S)]
        filas = [[limpio(c) for c in f] for f in filas if any(limpio(c) for c in f)]
        if thead:                     # cabecera + una fila de valores (Familia / Nombre cientifico / Nombre comun)
            cols = [limpio(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), re.S)]
            if filas:
                for c, v in zip(cols, filas[0]):
                    poner(clave(c), v)
            secciones.append({"titulo": titulo or "cabecera", "tipo": "cabecera", "columnas": cols, "filas": filas})
        elif filas and all(len(f) == 2 for f in filas):   # pares etiqueta / valor
            for etiqueta, valor in filas:
                poner(clave(etiqueta), valor)
            secciones.append({"titulo": titulo, "tipo": "pares", "filas": filas})
        elif filas:                                       # texto libre bajo un titulo
            texto = " ".join(" ".join(f) for f in filas)
            poner(clave(titulo) if titulo else "texto", texto)
            secciones.append({"titulo": titulo, "tipo": "texto", "texto": texto})
    return campos, secciones


def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    fichas = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    pendientes, vistos, externos, i = list(ids_de_fichas()), set(), set(), 0
    while pendientes:
        gid = pendientes.pop(0)
        if gid in vistos:
            continue
        vistos.add(gid)
        i += 1
        url = f"{s.BASE_URL}/web/general/detalle?group_id={gid}"
        archivo = HTML_DIR / f"{gid}.html"
        try:
            if archivo.exists():
                interior, titulo_pag = archivo.read_text(encoding="utf-8"), (fichas.get(gid) or {}).get("titulo_pagina")
            else:
                h = s.descargar(url)
                bloque = next((b for b in s.extraer_bloques(h) if b["titulo"] == "Detalle BN6"), None)
                interior = bloque["html"] if bloque else ""
                archivo.write_text(interior, encoding="utf-8")
                t = re.search(r"<title>(.*?)</title>", h, re.S)
                titulo_pag = html_lib.unescape(t.group(1)).strip() if t else None
                time.sleep(0.3)
            campos, secciones = parsear(interior)
            enlaces = enlaces_a_fichas(interior)
            externos |= set(re.findall(r'https?://(?!campuslab\.iteso\.mx)[a-z.]*iteso\.mx/web/general/detalle\?group_id=\d+', interior))
            imagenes = re.findall(r'<img[^>]+src="(/documents/[^"]+)"', interior)
            tipo = "listado" if len(enlaces) > 10 else ("arbol" if "lugar_de_origen" in campos else ("orquidea" if "distribucion" in campos else "otro"))
            fichas[gid] = {"url": url, "titulo_pagina": titulo_pag, "tipo": tipo, "n_campos": len(campos),
                           "campos": campos, "secciones": secciones, "imagenes": imagenes, "enlaces_a_fichas": enlaces}
            for _, nuevo in enlaces:
                if nuevo not in vistos:
                    pendientes.append(nuevo)
        except Exception as e:
            fichas[gid] = {"url": url, "error": str(e)}
        if i % 25 == 0:
            SALIDA.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{i} (cola {len(pendientes)}) {gid} {fichas[gid].get('titulo_pagina') or fichas[gid].get('error')} [{fichas[gid].get('tipo')}] {fichas[gid].get('n_campos')} campos")
    SALIDA.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fichas:", len(fichas), "| enlaces a otros sitios de ITESO:", sorted(externos))
    print("guardado:", SALIDA)


if __name__ == "__main__":
    main()
