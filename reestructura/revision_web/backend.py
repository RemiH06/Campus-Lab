"""
Revisor web de especies: reemplaza Revision_Especies.ipynb (input() de texto) por una
interfaz en el navegador. Corre 100% local, no se publica ni se expone a internet.

Une en una sola cola tres cosas que antes vivian separadas:
  - Sugerencias de Pl@ntNet ya con especie_id (fotos.estado='pendiente'), como antes.
  - "posible_cientifico" de Resolucion_Nombres.ipynb: nombre reconstruido del nombre
    de archivo, un solo candidato.
  - "ambiguo" de Resolucion_Nombres.ipynb: nombre comun que mapea a 2+ cientificos
    en BASE_DATOS_GENERAL. Antes no tenia interfaz (necesita elegir, no es si/no).
  - "codigo_especimen": mismo individuo fotografiado varias veces (mismo codigo tipo
    "106_020" en el nombre). No trae sugerencia sola, pero al confirmar una foto del
    grupo se puede aplicar la misma especie a las demas (propagacion).

No inventa nombres nuevos: toda sugerencia y todo resultado de busqueda sale de
referencia_nombres_comunes (espejo de BASE_DATOS_GENERAL.xlsx), igual que ya hace
Especies_PlantNet.ipynb con su filtro ESPECIES_OFICIALES.

Uso: python backend.py, luego abrir http://localhost:8040
"""

import concurrent.futures
import json
import re
import sqlite3
import unicodedata
from io import BytesIO
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel

RUTA_BD = Path(__file__).parent / "../../experimentos/bd/campuslab_volumen.db"
RUTA_CONFIG = Path(__file__).parent / "../notebooks/config_local.json"

app = FastAPI(title="Revisor Campus Lab")

# Cache en memoria: mismo proceso, misma especie no se vuelve a pedir a iNaturalist
# en la misma sesion de revision. Se pierde al reiniciar el servidor, no hace falta mas.
_cache_inaturalist = {}


def fotos_inaturalist(nombre_cientifico, limite=4):
    """Fotos de referencia de internet para la especie sugerida (no son de Campus Lab).
    La API de lectura de iNaturalist es abierta, sin API key ni aprobacion (a diferencia
    de crear observaciones, eso si la necesita).

    Se piden observaciones reales (no solo la foto "default" del taxon) para que las
    4 fotos vengan de fotografos distintos y en angulos distintos (flor, planta completa,
    corteza, etc. segun lo que la gente haya subido) sin tener que clasificar nosotros
    que organo es cada una — ver la discusion sobre la tabla de consulta por grupo/familia
    mas abajo, queda pendiente para cuando haga falta mas precision que "varias fotos
    distintas".
    """
    if not nombre_cientifico:
        return []
    if nombre_cientifico in _cache_inaturalist:
        return _cache_inaturalist[nombre_cientifico]
    fotos = []
    try:
        r = requests.get(
            "https://api.inaturalist.org/v1/observations",
            params={
                "taxon_name": nombre_cientifico,
                "photos": "true",
                "quality_grade": "research",
                "order_by": "votes",
                "per_page": limite,
            },
            timeout=6,
        )
        r.raise_for_status()
        for obs in r.json().get("results", []):
            for foto in obs.get("photos", [])[:1]:  # una por observacion, para variedad
                url = foto.get("url")
                if url:
                    fotos.append(url.replace("square.", "medium."))
            if len(fotos) >= limite:
                break
    except (requests.RequestException, ValueError):
        pass  # sin internet o sin resultado: se muestra solo lo del catalogo, no truena
    _cache_inaturalist[nombre_cientifico] = fotos
    return fotos

# PENDIENTE EN EL RADAR (no construir hasta que haga falta de verdad): si algun dia se
# necesita garantizar partes especificas (tallo/fruto/flor/hoja) en vez de solo variedad,
# la forma correcta NO es un automata — es una tabla de consulta simple por especies.grupo
# o especies.familia (ej. Cactaceae -> tallo/flor/fruto, sin hoja diferenciada), ya que
# ninguna API gratuita (iNaturalist, GBIF, Pl@ntNet) deja pedir fotos filtradas por organo.


def cargar_config():
    if not RUTA_CONFIG.exists():
        raise FileNotFoundError(f"No se encontro {RUTA_CONFIG}. Copia config_local.example.json y ajustalo.")
    return json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))


_ITESO_DISPONIBLE = None


def red_iteso_disponible():
    """Chequeo de una sola vez por corrida del servidor (cacheado), con timeout corto.
    Un drive de red desconectado (Y:\\) puede colgarse varios segundos/minutos en
    cualquier acceso, incluyendo un simple .exists(); sin este cache, cada foto que no
    esta en el espejo local congelaria la revision entera esperando a la red."""
    global _ITESO_DISPONIBLE
    if _ITESO_DISPONIBLE is None:
        # OJO: nada de "with ThreadPoolExecutor(...) as ex", su __exit__ hace
        # shutdown(wait=True) y espera a que el hilo colgado termine igual, tirando
        # el timeout de result() a la basura. shutdown(wait=False) suelta el hilo
        # colgado en segundo plano y regresa de inmediato.
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        futuro = ex.submit(lambda: Path("Y:/").exists())
        try:
            _ITESO_DISPONIBLE = futuro.result(timeout=2)
        except concurrent.futures.TimeoutError:
            _ITESO_DISPONIBLE = False
        ex.shutdown(wait=False)
    return _ITESO_DISPONIBLE


def resolver_ruta_legible(ruta_actual):
    """Mismo mecanismo que 'resolver_ruta_legible' en Especies_PlantNet.ipynb: si hay un
    espejo local configurado (trabajo fuera de la red de ITESO, 'ruta_espejo_local_fotos'
    en config_local.json) y la foto ya se copio ahi, usa esa copia. Si no esta ahi Y la
    red de ITESO no responde, regresa None de una vez (ver red_iteso_disponible) en vez
    de intentar .exists() contra Y:\\ y colgarse. Si hay red, usa la ruta real normal."""
    ruta_espejo = cargar_config().get("ruta_espejo_local_fotos")
    if ruta_espejo:
        local = Path(ruta_espejo) / Path(ruta_actual).name
        if local.exists():
            return local
    if not red_iteso_disponible():
        return None
    return Path(ruta_actual)


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


# Columna de control para las sugerencias de iNaturalist: sin esto, rechazar una
# sugerencia de una foto que ya estaba en limbo (estado='pendiente_revision') no
# cambia ningun campo que el query de la cola filtre, y la foto reaparaceria en la
# cola para siempre. Se marca "revisado" en cuanto se toma CUALQUIER decision sobre
# esa foto (confirmar o rechazar), sin importar si la sugerencia vino de iNaturalist
# o de otro origen (no-op inofensivo si la foto no tiene fila en inaturalist_intentos).
_c_inicial = sqlite3.connect(RUTA_BD)
_cols_inaturalist = [r[1] for r in _c_inicial.execute("PRAGMA table_info(inaturalist_intentos)")]
if _cols_inaturalist and "revisado" not in _cols_inaturalist:
    _c_inicial.execute("ALTER TABLE inaturalist_intentos ADD COLUMN revisado INTEGER DEFAULT 0")
    _c_inicial.commit()
_c_inicial.close()


# ---- Misma logica de parseo/clasificacion que Resolucion_Nombres.ipynb ----
# (copiada a proposito, no importada: este backend no depende de que el notebook
# se haya corrido en esta sesion, solo de que referencia_nombres_comunes este en la BD).

PATRON_NOMBRE = re.compile(r"^(AUTORES|ESPECIE|EVENTOS|ESPACIOS)-(.+)-([0-9a-f]{6})\.[^.]+$", re.IGNORECASE)
PATRON_CODIGO_ESPECIMEN = re.compile(r"^[\d_]+$")
PATRON_CIENTIFICO_PEGADO = re.compile(r"^([A-ZÁÉÍÓÚ][a-záéíóúñ]+){2,}$")
PATRON_SEGMENTOS = re.compile(r"[A-ZÁÉÍÓÚ][a-záéíóúñ]+")
# Se revisa contra CUALQUIER segmento (genero y "epiteto"), no solo el genero: se
# descubrio con "Encyclias arboretum" -> la carpeta original era Encyclia(s) fotografiadas
# EN el Arboretum, no una especie llamada "arboretum". El bug era que solo se revisaba
# el genero, nunca la palabra que se tomaba como epiteto.
PALABRAS_NO_TAXONOMICAS = {"casa", "nueva", "duda", "sin", "revisar", "copia", "copias", "otras",
                           "fotos", "sub", "naturalista", "concurso", "taller", "juntas",
                           "arboretum", "huerto", "jardin", "jardín", "campus",
                           "estacion", "estación", "espacio", "espacios",
                           "subir", "subira", "nat"}  # "SubiraNat" = carpeta "Subir a Naturalista", no especie


def normalizar_comun(nombre):
    if not nombre:
        return None
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def cargar_referencia(c):
    filas = c.execute("SELECT nombre_comun, comun_normalizado, nombre_cientifico, grupo FROM referencia_nombres_comunes").fetchall()
    por_normalizado = {}
    for f in filas:
        por_normalizado.setdefault(f["comun_normalizado"], []).append(dict(f))
    return por_normalizado


def parsear_nombre_archivo(nombre_archivo, por_normalizado):
    m = PATRON_NOMBRE.match(nombre_archivo)
    if not m:
        return {"categoria": "no_parseable"}
    rama, medio, _hash = m.groups()
    partes = medio.split("-", 1)
    especie_token = partes[1] if len(partes) == 2 else partes[0]

    if especie_token.upper() == "SINESP" or not especie_token:
        return {"categoria": "sin_nombre"}

    if PATRON_CODIGO_ESPECIMEN.fullmatch(especie_token):
        return {"categoria": "codigo_especimen", "especie_token": especie_token}

    token_norm = normalizar_comun(especie_token)
    candidatos = por_normalizado.get(token_norm, [])
    cientificos_distintos = {c["nombre_cientifico"] for c in candidatos}
    if len(cientificos_distintos) >= 2:
        return {"categoria": "ambiguo", "candidatos": candidatos}
    if len(cientificos_distintos) == 1:
        return {"categoria": "resuelto"}  # esto ya lo aplica Resolucion_Nombres.ipynb, no deberia llegar aqui

    if PATRON_CIENTIFICO_PEGADO.match(especie_token):
        segmentos = PATRON_SEGMENTOS.findall(especie_token)
        genero, resto = segmentos[0], segmentos[1:]
        if not any(s.lower() in PALABRAS_NO_TAXONOMICAS for s in segmentos):
            reconstruido = genero + " " + " ".join(s.lower() for s in resto)
            return {"categoria": "posible_cientifico", "nombre_cientifico": reconstruido}

    return {"categoria": "no_reconocido"}


def nombre_archivo_de(ruta):
    return ruta.replace("\\", "/").rsplit("/", 1)[-1]


def fotos_referencia_para_especie(c, especie_id, excluir_foto_id, limite=4):
    """Otras fotos YA confirmadas (usable) de la misma especie, para comparar visualmente.
    Fotos reales de Campus Lab, no imagenes genericas de internet."""
    if not especie_id:
        return []
    filas = c.execute(
        "SELECT id FROM fotos WHERE especie_id=? AND estado='usable' AND id != ? AND ruta_actual NOT LIKE '%.db' LIMIT ?",
        (especie_id, excluir_foto_id, limite),
    ).fetchall()
    return [f["id"] for f in filas]


def fotos_referencia_para_nombre(c, nombre_cientifico, excluir_foto_id, limite=4):
    fila = c.execute("SELECT id FROM especies WHERE nombre_cientifico=?", (nombre_cientifico,)).fetchone()
    if not fila:
        return []
    return fotos_referencia_para_especie(c, fila["id"], excluir_foto_id, limite)


# ---- Armar la cola ----

def armar_cola():
    c = con()
    por_normalizado = cargar_referencia(c)

    cola = []

    # 1. Sugerencias de Pl@ntNet, ya con especie_id
    de_plantnet = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, e.id AS especie_id, e.nombre_cientifico,
               e.plantnet_score, e.familia, e.genero
        FROM fotos f JOIN especies e ON e.id = f.especie_id
        WHERE f.estado = 'pendiente' AND f.ruta_actual NOT LIKE '%.db'
        ORDER BY f.id
    """).fetchall()
    for fila in de_plantnet:
        cola.append({
            "foto_id": fila["foto_id"],
            "origen": "plantnet",
            "categoria": "plantnet",
            "sugerencias": [{
                "especie_id": fila["especie_id"],
                "nombre_cientifico": fila["nombre_cientifico"],
                "familia": fila["familia"],
                "genero": fila["genero"],
                "score": fila["plantnet_score"],
            }],
            "grupo_token": None,
        })

    # 1b. Sugerencias de Pl@ntNet por debajo del umbral de auto-aceptar (70%) o fuera de la
    # lista oficial: no se descartan, se le pasan a revision manual con su score real, en vez
    # de perderse sin que nadie las vea.
    de_plantnet_bajo_umbral = c.execute("""
        SELECT pi.foto_id, pi.nombre_sugerido, pi.score
        FROM plantnet_intentos pi JOIN fotos f ON f.id = pi.foto_id
        WHERE pi.aceptado = 0 AND pi.nombre_sugerido IS NOT NULL AND f.especie_id IS NULL
          AND f.estado = 'pendiente' AND f.ruta_actual NOT LIKE '%.db'
        ORDER BY pi.score DESC
    """).fetchall()
    for fila in de_plantnet_bajo_umbral:
        cola.append({
            "foto_id": fila["foto_id"],
            "origen": "plantnet",
            "categoria": "plantnet_bajo_umbral",
            "sugerencias": [{
                "especie_id": None,
                "nombre_cientifico": fila["nombre_sugerido"],
                "familia": None, "genero": None,
                "score": fila["score"],
            }],
            "grupo_token": None,
        })

    # 2. Fotos sin especie_id: clasificar por nombre de archivo (posible_cientifico / ambiguo / codigo_especimen)
    # LEFT JOIN para tener el breadcrumb de la carpeta original a la mano: en codigo_especimen
    # no hay ninguna sugerencia que ofrecer (el token es solo un numero), asi que sin esta pista
    # la unica forma de confirmar era adivinar que buscar.
    sin_especie = c.execute("""
        SELECT f.id AS foto_id, f.ruta_actual, s.breadcrumb_especie
        FROM fotos f LEFT JOIN staging_escaneo s ON s.ruta_completa = f.ruta_original
        WHERE f.especie_id IS NULL AND f.estado = 'pendiente' AND f.ruta_actual NOT LIKE '%.db'
    """).fetchall()

    grupos_especimen = {}
    for fila in sin_especie:
        nombre_archivo = nombre_archivo_de(fila["ruta_actual"])
        info = parsear_nombre_archivo(nombre_archivo, por_normalizado)

        if info["categoria"] == "posible_cientifico":
            cola.append({
                "foto_id": fila["foto_id"],
                "origen": "resolucion_nombres",
                "categoria": "posible_cientifico",
                "sugerencias": [{
                    "especie_id": None,
                    "nombre_cientifico": info["nombre_cientifico"],
                    "familia": None, "genero": None, "score": None,
                }],
                "grupo_token": None,
            })
        elif info["categoria"] == "ambiguo":
            cola.append({
                "foto_id": fila["foto_id"],
                "origen": "resolucion_nombres",
                "categoria": "ambiguo",
                "sugerencias": [{
                    "especie_id": None,
                    "nombre_cientifico": c2["nombre_cientifico"],
                    "familia": None, "genero": None, "score": None,
                } for c2 in info["candidatos"]],
                "grupo_token": None,
            })
        elif info["categoria"] == "codigo_especimen":
            grupos_especimen.setdefault(info["especie_token"], []).append((fila["foto_id"], fila["breadcrumb_especie"]))

    # Grupos de especimen: solo entran a la cola visible los que tienen 2+ fotos
    # (una sola foto con codigo no da nada para propagar, y sin nombre tampoco se
    # puede sugerir nada, asi que un grupo de 1 no aporta a esta cola).
    for token, miembros in grupos_especimen.items():
        if len(miembros) < 2:
            continue
        foto_ids = [m[0] for m in miembros]
        breadcrumb = next((b for _, b in miembros if b), None)
        for foto_id in foto_ids:
            cola.append({
                "foto_id": foto_id,
                "origen": "resolucion_nombres",
                "categoria": "codigo_especimen",
                "sugerencias": [],
                "grupo_token": token,
                "grupo_breadcrumb": breadcrumb,
                "grupo_miembros": [f for f in foto_ids if f != foto_id],
            })

    # 3. Sugerencias de iNaturalist: cubre tanto fotos nuevas (ave/insecto/mamifero/
    # hongo/anfibio_reptil/planta, especie_id NULL) como fotos que ya estaban en limbo
    # (Stanhopea, Oncidium, etc.) y ahora tambien tienen una sugerencia de iNaturalist
    # ademas de la sugerencia original rechazada. "confirmar" aqui las saca del limbo
    # de una vez (estado='usable'); "rechazar" dejar la foto en limbo con esta sugerencia
    # como la mas reciente (no inventa nombre, tal como el resto del archivo).
    de_inaturalist = c.execute("""
        SELECT ii.foto_id, ii.grupo, ii.nombre_sugerido, ii.score
        FROM inaturalist_intentos ii JOIN fotos f ON f.id = ii.foto_id
        WHERE ii.nombre_sugerido IS NOT NULL
          AND f.especie_id IS NULL AND f.ruta_actual NOT LIKE '%.db'
          AND (ii.revisado IS NULL OR ii.revisado = 0)
        ORDER BY ii.score DESC
    """).fetchall()
    for fila in de_inaturalist:
        # iNaturalist manda el score en escala 0-100, no 0-1 como Pl@ntNet: se
        # normaliza aqui para que el frontend (que asume 0-1, "score*100 + %") no
        # muestre confianzas como "9960%".
        score_normalizado = fila["score"] / 100 if fila["score"] is not None else None
        cola.append({
            "foto_id": fila["foto_id"],
            "origen": "inaturalist",
            "categoria": "inaturalist_" + (fila["grupo"] or "otro"),
            "sugerencias": [{
                "especie_id": None,
                "nombre_cientifico": fila["nombre_sugerido"],
                "familia": None, "genero": None,
                "score": score_normalizado,
            }],
            "grupo_token": None,
        })

    # Quitar de la cola visible las fotos que ahorita no se pueden ver (no estan en el
    # espejo local y la red de ITESO no responde): de nada sirve mandar a revisar una
    # sugerencia si no se puede ver la foto. No se pierden ni se tocan en la base, solo
    # no aparecen en esta lista hasta que si se puedan ver (de vuelta en ITESO, o si se
    # copian al espejo local mas adelante).
    foto_ids_cola = [item["foto_id"] for item in cola]
    if foto_ids_cola:
        placeholders = ",".join("?" * len(foto_ids_cola))
        rutas = dict(c.execute(f"SELECT id, ruta_actual FROM fotos WHERE id IN ({placeholders})", foto_ids_cola).fetchall())
        cola = [item for item in cola if resolver_ruta_legible(rutas.get(item["foto_id"], "")) is not None]

    c.close()
    return cola


@app.get("/api/cola")
def api_cola():
    cola = armar_cola()
    return {"total": len(cola), "items": cola}


@app.get("/api/foto/{foto_id}/imagen")
def api_imagen(foto_id: int):
    c = con()
    fila = c.execute("SELECT ruta_actual FROM fotos WHERE id=?", (foto_id,)).fetchone()
    c.close()
    if not fila:
        raise HTTPException(404, "Foto no encontrada")
    ruta = resolver_ruta_legible(fila["ruta_actual"])
    if ruta is None or not ruta.exists():
        raise HTTPException(404, f"Archivo no accesible: {fila['ruta_actual']} (no está en el espejo local y la red de ITESO no responde ahorita)")
    try:
        with Image.open(ruta) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail((900, 900), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, "JPEG", quality=82)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(500, f"No se pudo abrir/redimensionar: {e}")


@app.get("/api/especies/buscar")
def api_buscar_especies(q: str = ""):
    if len(q.strip()) < 2:
        return []
    c = con()
    like = f"%{normalizar_comun(q)}%"
    filas = c.execute("""
        SELECT DISTINCT nombre_comun, nombre_cientifico, grupo
        FROM referencia_nombres_comunes
        WHERE comun_normalizado LIKE ? OR LOWER(nombre_cientifico) LIKE ?
        ORDER BY nombre_comun LIMIT 25
    """, (like, f"%{q.lower()}%")).fetchall()
    c.close()
    return [dict(f) for f in filas]


@app.get("/api/referencias")
def api_referencias(excluir_foto_id: int, especie_id: int | None = None, nombre_cientifico: str | None = None):
    """Fotos para comparar contra la sugerencia: primero las ya confirmadas del propio
    catalogo de Campus Lab, y ademas fotos de iNaturalist (utiles cuando el catalogo
    todavia no tiene ninguna confirmada, como paso justo con Quercus suber).
    Se pide por separado (no dentro de /api/cola) porque calcularlo para las ~1000
    fotos de la cola de una sola vez hacia la pagina insoportablemente lenta de cargar."""
    c = con()
    nombre_para_buscar = nombre_cientifico
    if especie_id:
        ids_catalogo = fotos_referencia_para_especie(c, especie_id, excluir_foto_id)
        if not nombre_para_buscar:
            fila = c.execute("SELECT nombre_cientifico FROM especies WHERE id=?", (especie_id,)).fetchone()
            nombre_para_buscar = fila["nombre_cientifico"] if fila else None
    elif nombre_cientifico:
        ids_catalogo = fotos_referencia_para_nombre(c, nombre_cientifico, excluir_foto_id)
    else:
        ids_catalogo = []
    c.close()
    return {
        "catalogo": ids_catalogo,
        "internet": fotos_inaturalist(nombre_para_buscar),
    }


class Decision(BaseModel):
    foto_id: int
    accion: str  # "confirmar" | "rechazar"
    nombre_cientifico: str | None = None
    especie_id: int | None = None
    aplicar_a_grupo: list[int] = []


def resolver_o_crear_especie(c, nombre_cientifico, especie_id=None):
    if especie_id:
        return especie_id
    fila = c.execute("SELECT id FROM especies WHERE nombre_cientifico=?", (nombre_cientifico,)).fetchone()
    if fila:
        return fila["id"]
    cur = c.execute(
        "INSERT INTO especies (nombre_cientifico, sugerido_por) VALUES (?,?)",
        (nombre_cientifico, "revision_web"),
    )
    return cur.lastrowid


@app.post("/api/decision")
def api_decision(d: Decision):
    config = cargar_config()
    revisor = config.get("nombre_revisor", "Remi")
    c = con()

    if d.accion == "rechazar":
        c.execute("UPDATE fotos SET especie_id=NULL, estado='pendiente_revision' WHERE id=?", (d.foto_id,))
        c.execute(
            "INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, score, decision, revisor) VALUES (?,?,?,?,?)",
            (d.foto_id, d.nombre_cientifico, None, "rechazada", revisor),
        )
        c.execute("UPDATE inaturalist_intentos SET revisado=1 WHERE foto_id=?", (d.foto_id,))
        c.commit()
        c.close()
        return {"ok": True, "propagadas": 0}

    if d.accion != "confirmar":
        c.close()
        raise HTTPException(400, "accion debe ser 'confirmar' o 'rechazar'")
    if not d.nombre_cientifico and not d.especie_id:
        c.close()
        raise HTTPException(400, "falta nombre_cientifico o especie_id")

    especie_id = resolver_o_crear_especie(c, d.nombre_cientifico, d.especie_id)
    nombre_confirmado = c.execute("SELECT nombre_cientifico FROM especies WHERE id=?", (especie_id,)).fetchone()[0]
    genero_confirmado = nombre_confirmado.split(" ")[0]
    c.execute("UPDATE fotos SET estado='usable', especie_id=? WHERE id=?", (especie_id, d.foto_id))
    c.execute(
        "UPDATE especies SET fuente_validacion=? WHERE id=? AND fuente_validacion IS NULL",
        ("revision manual Campus Lab (web)", especie_id),
    )
    c.execute(
        "INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, score, decision, revisor) VALUES (?,?,?,?,?)",
        (d.foto_id, d.nombre_cientifico, None, "confirmada", revisor),
    )
    c.execute("UPDATE inaturalist_intentos SET revisado=1 WHERE foto_id=?", (d.foto_id,))
    # Si esta foto ya tenia embedding calculado con un genero provisional (limbo/iNaturalist),
    # sincronizarlo con la especie recien confirmada. Sin esto el genero se queda obsoleto y
    # 8043 agrupa/muestra la foto bajo un genero que ya no corresponde (bug real, 25-sep).
    c.execute("UPDATE especimen_embeddings SET genero=? WHERE foto_id=?", (genero_confirmado, d.foto_id))

    propagadas = 0
    for otro_id in d.aplicar_a_grupo:
        c.execute("UPDATE fotos SET estado='usable', especie_id=? WHERE id=? AND especie_id IS NULL", (especie_id, otro_id))
        c.execute(
            "INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, score, decision, revisor) VALUES (?,?,?,?,?)",
            (otro_id, d.nombre_cientifico, None, "confirmada (propagada de grupo)", revisor),
        )
        c.execute("UPDATE especimen_embeddings SET genero=? WHERE foto_id=?", (genero_confirmado, otro_id))
        propagadas += 1

    c.commit()
    c.close()
    return {"ok": True, "especie_id": especie_id, "propagadas": propagadas}


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    cargar_config()  # falla rapido si falta config_local.json, antes de levantar el server
    print(f"Base de datos: {RUTA_BD.resolve()} ({'existe' if RUTA_BD.exists() else 'NO ENCONTRADA'})")
    uvicorn.run(app, host="127.0.0.1", port=8040)
