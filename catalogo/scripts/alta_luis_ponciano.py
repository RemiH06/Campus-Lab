# -*- coding: utf-8 -*-
"""Paso 2 de las fotos de Luis Ponciano: autor y original para las que ya están en el volumen, alta de las nuevas.

Entrada: tabla fotos_luis_ponciano (fotos_luis_ponciano.py). El paso 1 encontró que casi todas ya estaban en el
volumen como copias más ligeras sin autor (ESPECIE\\ÁRBOLES y ESPECIE\\ARBOLES_TODAS, a veces las dos).

Una foto del volumen es de Luis si su EXIF trae el MISMO segundo de toma que una de sus originales y el dHash queda
a <= UMBRAL_HASH bits (el mismo segundo solo no basta: puede ser ráfaga). Si la copia del volumen perdió el EXIF,
basta dHash 0 contra la original. Lo demás que se parece pero no cumple va a REVISAR. El EXIF del volumen se lee
del espejo local (config: ruta_espejo_local_fotos) y se guarda en salida/luis_ponciano/exif_volumen.json (resumible).

Acciones del plan:
  AUTOR     fotos.autor_id = Luis Ponciano si estaba vacío (nunca pisa otro autor) + fila en fotos_originales
  ALTA      foto nueva en fotos (origen onedrive_luis_ponciano, estado pendiente, ruta_actual ONEDRIVE_LP\\<nombre
            con la convención>) + fotos_originales; la miniatura se copia al espejo con ese nombre para que las
            herramientas de revisión la abran (resolver_ruta_legible). El original no se copia a ningún lado.
  REVISAR   no se toca
  NO ALTA   fotos de personas en la raíz de la carpeta
fotos_originales (foto_id → ruta relativa a la carpeta de OneDrive) es de donde se lee el original al subir a Liferay.
No cambia especies: la columna "Carpeta del volumen" deja ver dónde la carpeta de Luis y la del volumen no coinciden.

Uso: python alta_luis_ponciano.py   (plan en seco: salida/luis_ponciano/Plan_Alta_Luis_Ponciano.xlsx)
     cambiar EJECUTAR_REAL a True después de revisar el plan, y volver a correr (resumible, no duplica).
"""
import hashlib
import json
import shutil
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image

EJECUTAR_REAL = False

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.rutas import RUTA_BD, SALIDA, cargar_config  # noqa: E402
from cruce_fotos_inat import dhash, distancias_hash  # noqa: E402
from fotos_luis_ponciano import MINIATURAS, leer_exif  # noqa: E402

CARPETA = SALIDA / "luis_ponciano"
CACHE_EXIF = CARPETA / "exif_volumen.json"
PLAN = CARPETA / "Plan_Alta_Luis_Ponciano.xlsx"
UMBRAL_HASH = 3
AUTOR = "Luis Ponciano"
FUENTE = "onedrive_luis_ponciano"
PREFIJO = "ONEDRIVE_LP"
# REVISAR que resultaron ser la misma foto al verlas lado a lado: 3326 copia del volumen cortada a la mitad,
# 4005 idéntica (dHash 6, mismo segundo), 4776 recorte para el concurso 2023 con la fecha cambiada
CONFIRMADAS_A_OJO = {3326, 4005, 4776}


def exif_volumen(c, espejo: Path):
    """Fecha de toma y dHash de las fotos del volumen que pueden ser de Luis, leídas del espejo local."""
    cache = {int(k): v for k, v in json.loads(CACHE_EXIF.read_text(encoding="utf-8")).items()} if CACHE_EXIF.exists() else {}
    filas = c.execute(r"""SELECT id, ruta_actual FROM fotos
        WHERE ruta_original LIKE '%\ESPECIE\ÁRBOLES\%' OR ruta_original LIKE '%\ESPECIE\ARBOLES_TODAS\%'
           OR id IN (SELECT parecida_a_foto_id FROM fotos_luis_ponciano)""").fetchall()
    for n, (i, ruta) in enumerate((f for f in filas if f[0] not in cache), 1):
        p = espejo / Path(ruta).name
        try:
            with Image.open(p) as img:
                e = leer_exif(img)
                img.draft("RGB", (600, 600))
                cache[i] = {"fecha": e["fecha_tomada"], "camara": e["camara"], "dhash": str(dhash(img))}
        except Exception as ex:
            cache[i] = {"error": f"{type(ex).__name__}: {ex}"}
        if n % 100 == 0:
            CACHE_EXIF.write_text(json.dumps(cache), encoding="utf-8")
    CACHE_EXIF.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def nombre_convencion(ruta_original):
    """{RAMA}-{autor}-{especie}-{hash6}, como las del volumen; la especie se pone al confirmarla."""
    return f"ESPECIE-{AUTOR.replace(' ', '')}-SINESP-{hashlib.sha1(ruta_original.encode()).hexdigest()[:6]}.jpg"


def armar_plan(c, vol):
    luis = pd.read_sql("""SELECT ruta_relativa, carpeta, entrega, bytes, fecha_tomada, dhash, miniatura,
                          parecida_a_foto_id, dist_dhash FROM fotos_luis_ponciano
                          WHERE duplicado_de IS NULL AND error IS NULL""", c)
    por_fecha = defaultdict(list)
    for _, r in luis.iterrows():
        por_fecha[r.fecha_tomada].append(r)
    parecida = {int(r.parecida_a_foto_id): r for _, r in luis.iterrows() if pd.notna(r.parecida_a_foto_id)}
    por_nombre = defaultdict(list)
    for _, r in luis.iterrows():
        por_nombre[r.ruta_relativa.rsplit("/", 1)[-1].lower()].append(r)
    info = {r[0]: r[1:] for r in c.execute("""SELECT f.id, f.ruta_original, f.autor_id, a.nombre, e.nombre_cientifico, f.estado
                                              FROM fotos f LEFT JOIN autores a ON a.id = f.autor_id
                                              LEFT JOIN especies e ON e.id = f.especie_id""")}
    plan, ligadas, en_revision = [], set(), set()
    for foto_id, x in sorted(vol.items()):
        ruta_vol, autor_id, autor, especie, estado = info[foto_id]
        fila = {"foto_id": foto_id, "Ruta en el volumen": ruta_vol, "Carpeta del volumen": ruta_vol.split("\\")[-2],
                "Especie en la BD": especie, "Estado": estado, "Autor actual": autor}
        original, probable, motivo = None, None, None  # probable: original que alguien tiene que confirmar
        if "error" in x:
            mismos = por_nombre.get(ruta_vol.rsplit("\\", 1)[-1].lower(), [])
            probable = mismos[0] if len(mismos) == 1 else None
            motivo = f"no se pudo leer la copia del volumen ({x['error']})" + (
                "; mismo nombre de archivo que la original: si es la misma, la original sustituye a la copia dañada"
                if probable is not None else "")
        else:
            cands = por_fecha.get(x["fecha"], []) if x["fecha"] else []
            if cands:
                dist = distancias_hash([int(x["dhash"])], [int(r.dhash) for r in cands])[0]
                j = int(dist.argmin())
                if dist[j] <= UMBRAL_HASH:
                    original, motivo = cands[j], f"mismo segundo de toma, dHash {int(dist[j])}"
                else:
                    probable = cands[j]
                    motivo = f"mismo segundo de toma pero dHash {int(dist[j])}: ¿editada u otra foto de la ráfaga?"
            elif foto_id in parecida:
                r = parecida[foto_id]
                if not x["fecha"] and r.dist_dhash == 0:
                    original, motivo = r, "la copia perdió el EXIF; dHash 0"
                else:
                    probable = r
                    motivo = f"dHash {int(r.dist_dhash)} pero la fecha no coincide ({x['fecha']} contra {r.fecha_tomada})"
            else:
                motivo = "en las carpetas de árboles pero sin original de Luis con la misma fecha"
        if original is None and probable is not None and foto_id in CONFIRMADAS_A_OJO:
            original, motivo = probable, f"{motivo}; confirmada a ojo (28-oct)"
        if original is not None:
            ligadas.add(original.ruta_relativa)
            accion = "AUTOR" if autor_id is None else ("YA ES DE LUIS" if autor == AUTOR else "REVISAR")
            if accion == "REVISAR":
                motivo += f"; ya tiene otro autor ({autor})"
            plan.append({"Accion": accion, **fila, "Original (OneDrive)": original.ruta_relativa,
                         "Carpeta de Luis": original.carpeta, "Criterio": motivo})
        elif foto_id in parecida or "error" in x or x.get("fecha") in por_fecha or "ÁRBOLES" in ruta_vol.upper():
            if probable is not None:
                en_revision.add(probable.ruta_relativa)
            plan.append({"Accion": "REVISAR", **fila,
                         "Original (OneDrive)": None if probable is None else probable.ruta_relativa,
                         "Carpeta de Luis": None if probable is None else probable.carpeta, "Criterio": motivo})
    for _, r in luis.iterrows():
        if r.ruta_relativa in ligadas:
            continue
        if r.ruta_relativa in en_revision:
            accion, motivo = "REVISAR", "posible original de una foto del volumen que está en REVISAR (ver la fila con foto_id)"
        elif pd.isna(r.carpeta):
            accion, motivo = "NO ALTA", "en la raíz de la carpeta, sin especie (retrato)"
        else:
            accion, motivo = "ALTA", "sin copia en el volumen"
        plan.append({"Accion": accion, "foto_id": None, "Original (OneDrive)": r.ruta_relativa,
                     "Carpeta de Luis": r.carpeta, "Criterio": motivo,
                     "Nombre nuevo": nombre_convencion(f"{PREFIJO}/{r.ruta_relativa}") if accion == "ALTA" else None})
    return pd.DataFrame(plan), luis.set_index("ruta_relativa")


def ejecutar(c, plan, luis, espejo: Path):
    c.execute("""CREATE TABLE IF NOT EXISTS fotos_originales (foto_id INTEGER PRIMARY KEY REFERENCES fotos(id),
                 fuente TEXT NOT NULL, ruta_relativa TEXT NOT NULL, criterio TEXT)""")
    autor_id = c.execute("SELECT id FROM autores WHERE nombre = ?", (AUTOR,)).fetchone()[0]
    for _, p in plan[plan.Accion.isin(["AUTOR", "YA ES DE LUIS"])].iterrows():
        c.execute("UPDATE fotos SET autor_id = ? WHERE id = ? AND autor_id IS NULL", (autor_id, int(p.foto_id)))
        c.execute("INSERT OR IGNORE INTO fotos_originales VALUES (?, ?, ?, ?)",
                  (int(p.foto_id), FUENTE, p["Original (OneDrive)"], p.Criterio))
        c.commit()
    for _, p in plan[plan.Accion == "ALTA"].iterrows():
        r = luis.loc[p["Original (OneDrive)"]]
        ruta_actual = f"{PREFIJO}\\{p['Nombre nuevo']}"
        destino = espejo / p["Nombre nuevo"]
        if not destino.exists():
            shutil.copy2(MINIATURAS / r.miniatura, destino)
        c.execute("""INSERT OR IGNORE INTO fotos (ruta_actual, ruta_original, autor_id, tomada_en_iteso, estado,
                     tamano_bytes, origen) VALUES (?, ?, ?, 1, 'pendiente', ?, ?)""",
                  (ruta_actual, f"{PREFIJO}/{p['Original (OneDrive)']}", autor_id, int(r.bytes), FUENTE))
        foto_id = c.execute("SELECT id FROM fotos WHERE ruta_actual = ?", (ruta_actual,)).fetchone()[0]
        c.execute("INSERT OR IGNORE INTO fotos_originales VALUES (?, ?, ?, ?)",
                  (foto_id, FUENTE, p["Original (OneDrive)"], "alta desde OneDrive"))
        c.commit()


def main():
    espejo = Path(cargar_config(obligatorio=True)["ruta_espejo_local_fotos"])
    c = sqlite3.connect(RUTA_BD)
    plan, luis = armar_plan(c, exif_volumen(c, espejo))
    orden = {"REVISAR": 0, "ALTA": 1, "NO ALTA": 2, "AUTOR": 3, "YA ES DE LUIS": 4}
    plan = plan.sort_values(["Accion", "Carpeta de Luis"], key=lambda s: s.map(orden) if s.name == "Accion" else s)
    plan.to_excel(PLAN, index=False)
    print(plan.Accion.value_counts().to_string())
    print(f"Plan: {PLAN}")
    if not EJECUTAR_REAL:
        print("En seco. Revisar el plan y cambiar EJECUTAR_REAL a True.")
        return
    ejecutar(c, plan, luis, espejo)
    print("Hecho:", c.execute("SELECT COUNT(*) FROM fotos_originales WHERE fuente = ?", (FUENTE,)).fetchone()[0],
          "fotos con original en OneDrive")


if __name__ == "__main__":
    main()
