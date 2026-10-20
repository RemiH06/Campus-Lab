# -*- coding: utf-8 -*-
"""Busca fichas de especie de bosque.iteso.mx que no estan enlazadas desde ninguna pagina.

Contexto (8-oct): la ficha de Palo verde (group_id 19307866) no la enlaza nada y el sitio no esta
en buscadores. Las fichas de un mismo lote suelen tener IDs cercanos, asi que se sondea una ventana
alrededor de los IDs conocidos, una peticion cada 0.4 s. Guarda el HTML de las que parezcan ficha
de arbol (tienen "Familia" y "Lugar de origen"). Resumible. Solo lee paginas publicas.

Uso: python sondeo_fichas_bosque.py [id_centro] [radio]
"""
import json
import re
import sys
import time
from pathlib import Path

import scraper_liferay as s

sys.stdout.reconfigure(encoding="utf-8")
CENTRO = int(sys.argv[1]) if len(sys.argv) > 1 else 19307866
RADIO = int(sys.argv[2]) if len(sys.argv) > 2 else 400
CARPETA = Path(__file__).resolve().parents[2] / "catalogo" / "salida" / "sitio_bosque"
HTML_DIR = CARPETA / "fichas_html"
SALIDA = CARPETA / "sondeo_fichas.json"
HTML_DIR.mkdir(parents=True, exist_ok=True)

vistos = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
encontradas = 0
for gid in range(CENTRO - RADIO, CENTRO + RADIO + 1):
    clave = str(gid)
    if clave in vistos:
        continue
    try:
        h = s.descargar(f"https://bosque.iteso.mx/web/general/detalle?group_id={gid}")
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        titulo = t.group(1).strip() if t else ""
        bloque = next((b for b in s.extraer_bloques(h) if b["titulo"] == "Detalle BN6"), None)
        es_ficha = bool(bloque) and "Familia" in bloque["texto"] and "Lugar de origen" in bloque["texto"]
        vistos[clave] = {"titulo": titulo, "es_ficha_arbol": es_ficha, "n_imagenes": len(bloque["imagenes"]) if bloque else 0}
        if es_ficha:
            (HTML_DIR / f"{gid}.html").write_text(bloque["html"], encoding="utf-8")
            encontradas += 1
            print(gid, titulo, "| imagenes:", vistos[clave]["n_imagenes"])
    except Exception as e:
        vistos[clave] = {"error": str(e)[:80]}
    if gid % 25 == 0:
        SALIDA.write_text(json.dumps(vistos, ensure_ascii=False, indent=0), encoding="utf-8")
    time.sleep(0.4)
SALIDA.write_text(json.dumps(vistos, ensure_ascii=False, indent=0), encoding="utf-8")
print("listo | fichas de arbol encontradas en esta corrida:", encontradas)
