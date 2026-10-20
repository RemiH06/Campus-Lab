"""
Buscador de una foto por su numero (id), con contexto de las fotos vecinas (mismo id
+/- N). Sirve para casos como "estas fotos van en secuencia y son la misma especie,
pero esta una foto suelta que tal vez debería pertenecer ahi" (ej. foto 3662): en vez
de buscarla en la cola completa, se salta directo a verla junto a sus vecinas.

Uso: python backend.py, luego abrir http://localhost:8044
"""

import sys
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # catalogo/, para importar comun/
from comun.bd import con, resolver_ruta_legible  # noqa: E402
from comun.rutas import RUTA_BD  # noqa: E402


app = FastAPI()


def info_foto(c, foto_id):
    fila = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, f.estado, e.nombre_cientifico
        FROM fotos f LEFT JOIN especies e ON e.id = f.especie_id WHERE f.id = ?
    """, (foto_id,)).fetchone()
    if fila is None:
        return None
    especie = fila["nombre_cientifico"]
    limbo = False
    if especie is None and fila["estado"] == "pendiente_revision":
        sugerida = c.execute("""
            SELECT especie_sugerida FROM identificaciones_revisadas
            WHERE foto_id=? AND decision='rechazada' AND especie_sugerida IS NOT NULL
            ORDER BY fecha DESC LIMIT 1
        """, (foto_id,)).fetchone()
        if sugerida:
            especie = sugerida["especie_sugerida"]
            limbo = True
    decision = c.execute(
        "SELECT decision FROM revision_animal_en_planta WHERE foto_id=?", (foto_id,)
    ).fetchone()
    disponible = resolver_ruta_legible(fila["ruta_actual"]) is not None
    return {
        "foto_id": foto_id,
        "estado": fila["estado"],
        "especie": especie,
        "limbo": limbo,
        "decision_animal": decision["decision"] if decision else None,
        "disponible": disponible,
    }


@app.get("/api/foto/{foto_id}/contexto")
def api_contexto(foto_id: int, rango: int = 10):
    c = con()
    objetivo = info_foto(c, foto_id)
    if objetivo is None:
        c.close()
        raise HTTPException(404, "Foto no encontrada")

    vecinos_ids = c.execute("""
        SELECT id FROM fotos WHERE ruta_actual NOT LIKE '%.db'
          AND id BETWEEN ? AND ? ORDER BY id
    """, (foto_id - rango, foto_id + rango)).fetchall()

    vecinos = [info_foto(c, v["id"]) for v in vecinos_ids]
    c.close()
    return {"objetivo": objetivo, "vecinos": vecinos}


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
    uvicorn.run(app, host="127.0.0.1", port=8044)
