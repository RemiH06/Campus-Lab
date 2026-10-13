"""
Etiquetado a mano de la parte del árbol que muestra cada foto (árbol completo, tronco,
hoja, flor, fruto u otro), por especie y por grupo de espécimen. Sirve para saber qué
partes ya tiene cada especie de árbol (pedido de Maya: árbol completo, tronco, hoja,
fruto y flor según aplique) y cuáles faltan por fotografiar.

No preclasifica con BioCLIP: se probó (8-oct) y acertó ~5 de 15.

Especie de árbol = nombre científico en una ficha de árbol del sitio (fichas.json) o en
Lista_Arboles_ITESO.csv, comparado por binomio normalizado. Solo fotos confirmadas.

Escribe solo en la tabla `partes_arbol_etiquetas` (una fila por foto, commit por fila).

Uso: python backend.py, luego abrir http://localhost:8047
"""

import concurrent.futures
import csv
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel

RUTA_BD = Path(__file__).parent / "../../../experimentos/bd/campuslab_volumen.db"
RUTA_CONFIG = Path(__file__).parent / "../../notebooks/config_local.json"
RUTA_LISTA_ARBOLES = Path(__file__).parent / "../../notebooks/Lista_Arboles_ITESO.csv"
RUTA_FICHAS = Path(__file__).parent / "../../salida/sitio_campuslab/fichas.json"

PARTES = ["arbol_completo", "tronco", "hoja", "flor", "fruto", "otro"]

app = FastAPI()


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


# Una sola vez al arrancar, nunca por request (ver "database is locked" en CLAUDE.md)
_c_inicial = con()
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS partes_arbol_etiquetas (
    foto_id INTEGER PRIMARY KEY, parte TEXT NOT NULL, revisor TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.commit()
_c_inicial.close()


def cargar_config():
    return json.loads(RUTA_CONFIG.read_text(encoding="utf-8")) if RUTA_CONFIG.exists() else {}


def binomio(nombre):
    plano = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    palabras = re.findall(r"[a-z]+", plano.lower().replace("×", "x"))
    return " ".join(palabras[:2]) if len(palabras) >= 2 else ""


def nombres_de_arboles():
    """binomio -> nombre común, de la lista oficial y de las fichas de árbol del sitio."""
    nombres = {}
    if RUTA_FICHAS.exists():
        for ficha in json.loads(RUTA_FICHAS.read_text(encoding="utf-8")).values():
            if ficha.get("tipo") == "arbol":
                campos = ficha.get("campos", {})
                nombres[binomio(campos.get("nombre_cientifico"))] = campos.get("nombre_comun")
    with open(RUTA_LISTA_ARBOLES, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            nombres.setdefault(binomio(fila["nombre_cientifico"]), fila["nombre_comun"])
    nombres.pop("", None)
    return nombres


NOMBRES_ARBOLES = nombres_de_arboles()

_ITESO_DISPONIBLE = None


def red_iteso_disponible():
    global _ITESO_DISPONIBLE
    if _ITESO_DISPONIBLE is None:
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        futuro = ex.submit(lambda: Path("Y:/").exists())
        try:
            _ITESO_DISPONIBLE = futuro.result(timeout=2)
        except concurrent.futures.TimeoutError:
            _ITESO_DISPONIBLE = False
        ex.shutdown(wait=False)  # nunca "with", su __exit__ esperaria al hilo colgado
    return _ITESO_DISPONIBLE


def resolver_ruta_legible(ruta_actual):
    ruta_espejo = cargar_config().get("ruta_espejo_local_fotos")
    if ruta_espejo:
        local = Path(ruta_espejo) / Path(ruta_actual).name
        if local.exists():
            return local
    if not red_iteso_disponible():
        return None
    ruta_directa = Path(ruta_actual)
    return ruta_directa if ruta_directa.exists() else None


def fotos_de_arboles(c, especie_id=None):
    filas = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, e.id AS especie_id, e.nombre_cientifico,
               e.nombre_comun, g.grupo_id, p.parte
        FROM fotos f
        JOIN especies e ON e.id = f.especie_id
        LEFT JOIN especimen_grupos_confirmados g ON g.foto_id = f.id
        LEFT JOIN partes_arbol_etiquetas p ON p.foto_id = f.id
        WHERE f.estado = 'usable'
          AND f.id NOT IN (SELECT foto_id FROM archivos_no_procesables)
          AND (? IS NULL OR e.id = ?)
        ORDER BY f.id
    """, (especie_id, especie_id)).fetchall()
    return [f for f in filas if binomio(f["nombre_cientifico"]) in NOMBRES_ARBOLES]


@app.get("/api/especies")
def api_especies():
    c = con()
    filas = fotos_de_arboles(c)
    c.close()
    por_especie = {}
    for f in filas:
        e = por_especie.setdefault(f["especie_id"], {
            "especie_id": f["especie_id"],
            "nombre_cientifico": f["nombre_cientifico"],
            "nombre_comun": f["nombre_comun"] or NOMBRES_ARBOLES.get(binomio(f["nombre_cientifico"])),
            "total": 0, "etiquetadas": 0, "partes": Counter(),
        })
        e["total"] += 1
        if f["parte"]:
            e["etiquetadas"] += 1
            e["partes"][f["parte"]] += 1
    return sorted(por_especie.values(), key=lambda e: e["nombre_cientifico"].lower())


@app.get("/api/especie/{especie_id}")
def api_especie(especie_id: int):
    c = con()
    filas = fotos_de_arboles(c, especie_id)
    c.close()
    if not filas:
        raise HTTPException(404, "Especie sin fotos de árbol confirmadas")
    grupos = defaultdict(list)
    for f in filas:
        grupos[f["grupo_id"]].append({
            "foto_id": f["foto_id"], "parte": f["parte"],
            "disponible": resolver_ruta_legible(f["ruta_actual"]) is not None,
        })
    # grupos grandes primero; las fotos sin grupo (None) al final, juntas
    orden = sorted((g for g in grupos if g is not None), key=lambda g: -len(grupos[g]))
    if None in grupos:
        orden.append(None)
    return {
        "especie_id": especie_id,
        "nombre_cientifico": filas[0]["nombre_cientifico"],
        "nombre_comun": filas[0]["nombre_comun"] or NOMBRES_ARBOLES.get(binomio(filas[0]["nombre_cientifico"])),
        "grupos": [{"grupo_id": g, "fotos": grupos[g]} for g in orden],
    }


class Etiqueta(BaseModel):
    foto_id: int
    parte: Optional[str] = None  # None borra la etiqueta


@app.post("/api/etiqueta")
def api_etiqueta(d: Etiqueta):
    if d.parte is not None and d.parte not in PARTES:
        raise HTTPException(400, f"Parte inválida, debe ser una de {PARTES}")
    c = con()
    if d.parte is None:
        c.execute("DELETE FROM partes_arbol_etiquetas WHERE foto_id=?", (d.foto_id,))
    else:
        c.execute("""
            INSERT INTO partes_arbol_etiquetas (foto_id, parte, revisor) VALUES (?, ?, ?)
            ON CONFLICT(foto_id) DO UPDATE SET parte=excluded.parte, revisor=excluded.revisor,
                                               fecha=CURRENT_TIMESTAMP
        """, (d.foto_id, d.parte, cargar_config().get("nombre_revisor", "Remi")))
    c.commit()
    c.close()
    return {"ok": True}


@app.get("/api/foto/{foto_id}/imagen")
def api_imagen(foto_id: int, tam: int = 400):
    c = con()
    fila = c.execute("SELECT ruta_actual FROM fotos WHERE id=?", (foto_id,)).fetchone()
    c.close()
    if not fila:
        raise HTTPException(404, "Foto no encontrada")
    ruta = resolver_ruta_legible(fila["ruta_actual"])
    if ruta is None:
        raise HTTPException(404, "Archivo no accesible (ni en espejo local ni en red)")
    try:
        with Image.open(ruta) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            tam = max(100, min(tam, 1600))
            img.thumbnail((tam, tam), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=80)
            return Response(
                content=buf.getvalue(), media_type="image/jpeg",
                headers={"Cache-Control": "private, max-age=86400"},
            )
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    print(f"Especies de árbol en lista + fichas: {len(NOMBRES_ARBOLES)}")
    uvicorn.run(app, host="127.0.0.1", port=8047)
