"""
Confirmar o mandar a limbo un GRUPO DE ESPECIMEN completo de un jalon, en vez de
foto por foto. Complementa a revision_web (8040, foto por foto) para el caso donde
ya sabemos que un grupo entero (reestructura/clustering_especimen, 8043) es el mismo
espécimen: confirmar/rechazar ahí aplica a TODAS sus fotos, respetando siempre
rechazos previos por foto (mismo golden rule que el resto del proyecto).

Fuente del "mejor candidato" por grupo: mejor sugerencia individual entre Pl@ntNet
(0-1, se normaliza a 0-100) e iNaturalist (0-100) de cualquiera de sus fotos, ya que
todas deberian ser el mismo especimen. Se muestran TODOS los candidatos agrupados por
nombre (no solo el mejor), por si hay que elegir entre dos a mano.

Uso: python backend.py, luego abrir http://localhost:8046
"""

import concurrent.futures
import json
import sqlite3
from datetime import datetime
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


def cargar_config():
    return json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))


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


def mejor_sugerencia(c, foto_id):
    """Todas las sugerencias de esta foto, normalizadas a 0-100."""
    candidatos = []
    for fila in c.execute("SELECT nombre_sugerido, score FROM plantnet_intentos WHERE foto_id=?", (foto_id,)):
        if fila["nombre_sugerido"]:
            candidatos.append((fila["nombre_sugerido"], fila["score"] * 100))
    fila = c.execute("SELECT nombre_sugerido, score FROM inaturalist_intentos WHERE foto_id=?", (foto_id,)).fetchone()
    if fila and fila["nombre_sugerido"]:
        candidatos.append((fila["nombre_sugerido"], fila["score"]))
    return candidatos


def grupos_sin_confirmar(c):
    filas = c.execute("""
        SELECT g.grupo_id, f.id AS foto_id
        FROM especimen_grupos_confirmados g
        JOIN fotos f ON f.id = g.foto_id
    """).fetchall()
    grupos = {}
    for fila in filas:
        grupos.setdefault(fila["grupo_id"], []).append(fila["foto_id"])

    confirmadas = {r["id"] for r in c.execute(
        "SELECT id FROM fotos WHERE estado='usable' AND especie_id IS NOT NULL"
    ).fetchall()}
    return {gid: fids for gid, fids in grupos.items() if not any(f in confirmadas for f in fids)}


@app.get("/api/grupos")
def api_grupos():
    c = con()
    grupos = grupos_sin_confirmar(c)
    resultado = []
    for gid, fids in grupos.items():
        candidatos = {}
        for fid in fids:
            for nombre, score in mejor_sugerencia(c, fid):
                candidatos.setdefault(nombre, []).append(score)
        mejor = None
        if candidatos:
            nombre_top = max(candidatos, key=lambda n: max(candidatos[n]))
            mejor = {"nombre": nombre_top, "score": round(max(candidatos[nombre_top]), 1)}
        genero = c.execute("SELECT genero FROM especimen_embeddings WHERE foto_id=?", (fids[0],)).fetchone()
        resultado.append({
            "grupo_id": gid,
            "total": len(fids),
            "genero": genero["genero"] if genero else None,
            "portada": min(fids),
            "mejor_candidato": mejor,
        })
    c.close()
    resultado.sort(key=lambda g: -(g["mejor_candidato"]["score"] if g["mejor_candidato"] else 0))
    return {"grupos": resultado}


@app.get("/api/grupo/{grupo_id}")
def api_grupo(grupo_id: int):
    c = con()
    fids = [r["foto_id"] for r in c.execute(
        "SELECT foto_id FROM especimen_grupos_confirmados WHERE grupo_id=?", (grupo_id,)
    ).fetchall()]
    if not fids:
        c.close()
        raise HTTPException(404, "Grupo no encontrado")

    candidatos = {}
    fotos = []
    for fid in fids:
        sugerencias = mejor_sugerencia(c, fid)
        for nombre, score in sugerencias:
            candidatos.setdefault(nombre, []).append(score)
        ruta = c.execute("SELECT ruta_actual FROM fotos WHERE id=?", (fid,)).fetchone()["ruta_actual"]
        disponible = resolver_ruta_legible(ruta) is not None
        sugerencias.sort(key=lambda s: -s[1])
        fotos.append({
            "foto_id": fid,
            "disponible": disponible,
            "mejor_sugerencia": {"nombre": sugerencias[0][0], "score": round(sugerencias[0][1], 1)} if sugerencias else None,
        })

    candidatos_resumen = sorted(
        [{"nombre": n, "score": round(max(s), 1), "n_fotos": len(s)} for n, s in candidatos.items()],
        key=lambda x: -x["score"],
    )
    c.close()
    return {"grupo_id": grupo_id, "fotos": fotos, "candidatos": candidatos_resumen}


class Decision(BaseModel):
    accion: str  # "confirmar" | "rechazar"
    nombre_cientifico: str | None = None


@app.post("/api/grupo/{grupo_id}/decision")
def api_decision(grupo_id: int, d: Decision):
    c = con()
    revisor = cargar_config().get("nombre_revisor", "Remi")
    fids = [r["foto_id"] for r in c.execute(
        "SELECT foto_id FROM especimen_grupos_confirmados WHERE grupo_id=?", (grupo_id,)
    ).fetchall()]
    if not fids:
        c.close()
        raise HTTPException(404, "Grupo no encontrado")

    ahora = datetime.now().isoformat(sep=" ", timespec="seconds")

    if d.accion == "rechazar":
        nombre = d.nombre_cientifico or "sin sugerencia"
        for fid in fids:
            c.execute("UPDATE fotos SET estado='pendiente_revision', especie_id=NULL WHERE id=?", (fid,))
            c.execute(
                "INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, decision, revisor, fecha) VALUES (?,?,?,?,?)",
                (fid, nombre, "rechazada", revisor, ahora),
            )
        c.commit()
        c.close()
        return {"ok": True, "confirmadas": 0, "bloqueadas": 0}

    if d.accion != "confirmar" or not d.nombre_cientifico:
        c.close()
        raise HTTPException(400, "accion debe ser 'confirmar' (con nombre_cientifico) o 'rechazar'")

    nombre = d.nombre_cientifico
    fila = c.execute("SELECT id FROM especies WHERE nombre_cientifico=?", (nombre,)).fetchone()
    if fila:
        especie_id = fila["id"]
    else:
        cur = c.execute("INSERT INTO especies (nombre_cientifico, sugerido_por) VALUES (?,?)", (nombre, "revision_grupos"))
        especie_id = cur.lastrowid
    genero = nombre.split(" ")[0]

    confirmadas = bloqueadas = 0
    for fid in fids:
        rechazo = c.execute(
            "SELECT 1 FROM identificaciones_revisadas WHERE foto_id=? AND decision='rechazada' AND especie_sugerida=?",
            (fid, nombre),
        ).fetchone()
        if rechazo:
            bloqueadas += 1
            continue
        c.execute("UPDATE fotos SET estado='usable', especie_id=? WHERE id=?", (especie_id, fid))
        c.execute(
            "INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, decision, revisor, fecha) VALUES (?,?,?,?,?)",
            (fid, nombre, "confirmada (grupo)", revisor, ahora),
        )
        c.execute("UPDATE especimen_embeddings SET genero=? WHERE foto_id=?", (genero, fid))
        confirmadas += 1
    c.commit()
    c.close()
    return {"ok": True, "confirmadas": confirmadas, "bloqueadas": bloqueadas}


@app.get("/api/foto/{foto_id}/imagen")
def api_imagen(foto_id: int, max: int = 500):
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
            img.thumbnail((max, max), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=85)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    cargar_config()  # falla rapido si falta config_local.json
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    uvicorn.run(app, host="127.0.0.1", port=8046)
