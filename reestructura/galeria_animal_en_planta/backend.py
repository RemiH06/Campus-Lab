"""
Revisor de TODO el catalogo (confirmado o no, cualquier reino): para cada foto, Remi
decide a mano una de: ave, insecto, mamifero, anfibio_reptil, hongo, planta (sin
animal), sin_sujeto (raiz/suelo/corteza, tomas artisticas sin sujeto identificable) -
tabla revision_animal_en_planta. Esto sirve como filtro humano previo, mas confiable
que el triage automatico de CLIP (reino_sugerido/tipo_sugerido), antes de meterle
cualquier modelo de identificacion de ave o insecto especifico. Cuando hay un score de
deteccion_animal_en_planta (solo existe para las fotos de planta ya confirmadas que se
corrieron con BioCLIP) se muestra como referencia, pero no filtra nada.

No duplica fotos todavia, solo registra la decision humana.

Uso: python backend.py, luego abrir http://localhost:8042
"""

import concurrent.futures
import json
import sqlite3
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel

RUTA_BD = Path(__file__).parent / "../../experimentos/bd/campuslab_volumen.db"
RUTA_CONFIG = Path(__file__).parent / "../notebooks/config_local.json"

app = FastAPI()


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


# Crear la tabla una sola vez al arrancar, no en cada request: un DDL por cada llamada
# choca con cualquier otro proceso que tenga una transaccion de escritura larga abierta
# al mismo tiempo (nos paso con el script de embeddings de especimen_embeddings, que
# antes solo comiteaba cada 100 fotos y dejaba el lock de escritura minutos abierto).
_c_inicial = sqlite3.connect(RUTA_BD)
_c_inicial.execute("""
    CREATE TABLE IF NOT EXISTS revision_animal_en_planta (
        foto_id INTEGER PRIMARY KEY,
        decision TEXT,
        revisor TEXT,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
_c_inicial.commit()
_c_inicial.close()


_ITESO_DISPONIBLE = None


def red_iteso_disponible():
    """Mismo mecanismo que revision_web/backend.py: chequeo de una sola vez por corrida
    del servidor (cacheado), con timeout corto. Un drive de red desconectado (Y:\\) puede
    colgarse varios segundos/minutos en cualquier acceso, incluyendo un simple .exists();
    sin este cache, cada foto que no esta en el espejo local congelaria la galeria entera."""
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
    """Mismo mecanismo que revision_web/backend.py: usa el espejo local si existe la
    foto ahi. Si no esta ahi Y la red de ITESO no responde, regresa None de una vez en
    vez de intentar .exists() contra Y:\\ y colgarse."""
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


@app.get("/api/galeria")
def api_galeria():
    c = con()
    filas = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual,
               d.score_insecto, d.score_ave, d.score_nada,
               e.nombre_cientifico AS especie_confirmada, r.decision
        FROM fotos f
        LEFT JOIN deteccion_animal_en_planta d ON d.foto_id = f.id
        LEFT JOIN especies e ON e.id = f.especie_id
        LEFT JOIN revision_animal_en_planta r ON r.foto_id = f.id
        WHERE f.ruta_actual NOT LIKE '%.db'
        ORDER BY (d.score_insecto IS NULL), MAX(d.score_insecto, d.score_ave) DESC, f.id
    """).fetchall()
    c.close()
    items = []
    disponibles = no_disponibles = 0
    for fila in filas:
        tiene_score = fila["score_insecto"] is not None
        mejor = max(fila["score_insecto"], fila["score_ave"]) if tiene_score else None
        tipo = None
        if tiene_score:
            tipo = "insecto" if fila["score_insecto"] >= fila["score_ave"] else "ave"
        especie = fila["especie_confirmada"]
        # Genero sacado del nombre cientifico (primera palabra): la columna especies.genero
        # no esta poblada todavia (falta completar el arbol de GBIF, ver CLAUDE.md), asi que
        # se deriva aqui igual que en otras partes del proyecto.
        genero = especie.split(" ")[0] if especie else "(sin especie confirmada)"
        disponible = resolver_ruta_legible(fila["ruta_actual"]) is not None
        if disponible:
            disponibles += 1
        else:
            no_disponibles += 1
        items.append({
            "foto_id": fila["foto_id"],
            "especie_confirmada": especie,
            "genero": genero,
            "tipo_probable": tipo,
            "score": round(mejor, 3) if tiene_score else None,
            "score_nada": round(fila["score_nada"], 3) if tiene_score else None,
            "decision": fila["decision"],
            "disponible": disponible,
        })
    print(f"Galeria: {len(items)} fotos totales, {disponibles} disponibles, {no_disponibles} sin red/espejo")
    return {"total": len(items), "disponibles": disponibles, "items": items}


DECISIONES_VALIDAS = ("ave", "insecto", "mamifero", "anfibio_reptil", "hongo", "planta", "sin_sujeto")


class Decision(BaseModel):
    foto_id: int
    decision: str


@app.post("/api/decision")
def api_decision(d: Decision):
    if d.decision not in DECISIONES_VALIDAS:
        raise HTTPException(400, f"decision debe ser una de: {DECISIONES_VALIDAS}")
    c = con()
    c.execute(
        "INSERT OR REPLACE INTO revision_animal_en_planta (foto_id, decision, revisor) VALUES (?,?,?)",
        (d.foto_id, d.decision, "Lambda Heredia"),
    )
    c.commit()
    c.close()
    return {"ok": True}


@app.delete("/api/decision/{foto_id}")
def api_borrar_decision(foto_id: int):
    """Deshacer: regresa la foto a pendiente (sin decision), para el boton/tecla de
    deshacer del frontend. El frontend decide cual foto deshacer via su propio
    historial de la sesion, no hay ambiguedad de 'cual fue la ultima' aqui."""
    c = con()
    c.execute("DELETE FROM revision_animal_en_planta WHERE foto_id=?", (foto_id,))
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
            img.thumbnail((500, 500), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=80)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    uvicorn.run(app, host="127.0.0.1", port=8042)
