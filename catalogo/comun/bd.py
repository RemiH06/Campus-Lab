"""Conexión a la BD y lectura de fotos, compartidas por todas las herramientas de catalogo/herramientas/."""
import concurrent.futures
import sqlite3
from pathlib import Path

from comun.rutas import RUTA_BD, cargar_config

_ITESO_DISPONIBLE = None


def con():
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    return c


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
    """Si hay un espejo local configurado (trabajo fuera de la red de ITESO,
    'ruta_espejo_local_fotos' en config_local.json) y la foto ya se copio ahi, usa esa
    copia. Si no esta ahi Y la red de ITESO no responde, regresa None de una vez (ver
    red_iteso_disponible) en vez de intentar .exists() contra Y:\\ y colgarse."""
    ruta_espejo = cargar_config().get("ruta_espejo_local_fotos")
    if ruta_espejo:
        local = Path(ruta_espejo) / Path(ruta_actual).name
        if local.exists():
            return local
    if not red_iteso_disponible():
        return None
    ruta_directa = Path(ruta_actual)
    return ruta_directa if ruta_directa.exists() else None
