"""Arma datos_campo.json para las hojas de campo (corre en Aerilate, donde están los Excel).

Zonas: los 13 jardines del ArcGIS en el orden de recorrido de rutas_jardines, zonas sin inventario
(solo árboles nuevos) y Casa ITESO Clavígero al final. Premarca derribos con ficha del registro de
jardinería y las 8 placas con coordenada mala.

Uso (desde esta carpeta):  python preparar.py   → salida/inventario_arboles/hojas_campo/datos_campo.json
Antes, si cambió el inventario: rutas_jardines/construir.py (orden de recorrido).
"""
import csv
import json
import sys
from pathlib import Path

import openpyxl

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1]))  # catalogo/, para importar comun/
sys.path.insert(0, str(AQUI.parent / "rutas_jardines"))  # guia: especie resuelta y avisos de nombre
from comun.rutas import SALIDA  # noqa: E402
import guia  # noqa: E402

INVENTARIO = SALIDA / "inventario_arboles"
ORDEN = INVENTARIO / "orden_recorrido.json"
MAESTRO = INVENTARIO / "Inventario_Maestro.xlsx"
DESTINO = INVENTARIO / "hojas_campo" / "datos_campo.json"

# Placas con coordenada mala en el ArcGIS (verificado 15-oct): georreferenciar en el recorrido
COORD_MALA = {"1310", "2315", "2403", "362", "1654", "1982", "1983", "89"}
# Zonas sin árboles en el inventario: solo se agregan árboles nuevos (los identifica Juan Gabriel)
ZONAS_NUEVAS = ["Prepa ITESO", "Estacionamiento nuevo", "Predios en el Bosque La Primavera"]
CLAVIGERO = "Casa ITESO Clavígero"


def leer_derribos():
    """Placa -> texto del registro de derribo de jardinería (hoja del Inventario_Maestro)."""
    ws = openpyxl.load_workbook(MAESTRO, read_only=True)["Registro de derribo"]
    filas = ws.iter_rows(values_only=True)
    i = {k: n for n, k in enumerate(next(filas))}
    derr = {}
    for f in filas:
        if not f or f[i["numero_de_ficha"]] in (None, ""):
            continue
        fecha = f[i["fecha"]].date().isoformat() if hasattr(f[i["fecha"]], "date") else str(f[i["fecha"]] or "")
        detalle = ", ".join(str(x).strip() for x in (f[i["especie_segun_jardineria"]], f[i["otro"]]) if x)
        for placa in str(f[i["numero_de_ficha"]]).split("/"):  # "1014/1015" son dos árboles
            derr[placa.strip()] = f"Derribado según jardinería ({fecha}): {detalle}"
    return derr


def leer_clavigero():
    """Casa Clavígero (ID_J 0) no entra en guia.leer_inventario; mismo formato de árbol."""
    arboles = []
    for r in csv.DictReader(open(guia.CSV_ARCGIS, encoding="utf-8-sig")):
        if r["ID_J"] != "0":
            continue
        arboles.append({"placa": r["Placa"], "jardin": CLAVIGERO, "comun_2014": guia.texto_limpio(r["Especie"]),
                        "comun_2018": guia.texto_limpio(r["Nom_comun"]), "especie": guia.binomio(r["Nom_cien"]),
                        "aviso": "", "obs": r["Obs"].strip(), "lat": r["Latitud"], "lon": r["Longitud"]})
    return arboles


def construir():
    orden = json.loads(ORDEN.read_text(encoding="utf-8"))
    por_num = {nombre.split(" - ")[0]: placas for nombre, placas in orden["jardines"].items()}
    derribos = leer_derribos()
    arboles = {}
    for a in guia.leer_inventario() + leer_clavigero():
        previo = derribos.get(a["placa"], "") if a["jardin"] != CLAVIGERO else ""
        if a["placa"] in COORD_MALA:
            previo = (previo + " · " if previo else "") + "Coordenada mala en ArcGIS: georreferenciar"
        try:
            lat, lon = float(a["lat"]), float(a["lon"])
        except ValueError:
            lat = lon = None
        if a["placa"] in COORD_MALA:
            lat = lon = None
        arboles[(a["jardin"], a["placa"])] = {
            "placa": a["placa"], "comun": a["comun_2018"] or a["comun_2014"], "cien": a["especie"],
            "aviso": a["aviso"], "obs": a["obs"], "previo": previo, "lat": lat, "lon": lon}

    zonas = []
    jardines = sorted({j for j, _ in arboles if j != CLAVIGERO}, key=lambda j: int(j.split(" - ")[0]))
    for nombre in jardines:
        num = nombre.split(" - ")[0]
        mias = {p for j, p in arboles if j == nombre}
        en_ruta = [p for p in por_num.get(num, []) if p in mias]
        resto = sorted(mias - set(en_ruta), key=int)
        zonas.append({"id": num, "nombre": nombre, "arboles": [arboles[(nombre, p)] for p in en_ruta + resto]})
    for k, z in enumerate(ZONAS_NUEVAS):
        zonas.append({"id": f"n{k}", "nombre": z, "arboles": []})
    clav = sorted((p for j, p in arboles if j == CLAVIGERO), key=lambda p: int(p) if p.isdigit() else 0)
    zonas.append({"id": "0", "nombre": CLAVIGERO, "arboles": [arboles[(CLAVIGERO, p)] for p in clav]})

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps({"generado": orden["generado"], "jardines": zonas, "edificios": orden["edificios"]},
                                  ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = sum(len(z["arboles"]) for z in zonas)
    print(f"{len(zonas)} zonas, {n} árboles, {sum(1 for a in arboles.values() if a['previo'])} premarcados")
    print(f"Escrito {DESTINO} ({DESTINO.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    construir()
