"""
Revisor de agrupacion por especimen dentro de genero. Los embeddings los calcula
Clustering_Especimen.ipynb (BioCLIP, cacheados en especimen_embeddings); esta
herramienta solo hace el agrupamiento (barato, cosine similarity) al vuelo cada vez
que se pide un genero, para nunca mostrar una propuesta desincronizada de embeddings
nuevos. La decision final de Remi se guarda en especimen_grupos_confirmados y ya
nunca la recalcula un proceso automatico.

Requisito explicito de Remi: debe poder mover una foto a CUALQUIER grupo (incluso de
otro genero) aunque la especie/genero predicho por Pl@ntNet no coincida - una mala
prediccion en una foto no debe bloquear que el ojo humano la agrupe bien. Por eso
"mover/crear grupo" nunca valida genero ni especie, solo trabaja con foto_id y
grupo_id sueltos.

Uso: python backend.py, luego abrir http://localhost:8043
"""

import concurrent.futures
import json
import sqlite3
from io import BytesIO
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel

RUTA_BD = Path(__file__).parent / "../../experimentos/bd/campuslab_volumen.db"
RUTA_CONFIG = Path(__file__).parent / "../notebooks/config_local.json"
UMBRAL_SIMILITUD = 0.90

app = FastAPI()


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


# Crear la tabla una sola vez al arrancar, no en cada request: hacerlo por request
# significa un DDL (escritura) por cada llamada, y choca con cualquier otro proceso
# que tenga una transaccion de escritura larga abierta al mismo tiempo (nos paso con
# el script de calculo de embeddings, que antes solo comiteaba cada 100 fotos).
_c_inicial = sqlite3.connect(RUTA_BD)
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS especimen_grupos_confirmados (
    foto_id INTEGER PRIMARY KEY, grupo_id INTEGER, revisor TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.commit()
_c_inicial.close()


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
    if RUTA_CONFIG.exists():
        config = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
        ruta_espejo = config.get("ruta_espejo_local_fotos")
        if ruta_espejo:
            local = Path(ruta_espejo) / Path(ruta_actual).name
            if local.exists():
                return local
    if not red_iteso_disponible():
        return None
    ruta_directa = Path(ruta_actual)
    return ruta_directa if ruta_directa.exists() else None


def clusters_por_similitud(foto_ids, vectores, umbral):
    """Union-find simple: dos fotos quedan en el mismo cluster si su similitud coseno
    pasa el umbral. Los vectores ya vienen normalizados (se normalizaron antes de
    guardarse), asi que la similitud coseno es solo el producto punto."""
    n = len(foto_ids)
    padre = list(range(n))

    def encontrar(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def unir(i, j):
        ri, rj = encontrar(i), encontrar(j)
        if ri != rj:
            padre[ri] = rj

    matriz = np.stack(vectores) if vectores else np.zeros((0, 1))
    sims = matriz @ matriz.T
    for i in range(n):
        for j in range(i + 1, n):
            if sims[i, j] >= umbral:
                unir(i, j)

    grupos = {}
    for i in range(n):
        raiz = encontrar(i)
        grupos.setdefault(raiz, []).append(foto_ids[i])
    return list(grupos.values())


@app.get("/api/generos")
def api_generos():
    c = con()
    filas = c.execute("""
        SELECT genero, COUNT(*) AS total
        FROM especimen_embeddings GROUP BY genero HAVING total >= 2 ORDER BY genero
    """).fetchall()
    generos = []
    for fila in filas:
        pendientes = c.execute("""
            SELECT COUNT(*) FROM especimen_embeddings e
            WHERE e.genero = ? AND e.foto_id NOT IN (SELECT foto_id FROM especimen_grupos_confirmados)
        """, (fila["genero"],)).fetchone()[0]
        generos.append({"genero": fila["genero"], "total": fila["total"], "pendientes": pendientes})
    c.close()
    return {"generos": generos}


def info_foto(c, foto_id):
    fila = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, e.nombre_cientifico
        FROM fotos f LEFT JOIN especies e ON e.id = f.especie_id WHERE f.id = ?
    """, (foto_id,)).fetchone()
    disponible = resolver_ruta_legible(fila["ruta_actual"]) is not None if fila else False
    return {
        "foto_id": foto_id,
        "especie": fila["nombre_cientifico"] if fila else None,
        "disponible": disponible,
    }


@app.get("/api/genero/{genero}")
def api_genero(genero: str):
    c = con()
    filas = c.execute(
        "SELECT foto_id, embedding FROM especimen_embeddings WHERE genero = ?", (genero,)
    ).fetchall()
    if not filas:
        c.close()
        raise HTTPException(404, "Genero sin embeddings")

    vectores_por_foto = {f["foto_id"]: np.frombuffer(f["embedding"], dtype=np.float32) for f in filas}
    confirmados_rows = c.execute("""
        SELECT foto_id, grupo_id FROM especimen_grupos_confirmados
        WHERE foto_id IN ({})
    """.format(",".join("?" * len(vectores_por_foto))), list(vectores_por_foto)).fetchall()
    confirmado_de = {r["foto_id"]: r["grupo_id"] for r in confirmados_rows}

    grupos_confirmados = {}
    for foto_id, grupo_id in confirmado_de.items():
        grupos_confirmados.setdefault(grupo_id, []).append(info_foto(c, foto_id))

    pendientes_ids = [fid for fid in vectores_por_foto if fid not in confirmado_de]
    pendientes_vectores = [vectores_por_foto[fid] for fid in pendientes_ids]
    clusters = clusters_por_similitud(pendientes_ids, pendientes_vectores, UMBRAL_SIMILITUD)

    propuestas = []
    sueltas = []
    for grupo in clusters:
        fotos = [info_foto(c, fid) for fid in grupo]
        if len(grupo) >= 2:
            propuestas.append({"fotos": fotos})
        else:
            sueltas.append(fotos[0])

    c.close()
    return {
        "genero": genero,
        "grupos_confirmados": [
            {"grupo_id": gid, "fotos": fotos} for gid, fotos in sorted(grupos_confirmados.items())
        ],
        "propuestas": propuestas,
        "sueltas": sueltas,
    }


class NuevoGrupo(BaseModel):
    foto_ids: list[int]
    grupo_id: int | None = None


@app.post("/api/grupo")
def api_grupo(datos: NuevoGrupo):
    if not datos.foto_ids:
        raise HTTPException(400, "foto_ids vacio")
    c = con()
    grupo_id = datos.grupo_id
    if grupo_id is None:
        fila = c.execute("SELECT COALESCE(MAX(grupo_id), 0) + 1 FROM especimen_grupos_confirmados").fetchone()
        grupo_id = fila[0]
    for foto_id in datos.foto_ids:
        c.execute(
            "INSERT OR REPLACE INTO especimen_grupos_confirmados (foto_id, grupo_id, revisor) VALUES (?,?,?)",
            (foto_id, grupo_id, "Lambda Heredia"),
        )
    c.commit()
    c.close()
    return {"ok": True, "grupo_id": grupo_id}


@app.delete("/api/grupo/foto/{foto_id}")
def api_quitar_de_grupo(foto_id: int):
    c = con()
    c.execute("DELETE FROM especimen_grupos_confirmados WHERE foto_id=?", (foto_id,))
    c.commit()
    c.close()
    return {"ok": True}


@app.get("/api/foto/{foto_id}/imagen")
def api_imagen(foto_id: int):
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
            img.thumbnail((300, 300), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=80)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    uvicorn.run(app, host="127.0.0.1", port=8043)
