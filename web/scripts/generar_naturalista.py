"""
Siembra los datos de la landing Naturalista ITESO: tres CSV para Documentos y Medios y las fotos de la galería.

Se corre UNA vez. Desde ahí cada CSV es la fuente de la verdad: se edita en Excel y se sube como nueva versión del
mismo archivo (la guía de cada fragmento en web/fragmentos/<fragmento>/README.md). Volver a correrlo pisaría esas
ediciones, por eso no escribe un CSV que ya existe (pasar --forzar para rehacerlos a propósito).

  itesodex-naturalista.csv  Todas las especies de la lista oficial y si ya tienen foto (de la BD y del cruce con iNaturalist).
  galeria-naturalista.csv   Ganadores, menciones y finalistas por edición, y el álbum completo de cada una (2025: evaluación
                            final del jurado + fotos de promoción).
  fechas-naturalista.csv    Línea de tiempo del concurso.
  fotos/                    Las fotos de la galería a 1600 px, JPEG calidad 82. Se suben a Documentos y Medios con el mismo
                            nombre; la página pide la versión de 1000 px de Adaptive Media (?imagePreview=1).
Los encabezados van en palabras ("Nombre común"); los fragmentos los leen sin acentos ni mayúsculas.

Uso (desde la raíz del repo):  python web/scripts/generar_naturalista.py [--forzar]
Salida (gitignorada): catalogo/salida/liferay_subir/naturalista/
Los CSV van en UTF-8 con BOM y separados por comas, para que Excel los abra con acentos con doble clic.
Sin correos ni datos de contacto: solo el nombre con el que cada persona aparece en los resultados públicos.
"""
import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "catalogo" / "scripts"))
sys.path.insert(0, str(REPO / "catalogo"))
from inaturalist_iteso import binomio, nuestros_nombres  # noqa: E402  (mismos nombres y misma normalización que el cruce)
from comun.rutas import RUTA_BD, SALIDA as SALIDA_CATALOGO  # noqa: E402

SALIDA = SALIDA_CATALOGO / "liferay_subir" / "naturalista"
INVENTARIO = SALIDA_CATALOGO / "liferay_subir" / "arboles" / "inventario-arboles.csv"
PROMO = SALIDA_CATALOGO / "naturalista_2025_promo"
EVALUACION = Path.home() / "CampusLab_SharePoint_Local" / "Actividades e intervenciones" / "Concurso Naturalista" / \
    "2025_Foto_Naturalista ITESO" / "BD_evaluacion_Naturalista2025 FINAL.xlsx"
GRUPOS = {"arboles": "Árboles", "aves": "Aves", "orquideas": "Orquídeas", "suculentas": "Suculentas", "flores_primavera": "Flores de La Primavera"}
ALBUMES = {"2025": "https://www.facebook.com/media/set/?set=a.1079736604189239&type=3", "2023": "https://www.facebook.com/media/set/?set=a.10159672820333752&type=3"}
LUGAR = {"1": "1er lugar", "2": "2º lugar", "3": "3er lugar", "Mención": "Mención honorífica", "Finalista": "Finalista"}


def limpio(nombre):
    """Nombre científico para mostrar: género y especie (más variedad o subespecie), sin autor ("Cinnamomum verum J Presl"
    → "Cinnamomum verum") y con el epíteto en minúscula. None si es una familia (la lista de árboles trae "Asteraceae")."""
    t = nombre.replace("×", " × ").split()
    if not t or t[0].lower().endswith("aceae"):
        return None
    n = 3 if len(t) > 2 and t[1] in ("×", "x") else 2
    fuera = t[:n]
    for i in range(n, len(t) - 1, 2):
        if t[i].lower() not in ("var.", "subsp.", "ssp.", "f."):
            break
        fuera += t[i:i + 2]
    return " ".join([fuera[0].capitalize()] + [w if w == "×" else w.lower() for w in fuera[1:]])


def escribir(ruta, columnas, filas, forzar=True):
    if ruta.exists() and not forzar:
        print(f"  {ruta.name}: ya existe (puede tener ediciones a mano), no se toca. --forzar para rehacerlo.")
        return
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)
    print(f"  {ruta.name}: {len(filas)} filas")


def itesodex(forzar):
    c = sqlite3.connect(RUTA_BD)
    c.row_factory = sqlite3.Row
    nombres, oficiales = nuestros_nombres(c)
    confirmadas = Counter(binomio(n) for (n,) in c.execute(
        "SELECT e.nombre_cientifico FROM fotos f JOIN especies e ON e.id=f.especie_id WHERE f.estado='usable'"))
    a_inat = {r["binomio"]: r for r in c.execute("SELECT * FROM inat_nombres_resueltos")}
    obs = Counter(binomio(o["taxon_nombre"]) for o in c.execute(
        "SELECT taxon_nombre FROM inat_observaciones WHERE taxon_rango IN ('species','hybrid','subspecies','variety','form')"))
    # dónde buscar cada árbol: jardines del inventario con cuántos árboles hay en cada uno
    jardines = defaultdict(Counter)
    if INVENTARIO.exists():
        for r in csv.DictReader(open(INVENTARIO, encoding="utf-8-sig")):
            if r["jardin"] and r["nombre_cientifico"]:
                jardines[binomio(r["nombre_cientifico"])][r["jardin"]] += 1
    filas = []
    for b in oficiales:
        original, grupo, comun, _ = nombres[b]
        if grupo not in GRUPOS:
            continue
        r = a_inat.get(b)
        clave = binomio(r["nombre_inat"]) if r and r["nombre_inat"] else b
        if not limpio(original):
            continue
        estado = "Fotografiada" if confirmadas[b] else ("Solo en iNaturalist" if obs[clave] else "Se busca")
        donde = jardines.get(b) or jardines.get(clave) or Counter()
        filas.append([GRUPOS[grupo], (comun or "").strip(), limpio(original), estado, confirmadas[b], obs[clave],
                      f"https://mexico.inaturalist.org/taxa/{r['taxon_id']}" if r and r["taxon_id"] else "",
                      "; ".join(f"{j} ({n})" for j, n in donde.most_common(3))])
    orden = {g: i for i, g in enumerate(GRUPOS.values())}
    filas.sort(key=lambda f: (orden[f[0]], f[1].lower() or f[2].lower()))
    escribir(SALIDA / "itesodex-naturalista.csv",
             ["Grupo", "Nombre común", "Nombre científico", "Estado", "Fotos en Campus Lab", "Observaciones en iNaturalist", "Enlace a iNaturalist", "Dónde buscar"], filas, forzar)
    print("   por estado:", Counter(f[3] for f in filas), "· por grupo:", Counter((f[0], f[3]) for f in filas))


def foto_web(origen, nombre):
    (SALIDA / "fotos").mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "fotos" / f"{nombre}.jpg"
    if not destino.exists():  # 1600 px: suficiente para la página y sin publicar el original de 4-10 MB
        im = ImageOps.exif_transpose(Image.open(origen)).convert("RGB")
        im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(destino, "JPEG", quality=82, optimize=True, progressive=True)
    return nombre


def galeria(forzar):
    promo = pd.read_excel(PROMO / "Creditos_fotos_promocion_2025.xlsx", sheet_name=0)
    por_titulo = {str(p["Título en el concurso"]).strip().lower(): p for p in promo.to_dict("records") if isinstance(p["Título en el concurso"], str)}
    ev = pd.read_excel(EVALUACION, sheet_name="Hoja2", header=2)
    texto = lambda v: v.strip() if isinstance(v, str) else ""  # noqa: E731  (celdas vacías llegan como NaN)
    filas = []
    for r in ev.to_dict("records"):
        if not texto(r["Nombre"]) or str(r["Lugar"]) == "nan":
            continue
        titulo = str(r["Título"]).split(",")[0].strip()  # "Alimentando a la nueva generación, Mirlo dorso rufo": la especie va aparte
        # sin título en la hoja de promoción (el abaniquillo): se busca por especie, que en la evaluación viene en científico
        p = por_titulo.get(titulo.lower()) or next((q for q in promo.to_dict("records") if not isinstance(q["Título en el concurso"], str)
                                                    and q["Nombre científico"] == texto(r["Especie"])), None)
        especie = p["Especie (nombre común)"] if p and not isinstance(p["Título en el concurso"], str) else texto(r["Especie"]).capitalize()
        cientifico = p["Nombre científico"].split(" (")[0] if p else texto(r["Unnamed: 11"])
        # nombre sin guion bajo ni acentos: es también la URL corta en Documentos y Medios (/documents/d/campuslab/<nombre>)
        foto = foto_web(PROMO / p["Archivo"], "naturalista-2025-" + Path(p["Archivo"]).stem.lower().replace("_", "-")) if p else ""
        filas.append(["2025", texto(r["Categoría"]) or "Semiprofesional", LUGAR.get(str(r["Lugar"]).strip(), str(r["Lugar"])),
                      titulo, texto(r["Nombre"]), especie, cientifico, foto])
    orden = {v: i for i, v in enumerate(LUGAR.values())}
    filas.sort(key=lambda f: (f[0], orden.get(f[2], 9)))
    # el álbum completo de cada edición (basta en una fila); 2023 todavía sin resultados capturados, solo su álbum
    filas = [f + [ALBUMES["2025"] if i == 0 else ""] for i, f in enumerate(filas)]
    filas.append(["2023", "", "", "", "", "", "", "", ALBUMES["2023"]])
    escribir(SALIDA / "galeria-naturalista.csv",
             ["Edición", "Categoría", "Resultado", "Título", "Autor", "Especie", "Nombre científico", "Foto", "Álbum"], filas, forzar)


def fechas(forzar):
    filas = [
        ["2023", "2023-01-16", "2023-02-24", "Convocatoria", "Primera edición: fotos tomadas en el campus, Casa ITESO Clavigero y los predios del Bosque La Primavera."],
        ["2023", "2023-03-15", "", "Finalistas", "Aviso por correo y en redes del ITESO."],
        ["2023", "2023-03-21", "2023-05-26", "Exposición", "Las fotos finalistas en la Galería Jardín del campus."],
        ["2023", "2023-04-21", "", "Premiación", "75 personas participaron con más de 170 fotos."],
        ["2025", "2024-11-25", "2025-03-14", "Convocatoria", "Dos categorías: semiprofesional y celular. Se amplió del 3 al 14 de marzo."],
        ["2025", "2025-04-07", "", "Finalistas", "Aviso por correo y en redes del ITESO."],
        ["2025", "2025-04-22", "", "Premiación", "Primero y segundo lugar, menciones honoríficas y exposición de finalistas."],
        ["2027", "2026-11", "", "Convocatoria", "Fechas por confirmar. Mientras, puedes ir registrando especies en iNaturalist."],
    ]
    escribir(SALIDA / "fechas-naturalista.csv", ["Edición", "Desde", "Hasta", "Etapa", "Detalle"], filas, forzar)


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv
    SALIDA.mkdir(parents=True, exist_ok=True)
    print(f"Salida: {SALIDA}")
    itesodex(forzar)
    galeria(forzar)
    fechas(forzar)
