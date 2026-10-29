# -*- coding: utf-8 -*-
"""F2 de la reestructura en el SharePoint oficial: aplica salida/Plan_Aplicacion_SharePoint.xlsx (lo arma la F1,
plan_aplicacion_sharepoint.py) DENTRO de la carpeta sincronizada, así OneDrive hace los cambios en SharePoint.

Excepción autorizada por Remi (29-oct) a la regla "nunca mover en la carpeta sincronizada", solo para esta
reestructura: mover ahí conserva el historial de versiones de cada archivo (subir copias lo perdería).

Qué hace con cada acción del plan:
  CREAR CARPETA  crea la carpeta (vacía)
  MOVER          renombra el archivo a su ruta nueva (OneDrive lo mueve en el servidor; no lo baja)
  SUBIR          copia el archivo desde el repo ("NUEVO: …") o desde la copia local de la estructura nueva
  BORRAR         borra basura del sistema (desktop.ini, .lock); va a la papelera de SharePoint (93 días)
  POR BORRAR, IMAGEN F3  no se tocan: siguen en las carpetas sin número hasta la F3
Si queda alguna fila REVISAR, no corre.

Uso:
  python aplicar_reestructura_sharepoint.py --paso0     acorta las carpetas del libro con rutas de más de 260
                                                         (luego volver a correr la F1)
  python aplicar_reestructura_sharepoint.py [--tanda "02."]   plan en seco de todo, o solo de los destinos que
                                                         empiezan con ese texto
  Cambiar EJECUTAR_REAL a True después de revisar el plan en seco. Resumible: lo hecho se salta.
  Cada operación queda en salida/Log_Aplicacion_SharePoint.csv.
"""
import csv
import os
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

EJECUTAR_REAL = False

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.rutas import RAIZ, SALIDA, cargar_config  # noqa: E402
from plan_aplicacion_sharepoint import ALIAS_PASO0, LIBRO_NUEVO  # noqa: E402

PLAN = SALIDA / "Plan_Aplicacion_SharePoint.xlsx"
LOG = SALIDA / "Log_Aplicacion_SharePoint.csv"
ORDEN = ["CREAR CARPETA", "MOVER", "SUBIR", "BORRAR"]


def larga(p):
    """Prefijo \\\\?\\ para que Windows acepte rutas de 260 caracteres o más."""
    s = os.path.abspath(p)
    return s if os.name != "nt" or s.startswith("\\\\?\\") else "\\\\?\\" + s


def existe(p):
    return os.path.lexists(larga(p))


def onedrive_corriendo():
    if os.name != "nt":
        return True
    salida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq OneDrive.exe"], capture_output=True, text=True).stdout
    return "OneDrive.exe" in salida


def registrar(fila):
    nuevo = not LOG.exists()
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "accion", "origen", "destino", "resultado"])
        if nuevo:
            w.writeheader()
        w.writerow({"fecha": datetime.now().isoformat(timespec="seconds"), **fila})


def paso0(sp):
    """Acorta dos carpetas del libro de octubre (ALIAS_PASO0). Es un cambio de nombre de carpeta: no baja nada."""
    base = sp / LIBRO_NUEVO
    cambios = [(base / "Libro aves Capítulos", base / "LC"),
               (base / "LC" / "6. Guía para observar las aves", base / "LC" / "G6")]
    assert [c for c, _ in ALIAS_PASO0] == ["LC", "G6"]
    for viejo, nuevo in cambios:
        if existe(nuevo) and not existe(viejo):
            print(f"  ya hecho: {nuevo.relative_to(sp)}")
            continue
        print(f"  {viejo.relative_to(sp)}  ->  {nuevo.name}")
        if EJECUTAR_REAL:
            os.rename(larga(viejo), larga(nuevo))
            registrar({"accion": "PASO 0", "origen": str(viejo.relative_to(sp)), "destino": str(nuevo.relative_to(sp)),
                       "resultado": "hecho"})
    if not EJECUTAR_REAL:
        print("EJECUTAR_REAL = False: no se cambió nada.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = cargar_config(obligatorio=True)
    sp = Path(cfg["ruta_sharepoint_sincronizado"])
    local = Path(cfg["ruta_destino_reestructura"])
    if not onedrive_corriendo():
        raise SystemExit("OneDrive.exe no está corriendo: sin él los archivos que solo están en la nube no se mueven bien.")
    if "--paso0" in sys.argv:
        return paso0(sp)
    tanda = sys.argv[sys.argv.index("--tanda") + 1] if "--tanda" in sys.argv else ""

    df = pd.read_excel(PLAN, sheet_name="Acciones").fillna("")
    if (df.accion == "REVISAR").any():
        raise SystemExit(f"Quedan {int((df.accion == 'REVISAR').sum())} filas REVISAR: resolverlas y volver a correr la F1.")
    ops = df[df.accion.isin(ORDEN) & df.destino.map(lambda d: unicodedata.normalize("NFC", d)).str.startswith(
        unicodedata.normalize("NFC", tanda))] if tanda else df[df.accion.isin(ORDEN)]
    if tanda:  # la basura no tiene destino: va con la tanda de todo
        ops = ops[ops.accion != "BORRAR"]
    ops = ops.assign(_o=ops.accion.map(ORDEN.index)).sort_values(["_o", "destino"])

    plan_seco, conteo = [], {}
    for f in ops.itertuples():
        # ruta_disco = el nombre como está en disco (con acentos NFC o NFD); ruta_actual va normalizada
        origen = sp / f.ruta_disco if f.ruta_disco else None
        destino = sp / f.destino if f.destino else None
        if f.accion == "SUBIR":
            origen = RAIZ / f.ruta_actual.removeprefix("NUEVO: ") if f.ruta_actual.startswith("NUEVO: ") else local / f.destino
        if f.accion == "CREAR CARPETA":
            estado = "ya hecho" if existe(destino) else "pendiente"
        elif f.accion == "BORRAR":
            estado = "pendiente" if existe(origen) else "ya hecho"
        elif f.accion == "SUBIR":
            if not existe(origen):
                estado = "ERROR: no existe el archivo a subir"
            elif existe(destino) and os.stat(larga(destino)).st_size == os.stat(larga(origen)).st_size:
                estado = "ya hecho"
            elif existe(destino):
                estado = "ERROR: ya hay otro archivo en el destino"
            else:
                estado = "pendiente"
        else:  # MOVER
            o, d = existe(origen), existe(destino)
            estado = ("pendiente" if o and not d else "ya hecho" if d and not o else
                      "ERROR: el origen ya no existe" if not o else "ERROR: origen y destino existen")
        conteo[(f.accion, estado)] = conteo.get((f.accion, estado), 0) + 1
        plan_seco.append((f.accion, origen, destino, estado))

    for (a, e), n in sorted(conteo.items()):
        print(f"  {a:14} {e:40} {n}")
    errores = [p for p in plan_seco if p[3].startswith("ERROR")]
    for a, o, d, e in errores[:20]:
        print(f"  {e}: {o} -> {d}")
    if not EJECUTAR_REAL:
        print("EJECUTAR_REAL = False: no se cambió nada.")
        return
    if errores:
        raise SystemExit("Hay errores en el plan en seco: no se aplica nada.")

    hechos = 0
    for accion, origen, destino, estado in plan_seco:
        if estado != "pendiente":
            continue
        rel_o = str(origen.relative_to(sp)) if origen and origen.is_relative_to(sp) else str(origen or "")
        rel_d = str(destino.relative_to(sp)) if destino else ""
        try:
            if accion == "CREAR CARPETA":
                os.makedirs(larga(destino), exist_ok=True)
            elif accion == "MOVER":
                os.makedirs(larga(destino.parent), exist_ok=True)
                os.rename(larga(origen), larga(destino))
            elif accion == "SUBIR":
                os.makedirs(larga(destino.parent), exist_ok=True)
                shutil.copy2(larga(origen), larga(destino))
            elif accion == "BORRAR":
                os.remove(larga(origen))
            registrar({"accion": accion, "origen": rel_o, "destino": rel_d, "resultado": "hecho"})
        except OSError as e:
            registrar({"accion": accion, "origen": rel_o, "destino": rel_d, "resultado": f"ERROR {e}"})
            print(f"  ERROR ({e}) en {rel_o or rel_d}; se sigue con lo demás, volver a correr para reintentar")
        hechos += 1
        if hechos % 100 == 0:
            print(f"  {hechos} operaciones")
            time.sleep(2)  # da aire a OneDrive para subir los cambios
    print(f"Listo: {hechos} operaciones. Log: {LOG}")


if __name__ == "__main__":
    main()
