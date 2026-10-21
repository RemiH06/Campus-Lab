"""
Siembra el inventario de árboles editable: inventario-arboles.csv, una fila por árbol con placa.

Se corre UNA vez para pasar la exportación de ArcGIS (2014-2018, solo lectura, cuenta de Hugo) a un archivo que
cualquiera edita en Excel. Desde ahí, el CSV es la fuente de la verdad: se edita en Excel, se sube como nueva
versión del mismo archivo en Documentos y Medios y los mapas lo leen solos. Volver a correr este script pisa
esas ediciones, por eso no escribe si el archivo ya existe (pasar --forzar para rehacerlo a propósito).

Uso (desde la raíz del repo):  python web/scripts/generar_inventario_csv.py [--forzar]
Salida (gitignorada): catalogo/salida/liferay_subir/arboles/inventario-arboles.csv
Se guarda en UTF-8 con BOM y separado por comas, para que Excel lo abra con acentos con doble clic.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "catalogo" / "herramientas" / "rutas_jardines"))
import guia  # noqa: E402  (misma lectura del inventario, mismas erratas corregidas)

SALIDA = REPO / "catalogo" / "salida" / "liferay_subir" / "arboles" / "inventario-arboles.csv"
COLUMNAS = ["placa", "territorio", "jardin", "nombre_comun", "nombre_cientifico", "latitud", "longitud",
            "altura_m", "copa_m", "diametro_tronco_cm", "anio_plantacion", "salud_2018", "estado", "revisado",
            "fuente", "notas", "aviso"]
# fuera de esta caja la coordenada está mala: (0, 0) o truncada a (20.6, -103.4)
CAJAS = {"campus": (20.600, 20.615, -103.425, -103.408), "clavigero": (20.668, 20.674, -103.373, -103.367)}


def numero(v):
    """'0' y vacío en ArcGIS significan "sin dato", no cero."""
    v = (v or "").strip()
    try:
        return "" if float(v) == 0 else v
    except ValueError:
        return ""


def main(forzar):
    if SALIDA.exists() and not forzar:
        sys.exit(f"{SALIDA} ya existe y puede tener ediciones a mano. Pasa --forzar para rehacerlo desde ArcGIS.")
    filas = list(csv.DictReader(open(guia.CSV_ARCGIS, encoding="utf-8-sig")))
    # nombre común → binomio dominante, para las filas sin nombre científico (todas las de Clavigero)
    comun_a_bi = defaultdict(Counter)
    for r in filas:
        b = guia.binomio(r["Nom_cien"])
        if b:
            comun_a_bi[guia.norm(r["Especie"])][b] += 1
    dominante = {c: n.most_common(1)[0][0] for c, n in comun_a_bi.items() if n.most_common(1)[0][1] / sum(n.values()) >= 0.8}
    campus = {a["placa"]: a for a in guia.leer_inventario()}  # especie y aviso ya resueltos para el campus

    out, malas = [], 0
    for r in filas:
        territorio = "clavigero" if r["ID_J"] == "0" else "campus"
        a = campus.get(r["Placa"], {})
        especie = a.get("especie") or guia.binomio(r["Nom_cien"])
        aviso = a.get("aviso", "")
        if not especie and dominante.get(guia.norm(r["Especie"])):
            especie = dominante[guia.norm(r["Especie"])]
            aviso = f"Nombre científico deducido de «{guia.texto_limpio(r['Especie'])}» (ArcGIS no lo traía): confirmar"
        lat, lon, notas = r["Latitud"].strip(), r["Longitud"].strip(), []
        try:
            la, lo = float(lat), float(lon)
            y0, y1, x0, x1 = CAJAS[territorio]
            if not (y0 <= la <= y1 and x0 <= lo <= x1):
                raise ValueError
        except ValueError:
            lat = lon = ""; malas += 1
            notas.append("Sin coordenada válida en ArcGIS: tomarla en el recorrido")
        if r["Obs"].strip():
            notas.append(r["Obs"].strip())
        out.append({
            "placa": r["Placa"].strip(), "territorio": territorio,
            "jardin": "Casa ITESO Clavigero" if territorio == "clavigero" else guia.jardin_limpio(r["Jardín"]),
            "nombre_comun": guia.texto_limpio(r["Nom_comun"]) or guia.texto_limpio(r["Especie"]),
            "nombre_cientifico": especie, "latitud": lat, "longitud": lon,
            "altura_m": numero(r["Altura2018"]), "copa_m": numero(r["DiamFoli20"]), "diametro_tronco_cm": numero(r["DmFuste201"]),
            "anio_plantacion": numero(r["Año_plant"]), "salud_2018": numero(r["Estado2018"]),
            "estado": "", "revisado": "", "fuente": "ArcGIS 2014-2018",
            "notas": " · ".join(notas), "aviso": aviso,
        })
    out.sort(key=lambda f: int(f["placa"]))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, COLUMNAS)
        w.writeheader()
        w.writerows(out)
    sin_especie = sum(1 for f in out if not f["nombre_cientifico"])
    print(f"{SALIDA}\n  {len(out)} árboles ({sum(f['territorio'] == 'clavigero' for f in out)} en Clavigero), "
          f"{malas} sin coordenada válida, {sin_especie} sin nombre científico, "
          f"{sum(1 for f in out if f['aviso'])} con aviso de nombre")


if __name__ == "__main__":
    main("--forzar" in sys.argv)
