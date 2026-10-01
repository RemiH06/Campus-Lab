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


# Creada una sola vez al arrancar, no por request (mismo patron de siempre para
# evitar "database is locked" si otra herramienta esta escribiendo).
_c_inicial = sqlite3.connect(RUTA_BD)
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS limbo_clasificacion (
    grupo_id INTEGER PRIMARY KEY, orden_o_familia TEXT, revisor TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.execute("""CREATE TABLE IF NOT EXISTS genero_taxonomia (
    genero TEXT PRIMARY KEY, reino TEXT, clase TEXT, orden TEXT, familia TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP)""")
_c_inicial.commit()
_c_inicial.close()


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


# Orquideas y suculentas son su propio tema aparte (Remi, 25/30-sep): se dejan
# agrupadas pero NO se confirman en esta pasada general. Ajustar/quitar cuando se
# retome ese tema por separado.
ORQUIDEAS_SUCULENTAS = {
    "Laelia", "Bletia", "Habenaria", "Spathoglottis", "Epidendrum", "Scaphyglottis",
    "Rhynchostele", "Malaxis", "Platystele", "Arundina", "Sacoila", "Cyrtopodium",
    "Rodriguezia", "Myrmecophila", "Paphiopedilum", "Phaius", "Dendrobium", "Cymbidium",
    "Bolusiella", "Clowesia", "Stanhopea", "Brassavola", "Oncidium", "Encyclia",
    "Mormodes", "Trichocentrum", "Alatiglossum", "Prosthechea",
    "Austrocylindropuntia", "Kroenleinia", "Cotyledon", "Quetzalcoatlia", "Aeonium",
    "Echeveria", "Mammillaria", "Astrophytum", "Echinopsis", "Ferocactus", "Melocactus",
    "Copiapoa", "Frailea", "Haworthiopsis", "Sedum", "Graptopetalum", "Opuntia",
    "Pilosocereus", "Selenicereus", "Lepismium", "Cereus", "Acanthocalycium",
}


def grupos_sin_confirmar(c, excluir_orquideas_suculentas=True):
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
    grupos = {gid: fids for gid, fids in grupos.items() if not any(f in confirmadas for f in fids)}

    if not excluir_orquideas_suculentas:
        return grupos

    resultado = {}
    for gid, fids in grupos.items():
        generos = {r["genero"] for r in c.execute(
            "SELECT genero FROM especimen_embeddings WHERE foto_id IN ({})".format(",".join("?" * len(fids))), fids
        ).fetchall()}
        if generos & ORQUIDEAS_SUCULENTAS:
            continue
        resultado[gid] = fids
    return resultado


@app.get("/api/grupos")
def api_grupos(tipo: str = "todos"):
    c = con()
    grupos = grupos_sin_confirmar(c)
    resultado = []
    for gid, fids in grupos.items():
        estados = {r["estado"] for r in c.execute(
            "SELECT estado FROM fotos WHERE id IN ({})".format(",".join("?" * len(fids))), fids
        ).fetchall()}
        es_limbo = "pendiente_revision" in estados
        if tipo == "limbo" and not es_limbo:
            continue
        if tipo == "nuevo" and es_limbo:
            continue

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
            "es_limbo": es_limbo,
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
    clasificacion = c.execute(
        "SELECT orden_o_familia FROM limbo_clasificacion WHERE grupo_id=?", (grupo_id,)
    ).fetchone()
    c.close()
    return {
        "grupo_id": grupo_id, "fotos": fotos, "candidatos": candidatos_resumen,
        "orden_o_familia_previo": clasificacion["orden_o_familia"] if clasificacion else None,
    }


_HINT_REINO = {"planta": "Plantae", "hongo": "Fungi"}


def taxonomia_genero(c, genero):
    """Reino/clase/orden/familia de un genero: cache en genero_taxonomia, y si falta se
    pide a GBIF (una sola vez). Sin red o sin match devuelve None sin romper nada."""
    fila = c.execute("SELECT * FROM genero_taxonomia WHERE genero=?", (genero,)).fetchone()
    if fila:
        return fila if fila["reino"] else None
    import urllib.parse
    import urllib.request
    decision = c.execute("""
        SELECT r.decision FROM especimen_embeddings e
        JOIN revision_animal_en_planta r ON r.foto_id = e.foto_id
        WHERE e.genero=? GROUP BY r.decision ORDER BY COUNT(*) DESC LIMIT 1
    """, (genero,)).fetchone()
    hint = _HINT_REINO.get(decision["decision"], "Animalia") if decision else None
    # Pl@ntNet solo sugiere plantas: pesa mas que la categoria de 8042, que en fotos con
    # animal posado (ej. Stanhopea con Euglossa) dice "insecto" y forzaba el reino equivocado
    if c.execute("SELECT 1 FROM plantnet_intentos WHERE nombre_sugerido LIKE ? LIMIT 1", (genero + " %",)).fetchone():
        hint = "Plantae"
    try:
        url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(genero)}&rank=GENUS"
        if hint:
            url += f"&kingdom={hint}"
        with urllib.request.urlopen(url, timeout=5) as r:
            m = json.load(r)
        if m.get("matchType") in (None, "NONE") or not m.get("kingdom"):
            url2 = f"https://api.gbif.org/v1/species/search?q={urllib.parse.quote(genero)}&rank=GENUS&limit=30"
            with urllib.request.urlopen(url2, timeout=5) as r:
                s = json.load(r)
            m = next((x for x in s.get("results", [])
                      if x.get("canonicalName") == genero and (hint is None or x.get("kingdom") == hint)), None)
        if not m:
            return None
        c.execute(
            "INSERT OR REPLACE INTO genero_taxonomia (genero, reino, clase, orden, familia) VALUES (?,?,?,?,?)",
            (genero, m.get("kingdom"), m.get("class"), m.get("order"), m.get("family")),
        )
        c.commit()
        return c.execute("SELECT * FROM genero_taxonomia WHERE genero=?", (genero,)).fetchone()
    except Exception:
        return None


@app.get("/api/grupo/{grupo_id}/similares")
def api_similares(grupo_id: int):
    """Especies parecidas (misma familia; si hay pocas, tambien mismo orden) que YA estan
    en el catalogo: primero las confirmadas, luego las que solo aparecen como sugerencia
    en grupos todavia sin confirmar."""
    c = con()
    fids = [r["foto_id"] for r in c.execute(
        "SELECT foto_id FROM especimen_grupos_confirmados WHERE grupo_id=?", (grupo_id,)
    ).fetchall()]
    if not fids:
        c.close()
        raise HTTPException(404, "Grupo no encontrado")

    generos = [r["genero"] for r in c.execute(
        "SELECT genero FROM especimen_embeddings WHERE foto_id IN ({})".format(",".join("?" * len(fids))), fids
    ).fetchall()]
    genero = max(set(generos), key=generos.count) if generos else None
    tax = taxonomia_genero(c, genero) if genero else None
    if not tax:
        c.close()
        return {"genero": genero, "familia": None, "orden": None, "similares": []}

    propios = set(fids)
    similares = {}  # nombre -> dict
    cubiertos = set()  # generos ya recorridos (el nivel orden no debe recontar los de familia)

    def agregar(nombre, foto_id, score, confirmada, nivel):
        if not nombre or foto_id in propios:
            return
        d = similares.setdefault(nombre, {"nombre": nombre, "n_fotos": 0, "portada": foto_id,
                                          "score": None, "confirmada": confirmada, "nivel": nivel})
        d["n_fotos"] += 1
        d["confirmada"] = d["confirmada"] or confirmada
        if score is not None and (d["score"] is None or score > d["score"]):
            d["score"] = round(score, 1)

    def recorrer(columna, valor, nivel):
        generos_nivel = [r["genero"] for r in c.execute(
            f"SELECT genero FROM genero_taxonomia WHERE {columna}=?", (valor,)
        ).fetchall() if r["genero"] not in cubiertos]
        if not generos_nivel:
            return
        cubiertos.update(generos_nivel)
        marcas = ",".join("?" * len(generos_nivel))
        for r in c.execute(f"""
            SELECT f.id AS foto_id, f.estado, e.nombre_cientifico
            FROM especimen_embeddings em
            JOIN fotos f ON f.id = em.foto_id
            LEFT JOIN especies e ON e.id = f.especie_id
            WHERE em.genero IN ({marcas})
        """, generos_nivel).fetchall():
            if r["estado"] == "usable" and r["nombre_cientifico"]:
                agregar(r["nombre_cientifico"], r["foto_id"], None, True, nivel)
            else:
                sugs = sorted(mejor_sugerencia(c, r["foto_id"]), key=lambda s: -s[1])
                if sugs:
                    agregar(sugs[0][0], r["foto_id"], sugs[0][1], False, nivel)

    if tax["familia"]:
        recorrer("familia", tax["familia"], "familia")
    if len(similares) < 3 and tax["orden"]:
        recorrer("orden", tax["orden"], "orden")

    lista = sorted(similares.values(), key=lambda d: (d["nivel"] != "familia", not d["confirmada"], -d["n_fotos"]))
    c.close()
    return {"genero": genero, "familia": tax["familia"], "orden": tax["orden"], "similares": lista[:15]}


class Decision(BaseModel):
    accion: str  # "confirmar" | "rechazar"
    nombre_cientifico: str | None = None
    orden_o_familia: str | None = None  # solo para "rechazar": para agrupar el envio a especialistas


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
        if d.orden_o_familia:
            c.execute(
                "INSERT OR REPLACE INTO limbo_clasificacion (grupo_id, orden_o_familia, revisor, fecha) VALUES (?,?,?,?)",
                (grupo_id, d.orden_o_familia, revisor, ahora),
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
