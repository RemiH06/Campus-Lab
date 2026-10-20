"""Genera el planeador de rutas del inventario de árboles (un solo HTML, sin servidor).

Grafo caminable = calles y andadores de OpenStreetMap + conexiones entre árboles vecinos
(OSM casi no tiene los andadores internos de los jardines), sin cruzar edificios.
Por jardín precalcula un recorrido cerrado por todos sus árboles (vecino más cercano + 2-opt
sobre distancias de Dijkstra). El HTML corre Dijkstra en el navegador para llegar desde el
punto de inicio (Edificio V por default) y reparte los recorridos en jornadas.

Uso (desde esta carpeta):  python construir.py [--osm-nuevo]
Salida: catalogo/salida/inventario_arboles/rutas_jardines.html (gitignorado).
"""
import csv
import json
import math
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import openpyxl
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI.parents[1] / "salida" / "inventario_arboles"
CSV_ARCGIS = SALIDA / "arcgis_2014_2018_export.csv"
XLSX_MAESTRO = SALIDA / "Inventario_Maestro.xlsx"
OSM_CACHE = SALIDA / "osm_campus.json"
PLANTILLA = AQUI / "plantilla.html"
DESTINO = SALIDA / "rutas_jardines.html"

CAJA = (20.6015, -103.4235, 20.6125, -103.4095)  # sur, oeste, norte, este (campus Tlaquepaque)
LAT0, LON0 = 20.607, -103.416
M = 111320.0
COSL = math.cos(math.radians(LAT0))

CAMINABLE = {"footway", "path", "pedestrian", "steps", "cycleway", "service", "living_street",
             "residential", "tertiary", "unclassified", "track", "busway", "corridor"}
DENSIFICAR_M = 12      # nodos cada 12 m en los caminos de OSM, para que los árboles se enganchen cerca
VECINOS_ARBOL = 5      # cada árbol se conecta con sus 5 árboles más cercanos...
MAX_ARBOL_M = 35       # ...si están a menos de 35 m
VECINOS_CAMINO = 3     # y con los 3 nodos de camino más cercanos...
MAX_CAMINO_M = 90      # ...si están a menos de 90 m
PENALIZA_PASTO = 1.15  # caminar por jardín cuesta un poco más que por andador


def xy(lat, lon):
    return ((lon - LON0) * M * COSL, (lat - LAT0) * M)


def latlon(x, y):
    return (LAT0 + y / M, LON0 + x / (M * COSL))


def bajar_osm():
    s, w, n, e = CAJA
    caja = f"({s},{w},{n},{e})"
    q = f'[out:json][timeout:90];(way["highway"]{caja};way["building"]{caja};);out geom tags;'
    datos = urllib.parse.urlencode({"data": q}).encode()
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                "https://overpass.private.coffee/api/interpreter"):
        try:
            req = urllib.request.Request(url, data=datos, headers={"User-Agent": "CampusLab-ITESO/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                OSM_CACHE.write_bytes(r.read())
            return
        except OSError as e:  # 502/504 de Overpass son comunes; probar el siguiente espejo
            print(f"  {url}: {e}")
    raise SystemExit("Ningún servidor de Overpass respondió; reintentar más tarde.")


def cruza(p, q, r, s):
    """¿El segmento pq cruza el segmento rs? (cruce propio)"""
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (o(p, q, r) * o(p, q, s) < 0) and (o(r, s, p) * o(r, s, q) < 0)


def dentro(pt, poli):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poli, poli[1:] + poli[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


class Edificios:
    def __init__(self, polis):
        self.polis = polis
        self.cajas = [(min(p[0] for p in pl), min(p[1] for p in pl),
                       max(p[0] for p in pl), max(p[1] for p in pl)) for pl in polis]

    def bloquea(self, a, b):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        mitad = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        for pl, (bx0, by0, bx1, by1) in zip(self.polis, self.cajas):
            if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
                continue
            if dentro(mitad, pl):
                return True
            if any(cruza(a, b, r, s) for r, s in zip(pl, pl[1:] + pl[:1])):
                return True
        return False


def leer_arboles():
    arboles = []
    with open(CSV_ARCGIS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                lat, lon = float(r["Latitud"]), float(r["Longitud"])
            except ValueError:
                continue
            jardin = r["Jardín"].replace("CamellÛn", "Camellón").replace("Area", "Área")
            if r["ID_J"] == "0" or not (CAJA[0] < lat < CAJA[2] and CAJA[1] < lon < CAJA[3]):
                continue  # Casa Clavígero está en el centro de Guadalajara; y coordenadas fuera del campus
            arboles.append({"placa": r["Placa"], "jardin": jardin, "comun": r["Nom_comun"].strip() or r["Especie"].strip(),
                            "cientifico": r["Nom_cien"].strip(), "lat": lat, "lon": lon,
                            "fuente": "ArcGIS 2014-2018", "obs": r["Obs"].strip()})
    # Jardín Contemplativo (fuera del mapa de Hugo): fotos de SW Maps del 2-oct
    ws = openpyxl.load_workbook(XLSX_MAESTRO, read_only=True)["Jardín Contemplativo (2-oct)"]
    filas = ws.iter_rows(values_only=True)
    enc = next(filas)
    i = {k: n for n, k in enumerate(enc)}
    for f in filas:
        if f[i["latitud"]] is None:
            continue
        arboles.append({"placa": f"C-{f[i['num']]}", "jardin": "Jardín Contemplativo (sin ficha)",
                        "comun": "sin identificar", "cientifico": f"¿{f[i['sugerida_1']]}? (Pl@ntNet)",
                        "lat": float(f[i["latitud"]]), "lon": float(f[i["longitud"]]),
                        "fuente": "SW Maps 2-oct-2026", "obs": ""})
    return arboles


def construir():
    if "--osm-nuevo" in sys.argv or not OSM_CACHE.exists():
        print("Bajando OSM...")
        bajar_osm()
    osm = json.loads(OSM_CACHE.read_text(encoding="utf-8"))["elements"]

    nodos, idx = [], {}

    def nodo(p):
        k = (round(p[0], 1), round(p[1], 1))
        if k not in idx:
            idx[k] = len(nodos)
            nodos.append(p)
        return idx[k]

    aristas = {}

    def arista(a, b, w):
        if a != b:
            k = (min(a, b), max(a, b))
            aristas[k] = min(w, aristas.get(k, w))

    polis, nombrados = [], []
    for e in osm:
        t, g = e.get("tags", {}), e.get("geometry", [])
        if "building" in t and len(g) > 3:
            pl = [xy(p["lat"], p["lon"]) for p in g[:-1]]
            polis.append(pl)
            if t.get("name"):
                cx, cy = sum(p[0] for p in pl) / len(pl), sum(p[1] for p in pl) / len(pl)
                nombrados.append({"nombre": t["name"], "x": cx, "y": cy, "poli": pl})
        elif t.get("highway") in CAMINABLE and t.get("access") != "no":
            pts = [xy(p["lat"], p["lon"]) for p in g]
            ant = nodo(pts[0])
            for a, b in zip(pts, pts[1:]):
                L = math.dist(a, b)
                partes = max(1, math.ceil(L / DENSIFICAR_M))
                for k in range(1, partes + 1):
                    p = (a[0] + (b[0] - a[0]) * k / partes, a[1] + (b[1] - a[1]) * k / partes)
                    n = nodo(p)
                    arista(ant, n, L / partes)
                    ant = n
    n_camino = len(nodos)
    edif = Edificios(polis)

    arboles = leer_arboles()
    for a in arboles:
        a["x"], a["y"] = xy(a["lat"], a["lon"])
        a["nodo"] = len(nodos)
        nodos.append((a["x"], a["y"]))

    P = np.array(nodos)
    kd_camino = cKDTree(P[:n_camino])
    kd_arbol = cKDTree(P[n_camino:])
    sin_conexion = 0
    for a in arboles:
        p = (a["x"], a["y"])
        ok = 0
        d, j = kd_arbol.query(p, k=VECINOS_ARBOL + 1, distance_upper_bound=MAX_ARBOL_M)
        for dd, jj in zip(d[1:], j[1:]):
            if math.isfinite(dd) and not edif.bloquea(p, tuple(P[n_camino + jj])):
                arista(a["nodo"], n_camino + jj, dd * PENALIZA_PASTO)
                ok += 1
        d, j = kd_camino.query(p, k=VECINOS_CAMINO, distance_upper_bound=MAX_CAMINO_M)
        for dd, jj in zip(d, j):
            if math.isfinite(dd) and not edif.bloquea(p, tuple(P[jj])):
                arista(a["nodo"], jj, dd * PENALIZA_PASTO)
                ok += 1
        if ok == 0:  # último recurso: el camino más cercano aunque cruce algo
            dd, jj = kd_camino.query(p)
            arista(a["nodo"], jj, dd * PENALIZA_PASTO * 2)
            sin_conexion += 1

    # Edificios con nombre: punto de salida = nodo de camino más cercano a su contorno
    inicios = []
    for b in nombrados:
        mejor = min((kd_camino.query(v) for v in b["poli"]), key=lambda t: t[0])
        inicios.append({"nombre": b["nombre"], "nodo": int(mejor[1])})
    inicios.sort(key=lambda b: b["nombre"])

    filas, cols, pesos = [], [], []
    for (a, b), w in aristas.items():
        filas += [a, b]; cols += [b, a]; pesos += [w, w]
    G = csr_matrix((pesos, (filas, cols)), shape=(len(nodos), len(nodos)))
    ncomp, etiqueta = connected_components(G, directed=False)
    principal = np.bincount(etiqueta).argmax()
    fuera = [a["placa"] for a in arboles if etiqueta[a["nodo"]] != principal]

    # Recorrido cerrado por jardín
    por_jardin = defaultdict(list)
    for k, a in enumerate(arboles):
        por_jardin[a["jardin"]].append(k)
    jardines = []
    def num_jardin(nombre):
        n = nombre.split(" - ")[0]
        return (0, int(n)) if n.isdigit() else (1, 0)
    for nombre, ks in sorted(por_jardin.items(), key=lambda t: (num_jardin(t[0]), t[0])):
        ns = [arboles[k]["nodo"] for k in ks]
        D, pred = dijkstra(G, indices=ns, return_predecessors=True)
        Dm = D[:, ns]
        orden = recorrido(Dm)
        tramos = []
        for i in range(len(orden)):
            a, b = orden[i], orden[(i + 1) % len(orden)]
            tramos.append(camino(pred[a], ns[a], ns[b]))
        largo = sum(Dm[orden[i], orden[(i + 1) % len(orden)]] for i in range(len(orden)))
        jardines.append({"nombre": nombre, "arboles": [ks[i] for i in orden], "tramos": tramos,
                         "largo_m": round(float(largo))})
        print(f"  {nombre}: {len(ks)} árboles, recorrido {largo/1000:.2f} km")

    # Solo se exportan los nodos que usa algo; se reindexan para achicar el JSON
    usados = sorted({n for (a, b) in aristas for n in (a, b)})
    nuevo = {n: i for i, n in enumerate(usados)}
    datos = {
        "generado": __import__("datetime").date.today().isoformat(),
        "origen": {"lat0": LAT0, "lon0": LON0, "m": M, "cosl": COSL},
        "nodos": [[round(P[n][0], 1), round(P[n][1], 1)] for n in usados],
        "aristas": [[nuevo[a], nuevo[b], round(w, 1)] for (a, b), w in aristas.items()],
        "edificios": [[[round(x, 1), round(y, 1)] for x, y in pl] for pl in polis],
        "etiquetas": [{"nombre": b["nombre"], "x": round(b["x"]), "y": round(b["y"])} for b in nombrados],
        "caminos_osm": n_camino,
        "inicios": [{"nombre": b["nombre"], "nodo": nuevo[b["nodo"]]} for b in inicios if b["nodo"] in nuevo],
        "arboles": [{"placa": a["placa"], "jardin": a["jardin"], "comun": a["comun"], "cientifico": a["cientifico"],
                     "nodo": nuevo[a["nodo"]], "lat": a["lat"], "lon": a["lon"], "fuente": a["fuente"], "obs": a["obs"]}
                    for a in arboles],
        "jardines": [{**j, "tramos": [[nuevo[n] for n in t] for t in j["tramos"]]} for j in jardines],
    }
    html = PLANTILLA.read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
    DESTINO.write_text(html, encoding="utf-8")
    print(f"Nodos de camino OSM: {n_camino}, árboles: {len(arboles)}, aristas: {len(aristas)}")
    print(f"Árboles sin vecino ni camino (enganchados a la fuerza): {sin_conexion}; fuera del grafo principal: {len(fuera)} {fuera[:10]}")
    print(f"Escrito {DESTINO} ({DESTINO.stat().st_size/1e6:.1f} MB)")


def camino(pred, origen, destino):
    """Nodos del camino más corto origen -> destino (sin el origen), desde la fila de predecesores."""
    seq = []
    n = destino
    while n != origen and n >= 0:
        seq.append(int(n))
        n = pred[n]
    return seq[::-1]


def recorrido(D):
    """Ciclo por todos los puntos: vecino más cercano + 2-opt sobre la matriz de distancias."""
    n = len(D)
    if n <= 2:
        return list(range(n))
    D = np.where(np.isfinite(D), D, 1e6)
    libre = np.ones(n, bool)
    orden = [0]
    libre[0] = False
    for _ in range(n - 1):
        fila = np.where(libre, D[orden[-1]], np.inf)
        j = int(fila.argmin())
        orden.append(j)
        libre[j] = False
    orden = np.array(orden)
    mejora = True
    while mejora:
        mejora = False
        for i in range(n - 2):
            a, b = orden[i], orden[i + 1]
            c = orden[i + 2:]
            d = np.append(orden[i + 3:], orden[0])[: len(c)]
            delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
            k = int(delta.argmin())
            if delta[k] < -1e-6:
                j = i + 2 + k
                orden[i + 1:j + 1] = orden[i + 1:j + 1][::-1]
                mejora = True
    return [int(x) for x in orden]


if __name__ == "__main__":
    construir()
