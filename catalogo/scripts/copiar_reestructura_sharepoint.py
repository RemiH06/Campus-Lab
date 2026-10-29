# -*- coding: utf-8 -*-
"""Arma la estructura nueva de los documentos de SharePoint (ProyectoBLP) en una carpeta local,
copiando según salida/Plan_Reestructura_Documentos_SharePoint.xlsx.

Solo lee de los orígenes; nunca mueve ni borra nada en ellos. El destino tiene que estar fuera
de OneDrive (la carpeta sincronizada es de doble vía con SharePoint real).

Orígenes, según la columna "Origen (local, relativo)":
  - "NUEVO: <ruta>"   → archivo generado en este repo (relativo a la raíz), p. ej. la lista de fuentes
  - "VOLUMEN: <ruta>" → volumen de fotos, Y:\\<ruta> (solo dentro de la red de ITESO)
  - cualquier otra    → biblioteca sincronizada de SharePoint (config: ruta_sharepoint_sincronizado)

Se copian las filas con "Accion v2" MOVER o COPIAR, a la columna "Destino vN" más nueva (v3 del 29-oct: 01-11,
Actividades con Avistamientos, Comunicación y Difusión, Referencias Interno/Externo). Las anteriores quedan de historial.

Resumible: cada copia se escribe como .tmp, se verifica por SHA-1 contra el origen, se renombra y
se anota en _manifiesto.csv del destino. Al volver a correr, lo que ya está en el manifiesto y en
disco se salta; se puede cortar a la mitad sin perder ni duplicar.

Uso: python copiar_reestructura_sharepoint.py   (plan en seco: salida/Plan_Copia_Reestructura.xlsx)
     cambiar EJECUTAR_REAL a True después de revisar el plan, y volver a correr.
"""
import csv
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

EJECUTAR_REAL = False

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.bd import red_iteso_disponible  # noqa: E402
from comun.rutas import RAIZ, SALIDA, cargar_config  # noqa: E402

PLAN = SALIDA / "Plan_Reestructura_Documentos_SharePoint.xlsx"
PLAN_SECO = SALIDA / "Plan_Copia_Reestructura.xlsx"
VOLUMEN = Path("Y:/")
COLUMNAS_MANIFIESTO = ["destino", "origen", "bytes", "sha1", "copiado"]


def sha1(p: Path) -> str:
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def resolver_origen(origen: str, sincronizado: Path) -> Path:
    if origen.startswith("NUEVO: "):
        return RAIZ / origen.removeprefix("NUEVO: ")
    if origen.startswith("VOLUMEN: "):
        return VOLUMEN / origen.removeprefix("VOLUMEN: ")
    return sincronizado / origen


def leer_manifiesto(ruta: Path) -> dict[str, dict]:
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8", newline="") as f:
        return {fila["destino"]: fila for fila in csv.DictReader(f)}


def main():
    cfg = cargar_config(obligatorio=True)
    sincronizado = Path(cfg["ruta_sharepoint_sincronizado"])
    destino_raiz = Path(cfg["ruta_destino_reestructura"])
    if "onedrive" in str(destino_raiz).lower() or destino_raiz.resolve().is_relative_to(sincronizado.resolve()):
        raise SystemExit(f"El destino {destino_raiz} no puede estar dentro de OneDrive ni de la carpeta sincronizada.")

    plan = pd.read_excel(PLAN)
    col_origen = plan.columns[0]
    # la versión más nueva de la estructura: "Destino v3" gana a "Destino v2"
    col_destino = max((c for c in plan.columns if re.fullmatch(r"Destino v\d+", c)), key=lambda c: int(c[9:]))
    copiar = plan[plan["Accion v2"].isin(["MOVER", "COPIAR"])]
    if copiar[col_destino].isna().any():
        raise SystemExit(f"Hay filas a copiar sin '{col_destino}'.")
    repetidos = copiar[col_destino][copiar[col_destino].str.casefold().duplicated()]  # Windows no distingue mayúsculas
    if len(repetidos):
        raise SystemExit(f"{len(repetidos)} destinos repetidos (se pisarían): {list(repetidos)[:5]}")

    hay_volumen = None
    manifiesto_ruta = destino_raiz / "_manifiesto.csv"
    manifiesto = leer_manifiesto(manifiesto_ruta)
    filas = []
    for origen_txt, destino_rel in zip(copiar[col_origen], copiar[col_destino]):
        if origen_txt.startswith("VOLUMEN: ") and hay_volumen is None:
            hay_volumen = red_iteso_disponible()
        if origen_txt.startswith("VOLUMEN: ") and not hay_volumen:
            estado, tam, origen = "sin red de ITESO", None, None
        else:
            origen = resolver_origen(origen_txt, sincronizado)
            # .exists()/.stat() no bajan el archivo de OneDrive; solo leerlo lo baja
            if not origen.exists():
                estado, tam = "NO EXISTE EL ORIGEN", None
            else:
                tam = origen.stat().st_size
                hecho = manifiesto.get(destino_rel)
                ya = hecho and (destino_raiz / destino_rel).exists() and int(hecho["bytes"]) == tam
                estado = "ya copiado" if ya else "por copiar"
        filas.append({"origen": origen_txt, "destino": destino_rel, "bytes": tam, "estado": estado, "_origen": origen})

    df = pd.DataFrame(filas)
    resumen = df.groupby("estado").agg(archivos=("destino", "size"), GB=("bytes", lambda b: round(b.sum() / 1e9, 2)))
    print(resumen.to_string())
    df.drop(columns="_origen").to_excel(PLAN_SECO, index=False)
    print(f"Plan en seco: {PLAN_SECO}")
    libre = shutil.disk_usage(destino_raiz.anchor).free
    falta = df.loc[df.estado == "por copiar", "bytes"].sum()
    print(f"Por copiar {falta / 1e9:.1f} GB; libres en {destino_raiz.anchor} {libre / 1e9:.0f} GB")

    if not EJECUTAR_REAL:
        print("EJECUTAR_REAL = False: no se copió nada.")
        return
    if falta > libre * 0.9:
        raise SystemExit("No hay espacio suficiente en el disco de destino.")

    destino_raiz.mkdir(parents=True, exist_ok=True)
    nuevo = not manifiesto_ruta.exists()
    with open(manifiesto_ruta, "a", encoding="utf-8", newline="") as fm:
        w = csv.DictWriter(fm, fieldnames=COLUMNAS_MANIFIESTO)
        if nuevo:
            w.writeheader()
        pendientes = df[df.estado == "por copiar"]
        for n, (origen_txt, destino_rel, origen) in enumerate(zip(pendientes.origen, pendientes.destino, pendientes._origen), 1):
            destino = destino_raiz / destino_rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            tmp = destino.with_name(destino.name + ".tmp")
            shutil.copy2(origen, tmp)
            h_origen, h_copia = sha1(origen), sha1(tmp)
            if h_origen != h_copia:
                tmp.unlink()
                print(f"  ERROR de verificación, se reintentará en la siguiente corrida: {destino_rel}")
                continue
            os.replace(tmp, destino)
            w.writerow({"destino": destino_rel, "origen": origen_txt, "bytes": destino.stat().st_size,
                        "sha1": h_copia, "copiado": datetime.now().isoformat(timespec="seconds")})
            fm.flush()  # una fila por archivo: si se corta, lo copiado queda registrado
            if n % 50 == 0 or n == len(pendientes):
                print(f"  {n}/{len(pendientes)}")
    print(f"Listo. Manifiesto: {manifiesto_ruta}")


if __name__ == "__main__":
    main()
