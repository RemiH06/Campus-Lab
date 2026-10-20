"""
Datos de los mapas 3D de los territorios del ITESO (campus, Casa ITESO Clavigero y predios en el Bosque La Primavera).

Uso (desde la raíz del repo):
    python web/scripts/generar_territorios_3d.py [--forzar]

Salida (gitignorada): catalogo/salida/liferay_subir/mapa3d/territorio-<id>.json, uno por territorio, para subir a
Documentos y Medios. Cada archivo trae, en metros sobre un plano local (x al este, z al sur, origen en el centro):
  lim   contorno del territorio (polígonos)            bld  edificios: [alto, x, z, x, z, ...]
  cam   calles y andadores: [ancho, x, z, ...]         ver  canchas, parques y jardines (polígonos)
  arb   árboles del inventario: [placa, x, z, alto, copa, especie]  (especie = índice en arboles.json, -1 si no está)
  obs   observaciones de iNaturalist: [x, z, grupo, nombre, id]
  etq   etiquetas de lugares con nombre dentro del territorio: [x, z, alto, texto]
  ter   (solo el bosque) relieve: {n, x0, z0, paso, y: [alturas en metros sobre el punto más bajo]}

Fuentes (todas abiertas): OpenStreetMap vía Overpass (ODbL: crédito "© colaboradores de OpenStreetMap"); inventario
ArcGIS 2014-2018 de árboles del ITESO; observaciones de Naturalista ITESO en la base de Campus Lab; polígono de los
predios del lugar 185911 de iNaturalist; relieve de los Terrain Tiles de AWS (Mapzen; SRTM y otras fuentes públicas).
Las descargas se guardan en caché junto a la salida: volver a correr no vuelve a pedir nada salvo con --forzar.
"""
import csv
import io
import json
import math
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
SALIDA = REPO / "catalogo" / "salida" / "liferay_subir" / "mapa3d"
CACHE = SALIDA / "cache"
CSV_ARCGIS = REPO / "catalogo" / "salida" / "inventario_arboles" / "arcgis_2014_2018_export.csv"
ARBOLES = REPO / "catalogo" / "salida" / "liferay_subir" / "arboles" / "arboles.json"
BD = REPO / "experimentos" / "bd" / "campuslab_volumen.db"
sys.path.insert(0, str(REPO / "catalogo" / "herramientas" / "rutas_jardines"))
import guia  # noqa: E402  (binomio(): misma normalización de nombres que el resto del proyecto)

OVERPASS = ("https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter")
AGENTE = "CampusLab-ITESO/1.0 (mapa 3D de territorios; campus.lab@iteso.mx)"
ANCHO = {"motorway": 20, "motorway_link": 8, "trunk": 18, "primary": 14, "primary_link": 7, "secondary": 12, "tertiary": 10,
         "residential": 8, "living_street": 6, "unclassified": 7, "service": 5, "busway": 7, "pedestrian": 5,
         "footway": 2.5, "path": 1.8, "track": 3, "steps": 2.5, "cycleway": 2.5}
VERDE = {("leisure", "pitch"), ("leisure", "park"), ("leisure", "garden"), ("leisure", "track"), ("leisure", "recreation_ground"),
         ("landuse", "grass"), ("landuse", "forest"), ("natural", "wood"), ("leisure", "nature_reserve")}
GRUPOS = {"Plantae": "planta", "Aves": "ave", "Insecta": "insecto", "Arachnida": "insecto", "Fungi": "hongo", "Mammalia": "mamifero",
          "Reptilia": "reptil", "Amphibia": "reptil", "Mollusca": "otro", "Actinopterygii": "otro", "Protozoa": "otro"}

TERRITORIOS = [
    {"id": "campus", "nombre": "Campus ITESO", "sub": "Tlaquepaque · árboles del inventario a su altura y copa reales",
     "osm_lim": [294780957, 467379617], "margen": 60, "jardines": "campus"},
    {"id": "clavigero", "nombre": "Casa ITESO Clavigero", "sub": "Guadalajara · la casa y su jardín",
     "centro": (20.67094, -103.36999), "radio": 140, "jardines": "clavigero"},
    {"id": "primavera", "nombre": "Predios en el Bosque La Primavera", "sub": "Zapopan · relieve real y lo observado en Naturalista",
     "inat_lugar": 185911, "margen": 250, "relieve": True},
]


def descargar(url, datos=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=datos, headers={"User-Agent": AGENTE})
            return urllib.request.urlopen(req, timeout=120).read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            print(f"  reintento ({e})"); time.sleep(4 * (i + 1))


def overpass(consulta, nombre, forzar):
    f = CACHE / f"osm_{nombre}.json"
    if f.exists() and not forzar:
        return json.loads(f.read_text(encoding="utf-8"))
    datos = urllib.parse.urlencode({"data": consulta}).encode()
    for url in OVERPASS:
        try:
            r = descargar(url, datos, tries=2)
            if r.lstrip().startswith(b"{"):
                f.write_bytes(r); return json.loads(r)
            print(f"  {url}: ocupado")
        except Exception as e:  # noqa: BLE001
            print(f"  {url}: {e}")
    raise SystemExit("Ningún servidor de Overpass respondió; volver a intentar más tarde.")


class Plano:
    """Proyección equirectangular local: metros al este (x) y al sur (z) desde el centro."""
    def __init__(self, lat0, lon0):
        self.lat0, self.lon0, self.kx = lat0, lon0, math.cos(math.radians(lat0)) * 111320
    def __call__(self, lat, lon):
        return round((lon - self.lon0) * self.kx, 1), round((self.lat0 - lat) * 110574, 1)
    def inverso(self, x, z):
        return self.lat0 - z / 110574, self.lon0 + x / self.kx


def plano_xz(pts):
    return [c for p in pts for c in p]


def dentro(px, pz, ext):
    return ext[0] <= px <= ext[2] and ext[1] <= pz <= ext[3]


def altura_edificio(t):
    if t.get("height"):
        try: return round(float(t["height"].split()[0]), 1)
        except ValueError: pass
    if t.get("building:levels"):
        try: return round(float(t["building:levels"]) * 3.6, 1)
        except ValueError: pass
    return {"chapel": 9.0, "church": 12.0, "house": 6.0, "roof": 4.5, "transportation": 5.0, "garage": 4.0}.get(t.get("building"), 7.5)


def dentro_poli(x, z, poli):
    """Punto en polígono (pares x, z), por cruces de rayo."""
    c = False
    for (x1, z1), (x2, z2) in zip(poli, poli[1:] + poli[:1]):
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            c = not c
    return c


def etiquetas(elementos, P, lims):
    """Lugares con nombre (edificios, jardines, canchas) cuyo centro cae dentro del territorio; sin comercios vecinos."""
    out, vistos = [], set()
    for el in elementos:
        t, g = el.get("tags", {}), el.get("geometry") or []
        n = t.get("name")
        if not n or t.get("highway") or n in vistos or len(g) < 3:
            continue
        pts = [P(q["lat"], q["lon"]) for q in g if q]
        x, z = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        if any(dentro_poli(x, z, l) for l in lims):
            vistos.add(n)
            out.append([round(x, 1), round(z, 1), altura_edificio(t) if t.get("building") else 0, n])
    return out


def capas_osm(elementos, P, ext):
    bld, cam, ver = [], [], []
    for el in elementos:
        t, g = el.get("tags", {}), el.get("geometry") or []
        pts = [P(q["lat"], q["lon"]) for q in g if q]
        if len(pts) < 2 or not any(dentro(x, z, ext) for x, z in pts):
            continue
        if t.get("building"):
            bld.append([altura_edificio(t)] + plano_xz(pts))
        elif t.get("highway") in ANCHO and t.get("area") != "yes":
            cam.append([ANCHO[t["highway"]]] + plano_xz(pts))
        elif any((k, t.get(k)) in VERDE for k in ("leisure", "landuse", "natural")) and len(pts) > 2:
            ver.append(plano_xz(pts))
    return bld, cam, ver


def especies_idx():
    esp = json.loads(ARBOLES.read_text(encoding="utf-8"))["especies"]
    return {e["sci"].lower(): i for i, e in enumerate(esp)}


def arboles(cual, P, ext, idx):
    out = []
    for r in csv.DictReader(open(CSV_ARCGIS, encoding="utf-8-sig")):
        es_clavigero = r["ID_J"] == "0"
        if (cual == "clavigero") != es_clavigero:
            continue
        try:
            lat, lon = float(r["Latitud"]), float(r["Longitud"])
        except ValueError:
            continue
        x, z = P(lat, lon)
        if not dentro(x, z, ext):
            continue  # coordenada mala (0,0 o truncada): queda fuera, igual que en el mapa 2D
        num = lambda v, d: float(v) if v.strip() not in ("", "0") else d  # noqa: E731
        alto = min(num(r["Altura2018"], 6.0), 40.0)
        copa = min(num(r["DiamFoli20"], alto * 0.6), 30.0)
        b = guia.binomio(r["Nom_cien"])
        out.append([int(r["Placa"]), x, z, round(alto, 1), round(copa, 1), idx.get(b.lower(), -1)])
    return out


def observaciones(P, ext):
    con = sqlite3.connect(BD)
    out = []
    for oid, nombre, reino, lat, lng in con.execute("SELECT obs_id, taxon_nombre, reino_iconico, lat, lng FROM inat_observaciones WHERE lat IS NOT NULL"):
        x, z = P(lat, lng)
        if dentro(x, z, ext):
            out.append([x, z, GRUPOS.get(reino, "otro"), nombre or "", oid])
    return out


def predios_inat(lugar, forzar):
    f = CACHE / f"inat_lugar_{lugar}.json"
    if not f.exists() or forzar:
        f.write_bytes(descargar(f"https://api.inaturalist.org/v1/places/{lugar}"))
    g = json.loads(f.read_text(encoding="utf-8"))["results"][0]["geometry_geojson"]
    polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [[(lat, lon) for lon, lat in poli[0]] for poli in polis]


def relieve(P, ext, forzar, n=129, z=15):
    """Malla n×n de alturas muestreada de los Terrain Tiles (codificación terrarium: R·256 + G + B/256 − 32768)."""
    tiles = {}
    def tile(tx, ty):
        if (tx, ty) not in tiles:
            f = CACHE / f"terrarium_{z}_{tx}_{ty}.png"
            if not f.exists() or forzar:
                f.write_bytes(descargar(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png"))
            tiles[(tx, ty)] = Image.open(io.BytesIO(f.read_bytes())).convert("RGB")
        return tiles[(tx, ty)]
    def altura(lat, lon):
        m = 2 ** z
        fx = (lon + 180) / 360 * m * 256
        fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * m * 256
        r, g, b = tile(int(fx // 256), int(fy // 256)).getpixel((int(fx) % 256, int(fy) % 256))
        return r * 256 + g + b / 256 - 32768
    paso = max(ext[2] - ext[0], ext[3] - ext[1]) / (n - 1)
    x0, z0 = (ext[0] + ext[2]) / 2 - paso * (n - 1) / 2, (ext[1] + ext[3]) / 2 - paso * (n - 1) / 2
    ys = [altura(*P.inverso(x0 + i * paso, z0 + j * paso)) for j in range(n) for i in range(n)]
    base = min(ys)
    return {"n": n, "x0": round(x0, 1), "z0": round(z0, 1), "paso": round(paso, 2), "base": round(base),
            "y": [round(y - base, 1) for y in ys]}, base


def construir(forzar=False):
    SALIDA.mkdir(parents=True, exist_ok=True); CACHE.mkdir(parents=True, exist_ok=True)
    idx = especies_idx()
    for T in TERRITORIOS:
        print(f"== {T['nombre']}")
        if T.get("osm_lim"):
            ids = ",".join(map(str, T["osm_lim"]))
            lim_osm = overpass(f"[out:json][timeout:60];way(id:{ids});out geom tags;", f"{T['id']}_limite", forzar)["elements"]
            lims_ll = [[(q["lat"], q["lon"]) for q in el["geometry"]] for el in lim_osm]
        elif T.get("inat_lugar"):
            lims_ll = predios_inat(T["inat_lugar"], forzar)
        else:
            lims_ll = []
        todos = [p for l in lims_ll for p in l] or [T["centro"]]
        lat0 = (min(p[0] for p in todos) + max(p[0] for p in todos)) / 2
        lon0 = (min(p[1] for p in todos) + max(p[1] for p in todos)) / 2
        P = Plano(lat0, lon0)
        if lims_ll:
            xs = [P(*p) for p in todos]; m = T["margen"]
            ext = [min(x for x, _ in xs) - m, min(z for _, z in xs) - m, max(x for x, _ in xs) + m, max(z for _, z in xs) + m]
        else:
            r = T["radio"]; ext = [-r, -r, r, r]
        (s, w), (n_, e) = P.inverso(ext[0], ext[3]), P.inverso(ext[2], ext[1])
        caja = f"({s:.5f},{w:.5f},{n_:.5f},{e:.5f})"
        q = (f'[out:json][timeout:90];(way["building"]{caja};way["highway"]{caja};way["leisure"]{caja};'
             f'way["landuse"~"grass|forest"]{caja};way["natural"="wood"]{caja};);out geom tags;')
        elementos = overpass(q, T["id"], forzar)["elements"]
        bld, cam, ver = capas_osm(elementos, P, ext)
        lims_xz = [[P(*p) for p in l] for l in lims_ll]
        etq = etiquetas(elementos, P, lims_xz) if lims_xz else [[0, 0, 0, T["nombre"]]]
        if T.get("inat_lugar"):
            etq = [[round(sum(p[0] for p in l) / len(l), 1), round(sum(p[1] for p in l) / len(l), 1), 0, "Predio del ITESO"] for l in lims_xz]
        datos = {"id": T["id"], "nombre": T["nombre"], "sub": T["sub"], "origen": [round(lat0, 6), round(lon0, 6)],
                 "ext": [round(v, 1) for v in ext], "lim": [plano_xz(P(*p) for p in l) for l in lims_ll],
                 "bld": bld, "cam": cam, "ver": ver, "etq": etq, "obs": observaciones(P, ext),
                 "creditos": "Mapa: © colaboradores de OpenStreetMap (ODbL). Árboles: inventario del ITESO 2014-2018. "
                             "Observaciones: Naturalista ITESO (iNaturalist)."}
        if T.get("jardines"):
            datos["arb"] = arboles(T["jardines"], P, ext, idx)
        if T.get("relieve"):
            datos["ter"], base = relieve(P, ext, forzar)
            datos["creditos"] += " Relieve: Terrain Tiles de AWS (Mapzen; SRTM y otras fuentes públicas)."
            print(f"   relieve: base {base:.0f} m, desnivel {max(datos['ter']['y']):.0f} m")
        f = SALIDA / f"territorio-{T['id']}.json"
        f.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"   etiquetas: {', '.join(e[3] for e in etq)}")
        print(f"   {len(bld)} edificios, {len(cam)} calles/andadores, {len(ver)} áreas verdes, {len(datos.get('arb', []))} árboles, "
              f"{len(datos['obs'])} observaciones · {round(f.stat().st_size / 1024)} KB · {round(ext[2] - ext[0])} × {round(ext[3] - ext[1])} m")


if __name__ == "__main__":
    construir(forzar="--forzar" in sys.argv)
