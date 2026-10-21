"""
Genera lo que se sube a Liferay para el catálogo de árboles (camino B):

  arboles.json       especies: nombres, familia, rasgos de la ficha, árboles por jardín, fotos por parte
  mapa-campus.json   edificios y caminos del campus (OSM) y un punto por árbol con placa (ArcGIS)
  fotos/             una foto por especie y parte (la más pesada), redimensionada al estándar
                     "liferay_hd" (2560 px) de redimensionar_imagenes.py; nombre <especie>-<parte>.jpg
  datos_local.js     los dos JSON en una variable, para ver web/fuentes/vista_local.html sin servidor
  lista_subida.csv   qué archivo va a Documentos y Medios y con qué nombre

Uso (desde la raíz del repo):  python web/scripts/generar_datos_arboles.py
Salida (gitignorada): catalogo/salida/liferay_subir/arboles/
Es resumible: una foto ya redimensionada no se vuelve a hacer (pasar --forzar para rehacerlas).

Reúsa la lectura del inventario de herramientas/rutas_jardines/guia.py (mismas especies, mismas
llaves de iNaturalist para unir sinónimos, mismas erratas corregidas).
"""
import argparse
import csv
import json
import math
import re
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "catalogo" / "herramientas" / "rutas_jardines"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import guia  # noqa: E402
from redimensionar_imagenes import ESTANDARES, redimensionar_una  # noqa: E402

SALIDA = REPO / "catalogo" / "salida" / "liferay_subir" / "arboles"
OSM = guia.SALIDA / "osm_campus.json"
PARTES = {"arbol_completo": "arbol-completo", "tronco": "tronco", "hoja": "hoja", "flor": "flor", "fruto": "fruto"}
CAMINOS = {"footway", "service", "living_street", "steps", "cycleway", "pedestrian", "path", "residential", "tertiary"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", guia.norm(s)).strip("-")


def jardin_corto(j):
    return re.sub(r"^\d+ - ", "", j)


def fotos_elegidas(llave_de):
    """Por (llave de especie, parte): la foto más pesada que exista en el espejo local, con su autor."""
    espejo = Path(json.loads(guia.RUTA_CONFIG.read_text(encoding="utf-8"))["ruta_espejo_local_fotos"])
    con = sqlite3.connect(guia.RUTA_BD)
    filas = con.execute("""
        SELECT f.id, f.ruta_actual, f.tamano_bytes, e.nombre_cientifico, p.parte, a.nombre
        FROM partes_arbol_etiquetas p JOIN fotos f ON f.id = p.foto_id JOIN especies e ON e.id = f.especie_id
        LEFT JOIN autores a ON a.id = f.autor_id
        WHERE f.estado = 'usable' AND f.id NOT IN (SELECT foto_id FROM archivos_no_procesables)
    """).fetchall()
    mejor = {}
    for fid, ruta, peso, nombre, parte, autor in filas:
        if parte not in PARTES:
            continue
        k = (llave_de(guia.binomio(nombre)), parte)
        local = espejo / Path(ruta).name
        if local.exists() and (k not in mejor or (peso or 0) > mejor[k]["peso"]):
            mejor[k] = {"id": fid, "local": local, "peso": peso or 0, "autor": autor}
    return mejor


def mapa(puntos_latlon):
    """Proyección local (equirectangular) a un lienzo de 1000 de ancho; descarta coordenadas fuera del campus."""
    ml = statistics.median(p[1] for p in puntos_latlon)
    mo = statistics.median(p[2] for p in puntos_latlon)
    buenos = [p for p in puntos_latlon if abs(p[1] - ml) < 0.01 and abs(p[2] - mo) < 0.01]
    malos = sorted({p[0] for p in puntos_latlon} - {p[0] for p in buenos}, key=int)
    kx = math.cos(math.radians(ml))
    minx, maxx = min(p[2] for p in buenos) * kx, max(p[2] for p in buenos) * kx
    maxy, miny = max(p[1] for p in buenos), min(p[1] for p in buenos)
    pad = (maxx - minx) * 0.04
    w = 1000
    sc = w / (maxx - minx + 2 * pad)
    h = round((maxy - miny + 2 * pad) * sc)
    X = lambda lon: round((lon * kx - minx + pad) * sc, 1)  # noqa: E731
    Y = lambda lat: round((maxy - lat + pad) * sc, 1)  # noqa: E731
    bld, cam = [], []
    for el in json.loads(OSM.read_text(encoding="utf-8"))["elements"]:
        t, g = el.get("tags", {}), el.get("geometry") or []
        xy = [(X(q["lon"]), Y(q["lat"])) for q in g]
        if not xy or all(not (-80 < x < w + 80 and -80 < y < h + 80) for x, y in xy):
            continue
        d = "M" + " L".join(f"{x},{y}" for x, y in xy)
        if t.get("building") or t.get("leisure") == "pitch":
            bld.append(d + "Z")
        elif t.get("highway") in CAMINOS:
            cam.append(d)
    return {"w": w, "h": h, "bld": bld, "cam": cam}, [(p[0], X(p[2]), Y(p[1]), p[3]) for p in buenos], malos


def construir(forzar=False):
    con = sqlite3.connect(guia.RUTA_BD)
    taxon = {b.lower(): t for b, t in con.execute("SELECT binomio, taxon_id FROM inat_nombres_resueltos WHERE taxon_id IS NOT NULL")}
    llave_de = lambda b: f"t{taxon[b.lower()]}" if b.lower() in taxon else b  # noqa: E731

    fichas = {}
    for v in json.loads(guia.FICHAS.read_text(encoding="utf-8")).values():
        if v["tipo"] == "arbol":
            c = v["campos"]
            fichas[llave_de(guia.binomio(c.get("nombre_cientifico", "")))] = c

    esp, puntos = {}, []
    for a in guia.leer_inventario():
        if not a["especie"]:
            continue
        k = llave_de(a["especie"])
        e = esp.setdefault(k, {"sci": a["especie"], "comunes": defaultdict(int), "n": 0, "jar": defaultdict(int)})
        e["n"] += 1
        e["jar"][jardin_corto(a["jardin"])] += 1
        e["comunes"][a["comun_2018"] or a["comun_2014"]] += 1
        puntos.append((a["placa"], float(a["lat"]), float(a["lon"]), k))

    geo, pts, malos = mapa(puntos)
    elegidas = fotos_elegidas(llave_de)
    ancho, alto = ESTANDARES["liferay_hd"]
    (SALIDA / "fotos").mkdir(parents=True, exist_ok=True)

    llaves = sorted(esp, key=lambda k: esp[k]["sci"])
    indice = {k: i for i, k in enumerate(llaves)}
    especies, subida, ids = [], [], set()
    for k in llaves:
        e, c = esp[k], fichas.get(k, {})
        ident = slug(e["sci"])
        assert ident not in ids, f"id repetido: {ident}"
        ids.add(ident)
        fotos = {}
        for parte, pslug in PARTES.items():
            f = elegidas.get((k, parte))
            if not f:
                continue
            nombre = f"{ident}-{pslug}"
            destino = SALIDA / "fotos" / f"{nombre}.jpg"
            if forzar or not destino.exists():
                redimensionar_una(f["local"], destino, ancho, alto)
            fotos[parte] = {"f": nombre, "a": f["autor"] or ""}
            subida.append([f"{nombre}.jpg", round(destino.stat().st_size / 1024), f["id"], f["autor"] or ""])
        especies.append({
            "id": ident, "sci": e["sci"], "inat": int(k[1:]) if k[0] == "t" and k[1:].isdigit() else None,
            "com": (c.get("nombre_comun") or max(e["comunes"], key=e["comunes"].get) or "").strip(),
            "fam": (c.get("familia") or "").split(" ")[0], "ori": c.get("lugar_de_origen", ""),
            "ras": {r: c[r] for r in guia.RASGOS if c.get(r)},
            "n": e["n"], "jar": dict(sorted(e["jar"].items(), key=lambda t: -t[1])), "fotos": fotos,
        })

    arboles = {"generado": date.today().isoformat(), "fuente": "Inventario ArcGIS 2014-2018, fichas del sitio y fotos confirmadas de Campus Lab",
               "especies": especies}
    geo["pts"] = [[int(p[0]), p[1], p[2], indice[p[3]]] for p in pts]
    sep = (",", ":")
    (SALIDA / "arboles.json").write_text(json.dumps(arboles, ensure_ascii=False, separators=sep), encoding="utf-8")
    (SALIDA / "mapa-campus.json").write_text(json.dumps(geo, ensure_ascii=False, separators=sep), encoding="utf-8")
    (SALIDA / "datos_local.js").write_text(
        "window.CL_DATOS = " + json.dumps({"arboles": arboles, "mapa": geo}, ensure_ascii=False, separators=sep) + ";\n", encoding="utf-8")
    with open(SALIDA / "lista_subida.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["archivo", "kb", "foto_id", "autor"])
        w.writerows([["arboles.json", round((SALIDA / "arboles.json").stat().st_size / 1024), "", ""],
                     ["mapa-campus.json", round((SALIDA / "mapa-campus.json").stat().st_size / 1024), "", ""]] + subida)

    con_foto = sum(1 for e in especies if e["fotos"])
    print(f"{len(especies)} especies ({con_foto} con foto), {len(subida)} fotos, {len(geo['pts'])} árboles en el mapa")
    print(f"Placas con coordenada fuera del campus (no van al mapa): {', '.join(malos) or 'ninguna'}")
    print(f"Fotos: {sum(r[1] for r in subida) / 1024:.1f} MB en total")
    print(f"Escrito en {SALIDA}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--forzar", action="store_true", help="Rehace las fotos aunque ya existan")
    construir(ap.parse_args().forzar)
