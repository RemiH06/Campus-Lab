"""
Galeria de solo lectura para apreciar fotos en buen tamano, agrupadas por especie,
genero o grupo de especimen (el mismo grupo_id que arma reestructura/clustering_especimen).
No confirma ni cambia nada en la base de datos, es puramente de consulta.

Usa reestructura/galeria_especies/../notebooks/config_local.json para el espejo local
offline, mismo patron que las demas herramientas de revision.

Filtro por tamano de imagen: depende de la tabla fotos_dimensiones (ancho/alto en
pixeles), calculada aparte por el script de scratchpad calcular_dimensiones.py
(resumible, commit por foto). Fotos sin dimension calculada todavia no aparecen si
se aplica un filtro de tamano minimo.

Uso: python backend.py, luego abrir http://localhost:8045
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

RUTA_BD = Path(__file__).parent / "../../experimentos/bd/campuslab_volumen.db"
RUTA_CONFIG = Path(__file__).parent / "../notebooks/config_local.json"

app = FastAPI()


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


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


# "Todas las fotos tienen nombre de especie asociado, que esten confirmadas es otra
# cosa" (Remi, 24-sep): especie/genero ya no filtran por estado='usable'. Se resuelve
# el mejor nombre disponible por foto con el mismo orden de prioridad que usa
# especimen_embeddings en Clustering_Especimen.ipynb: confirmada > limbo (ultima
# sugerencia rechazada) > iNaturalist (ave/insecto/mamifero/hongo/anfibio_reptil/
# planta sin sugerencia propia). Fotos sin ninguna de las tres caen en "Sin
# identificar" en vez de desaparecer.
CTE_NOMBRES = """
    nombres AS (
        SELECT f.id AS foto_id,
            COALESCE(
                e.nombre_cientifico,
                (SELECT ir.especie_sugerida FROM identificaciones_revisadas ir
                 WHERE ir.foto_id = f.id AND ir.decision = 'rechazada' AND ir.especie_sugerida IS NOT NULL
                 ORDER BY ir.fecha DESC LIMIT 1),
                (SELECT ii.nombre_sugerido FROM inaturalist_intentos ii WHERE ii.foto_id = f.id)
            ) AS nombre,
            (f.estado = 'usable' AND f.especie_id IS NOT NULL) AS confirmada
        FROM fotos f
        LEFT JOIN especies e ON e.id = f.especie_id
        WHERE f.ruta_actual NOT LIKE '%.db' AND f.id NOT IN (SELECT foto_id FROM archivos_no_procesables)
    )
"""
ESPECIE_VALOR_SQL = "COALESCE(n.nombre, 'Sin identificar')"
GENERO_VALOR_SQL = (
    "CASE WHEN n.nombre IS NULL THEN 'Sin identificar' "
    "ELSE SUBSTR(n.nombre, 1, INSTR(n.nombre || ' ', ' ') - 1) END"
)

# Mapeo a las 7 categorias reales de revision_animal_en_planta (herramienta 8042,
# cubre todo el catalogo). "otro" junta mamifero/anfibio_reptil/hongo (poca cantidad
# cada una, no ameritan su propio filtro). "artistico" = sin_sujeto: fotos sin ningun
# organismo identificable (eventos, gente, logos, etc.), pedido asi por Remi.
CATEGORIA_SQL = {
    "planta": "r.decision = 'planta'",
    "ave": "r.decision = 'ave'",
    "insecto": "r.decision = 'insecto'",
    "otro": "r.decision IN ('mamifero','anfibio_reptil','hongo')",
    "artistico": "r.decision = 'sin_sujeto'",
    # Para revisar con Hugo de Alba (1-oct). Una foto es orquidea si su genero cae en
    # Orchidaceae por cualquiera de tres vias: el genero con el que se agrupo, la especie
    # confirmada, o el nombre escrito en el archivo original (carpetas de Hugo).
    "orquidea": """f.id IN (
        SELECT em.foto_id FROM especimen_embeddings em
        JOIN genero_taxonomia t ON t.genero = em.genero WHERE t.familia = 'Orchidaceae'
        UNION
        SELECT f2.id FROM fotos f2 JOIN especies e2 ON e2.id = f2.especie_id
        JOIN genero_taxonomia t ON t.genero = SUBSTR(e2.nombre_cientifico, 1, INSTR(e2.nombre_cientifico || ' ', ' ') - 1)
        WHERE t.familia = 'Orchidaceae'
        UNION
        SELECT p.foto_id FROM pistas_nombre_archivo p
        JOIN genero_taxonomia t ON t.genero = SUBSTR(p.nombre_cientifico, 1, INSTR(p.nombre_cientifico || ' ', ' ') - 1)
        WHERE t.familia = 'Orchidaceae')""",
}


def clausula_filtros(ancho_min, alto_min, categoria):
    condiciones = []
    if ancho_min:
        condiciones.append(f"d.ancho >= {int(ancho_min)}")
    if alto_min:
        condiciones.append(f"d.alto >= {int(alto_min)}")
    if categoria:
        if categoria not in CATEGORIA_SQL:
            raise HTTPException(400, "categoria invalida")
        condiciones.append(CATEGORIA_SQL[categoria])
    return (" AND " + " AND ".join(condiciones)) if condiciones else ""


def query_base(tipo):
    """Devuelve (with_sql, select_agrupador, from_join, campo_valor) segun el tipo."""
    if tipo == "especie":
        return (
            CTE_NOMBRES,
            f"{ESPECIE_VALOR_SQL} AS grupo_valor, {ESPECIE_VALOR_SQL} AS grupo_etiqueta, NULL AS grupo_referencia",
            """FROM nombres n JOIN fotos f ON f.id = n.foto_id
               LEFT JOIN fotos_dimensiones d ON d.foto_id = f.id
               LEFT JOIN revision_animal_en_planta r ON r.foto_id = f.id
               WHERE 1=1""",
            ESPECIE_VALOR_SQL,
        )
    if tipo == "genero":
        return (
            CTE_NOMBRES,
            f"{GENERO_VALOR_SQL} AS grupo_valor, {GENERO_VALOR_SQL} AS grupo_etiqueta, NULL AS grupo_referencia",
            """FROM nombres n JOIN fotos f ON f.id = n.foto_id
               LEFT JOIN fotos_dimensiones d ON d.foto_id = f.id
               LEFT JOIN revision_animal_en_planta r ON r.foto_id = f.id
               WHERE 1=1""",
            GENERO_VALOR_SQL,
        )
    if tipo == "grupo":
        return (
            None,
            "g.grupo_id AS grupo_valor, g.grupo_id AS grupo_etiqueta, "
            "COALESCE(MAX(e.nombre_cientifico), MAX(em.genero)) AS grupo_referencia",
            """FROM especimen_grupos_confirmados g
               JOIN especimen_embeddings em ON em.foto_id = g.foto_id
               JOIN fotos f ON f.id = g.foto_id
               LEFT JOIN fotos_dimensiones d ON d.foto_id = f.id
               LEFT JOIN revision_animal_en_planta r ON r.foto_id = f.id
               LEFT JOIN especies e ON e.id = f.especie_id
               WHERE 1=1""",
            "g.grupo_id",
        )
    raise HTTPException(400, "tipo invalido, usa especie/genero/grupo")


def con_with(with_sql):
    return f"WITH {with_sql} " if with_sql else ""


@app.get("/api/catalogo")
def api_catalogo(tipo: str, ancho_min: int = 0, alto_min: int = 0, categoria: str = ""):
    with_sql, select_agrupador, from_join, campo_valor = query_base(tipo)
    filtro = clausula_filtros(ancho_min, alto_min, categoria)
    c = con()
    filas = c.execute(f"""
        {con_with(with_sql)}SELECT {select_agrupador}, COUNT(*) AS total, MIN(f.id) AS portada
        {from_join}{filtro}
        GROUP BY grupo_valor HAVING total > 0 ORDER BY grupo_valor
    """).fetchall()
    c.close()
    return {"carpetas": [
        {"valor": f["grupo_valor"], "etiqueta": f["grupo_etiqueta"],
         "referencia": f["grupo_referencia"], "total": f["total"], "portada": f["portada"]}
        for f in filas
    ]}


@app.get("/api/galeria")
def api_galeria(tipo: str, valor: str, ancho_min: int = 0, alto_min: int = 0, categoria: str = ""):
    with_sql, select_agrupador, from_join, campo_valor = query_base(tipo)
    filtro = clausula_filtros(ancho_min, alto_min, categoria)
    c = con()
    filas = c.execute(f"""
        {con_with(with_sql)}SELECT f.id AS foto_id, d.ancho, d.alto
        {from_join} AND {campo_valor} = ?{filtro}
        GROUP BY f.id
    """, (valor,)).fetchall()
    c.close()

    fotos = [{"foto_id": f["foto_id"], "ancho": f["ancho"], "alto": f["alto"]} for f in filas]
    fotos.sort(key=lambda x: (x["ancho"] or 0) * (x["alto"] or 0), reverse=True)
    return {"total": len(fotos), "fotos": fotos}


@app.get("/api/foto/{foto_id}/imagen")
def api_imagen(foto_id: int, max: int = 1100):
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
            img.save(buf, "JPEG", quality=90)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    uvicorn.run(app, host="127.0.0.1", port=8045)
