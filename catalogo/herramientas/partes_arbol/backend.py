"""
Etiquetado a mano de la parte del árbol que muestra cada foto (árbol completo, tronco,
hoja, flor, fruto, detalle u otro), por especie y por grupo de espécimen. Sirve para saber qué
partes ya tiene cada especie de árbol (pedido de Maya: árbol completo, tronco, hoja,
fruto y flor según aplique) y cuáles faltan por fotografiar.

No preclasifica con BioCLIP: se probó (8-oct) y acertó ~5 de 15.

Especie de árbol = nombre científico en una ficha de árbol del sitio (fichas.json) o en
Lista_Arboles_ITESO.csv, comparado por binomio normalizado. Solo fotos confirmadas.

"Detalle" (micro/macro, 21-oct) va cuando a simple vista no se reconoce de qué parte es
(textura de corteza, tricomas, insecto sobre la hoja); si se reconoce la flor, es "flor".
La ★ "destacada" es una calidad, no una parte: se suma a la parte y sirve para elegir la
foto de cada anillo y para galerías y promoción.

Escribe solo en `partes_arbol_etiquetas` y `fotos_destacadas` (una fila por foto, commit por fila).

Uso: python backend.py, luego abrir http://localhost:8047
"""

import csv
import json
import re
import sys
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # catalogo/, para importar comun/
from comun.bd import con, resolver_ruta_legible  # noqa: E402
from comun.rutas import RUTA_BD, RUTA_LISTA_ARBOLES, RUTA_FICHAS, cargar_config  # noqa: E402


PARTES = ["arbol_completo", "tronco", "hoja", "flor", "fruto", "detalle", "otro"]

app = FastAPI()


# Una sola vez al arrancar, nunca por request (ver "database is locked" en CLAUDE.md)
_c_inicial = con()
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS partes_arbol_etiquetas (
    foto_id INTEGER PRIMARY KEY, parte TEXT NOT NULL, revisor TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS fotos_destacadas (
    foto_id INTEGER PRIMARY KEY, revisor TEXT, fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.commit()
_c_inicial.close()


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


def fotos_de_arboles(c, especie_id=None):
    filas = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, e.id AS especie_id, e.nombre_cientifico,
               e.nombre_comun, g.grupo_id, p.parte, d.foto_id IS NOT NULL AS destacada
        FROM fotos f
        JOIN especies e ON e.id = f.especie_id
        LEFT JOIN especimen_grupos_confirmados g ON g.foto_id = f.id
        LEFT JOIN partes_arbol_etiquetas p ON p.foto_id = f.id
        LEFT JOIN fotos_destacadas d ON d.foto_id = f.id
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
            "total": 0, "etiquetadas": 0, "destacadas": 0, "partes": Counter(),
        })
        e["total"] += 1
        e["destacadas"] += f["destacada"]
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
            "foto_id": f["foto_id"], "parte": f["parte"], "destacada": bool(f["destacada"]),
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


class Destacada(BaseModel):
    foto_id: int
    destacada: bool


@app.post("/api/destacada")
def api_destacada(d: Destacada):
    c = con()
    if d.destacada:
        c.execute("INSERT OR IGNORE INTO fotos_destacadas (foto_id, revisor) VALUES (?, ?)",
                  (d.foto_id, cargar_config().get("nombre_revisor", "Remi")))
    else:
        c.execute("DELETE FROM fotos_destacadas WHERE foto_id=?", (d.foto_id,))
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
