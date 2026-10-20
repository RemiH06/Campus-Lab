"""Rutas del proyecto en un solo lugar. Si algo cambia de carpeta, se corrige aquí y nada más.

Uso desde una herramienta o script dentro de catalogo/:
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[N]))  # N = niveles hasta catalogo/
    from comun.rutas import RUTA_BD, SALIDA, cargar_config
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO = RAIZ / "catalogo"

RUTA_BD = RAIZ / "experimentos" / "bd" / "campuslab_volumen.db"  # la BD real; vive ahí desde la migración
RUTA_CONFIG = CATALOGO / "config_local.json"
LISTAS = CATALOGO / "listas"
SALIDA = CATALOGO / "salida"
RUTA_LISTA_ARBOLES = LISTAS / "Lista_Arboles_ITESO.csv"
RUTA_FICHAS = SALIDA / "sitio_campuslab" / "fichas.json"


def cargar_config(obligatorio=False):
    if not RUTA_CONFIG.exists():
        if obligatorio:
            raise FileNotFoundError(f"No se encontro {RUTA_CONFIG}. Copia config_local.example.json y ajustalo.")
        return {}
    return json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
