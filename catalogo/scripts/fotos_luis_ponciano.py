# -*- coding: utf-8 -*-
"""Paso 1 de las fotos de árboles de Luis Ponciano: referencia + hash + EXIF + miniatura.

Las fotos viven en el OneDrive personal de Luis, compartido con Campus Lab y sincronizado "solo en la
nube" (config: ruta_fotos_luis_ponciano). No se copian los originales (decisión de Remi, 28-oct): en la
BD queda la referencia (ruta relativa a esa carpeta) con SHA-1 y EXIF, y la única copia es una
miniatura de 1024 px en salida/luis_ponciano/miniaturas/ (caché para revisar y para iNaturalist /
Pl@ntNet; regenerable, nunca se publica).

Por cada foto: leer (OneDrive la descarga) → SHA-1, EXIF, dHash, miniatura → "Liberar espacio"
(attrib -P +U), y al final otra pasada para lo que OneDrive no liberó a la primera. Sin ese paso
OneDrive deja cada archivo descargado y ~55 GB no caben en el disco. Nunca mueve, renombra ni borra
nada en OneDrive.

Duplicados:
  - "TODAS" repite fotos de las entregas: misma ruta base y tamaño → se anota duplicado_de sin leerla.
    Se procesan primero las entregas, así la copia que se lee es la de la entrega.
  - mismo SHA-1 con otro nombre → duplicado_de por sha1 (se leyó, pero no se guarda otra miniatura).
  - contra la tabla fotos: dHash contra salida/inaturalist_iteso/dhash_nuestras.json; si queda a
    <= UMBRAL_HASH bits se anota parecida_a_foto_id para revisarla en el paso 2 (no se descarta sola).

Tabla nueva fotos_luis_ponciano (una fila por archivo, incluidos los duplicados). Resumible: lo que ya
tiene fila sin error se salta; comitea después de cada foto (la BD no tiene WAL).

Uso: python fotos_luis_ponciano.py                     (en seco: conteos y GB, no lee fotos)
     python fotos_luis_ponciano.py --procesar --limite 10   (piloto)
     python fotos_luis_ponciano.py --procesar           (todo; se puede cortar y volver a correr)
"""
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.rutas import RUTA_BD, SALIDA, cargar_config  # noqa: E402
from cruce_fotos_inat import CACHE_HASH, dhash, distancias_hash  # noqa: E402

MINIATURAS = SALIDA / "luis_ponciano" / "miniaturas"
LADO_MINIATURA = 1024  # tope de iNaturalist y Pl@ntNet
UMBRAL_HASH = 4  # mismo criterio estricto que cruce_fotos_inat.py
LIBRE_MINIMO = 10e9  # si OneDrive no alcanza a liberar espacio, parar antes de llenar el disco
HILOS = 4
EN_LA_NUBE = 0x400000  # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS: placeholder sin descargar

COLUMNAS = """ruta_relativa TEXT PRIMARY KEY, carpeta TEXT, entrega TEXT, bytes INTEGER, sha1 TEXT,
    duplicado_de TEXT, metodo_duplicado TEXT, ancho INTEGER, alto INTEGER, fecha_tomada TEXT,
    gps_lat REAL, gps_lon REAL, gps_alt REAL, camara TEXT, orientacion INTEGER, dhash TEXT,
    miniatura TEXT, parecida_a_foto_id INTEGER, dist_dhash INTEGER, error TEXT, procesado_en TEXT"""


def inventario(base: Path):
    """Todos los JPG con tamaño y si están solo en la nube, sin abrirlos. Entregas primero, TODAS al final."""
    filas = []
    for raiz, _, archivos in os.walk(base):
        for a in archivos:
            if a.lower().endswith((".jpg", ".jpeg")):
                p = Path(raiz) / a
                st = p.stat()
                filas.append((p.relative_to(base).as_posix(), st.st_size, bool(st.st_file_attributes & EN_LA_NUBE)))
    return sorted(filas, key=lambda f: (f[0].startswith("TODAS/"), f[0]))


def entrega_de(ruta):
    partes = ruta.split("/")
    return partes[0] if len(partes) > 1 else None


def carpeta_de(ruta):
    """Carpeta de especie: lo que hay entre la entrega (o TODAS) y el archivo, p. ej. "Cedro rojo/joven"."""
    partes = ruta.split("/")
    return "/".join(partes[1:-1]) or None


def grados(dms, ref):
    if not dms:
        return None
    g = float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600
    return -g if ref in ("S", "W") else g


def leer_exif(img):
    exif = img.getexif()
    sub = exif.get_ifd(0x8769)
    gps = exif.get_ifd(0x8825)
    fecha = sub.get(36867) or exif.get(306)  # DateTimeOriginal, si no DateTime
    camara = " ".join(str(exif.get(t, "")).strip() for t in (271, 272)).strip() or None
    alt = gps.get(6)
    return {
        "fecha_tomada": datetime.strptime(fecha, "%Y:%m:%d %H:%M:%S").isoformat(sep=" ") if fecha else None,
        "gps_lat": grados(gps.get(2), gps.get(1)),
        "gps_lon": grados(gps.get(4), gps.get(3)),
        "gps_alt": (-float(alt) if gps.get(5) == 1 else float(alt)) if alt is not None else None,
        "camara": camara,
        "orientacion": exif.get(274),
    }


def liberar_espacio(p: Path):
    """Lo mismo que "Liberar espacio" en el Explorador; OneDrive lo aplica en segundo plano."""
    subprocess.run(["attrib", "-P", "+U", str(p)], check=True, capture_output=True)


def liberar_pendientes(base: Path, rutas):
    """Si se pide liberar mientras OneDrive aún termina la descarga, lo ignora (pasó en el piloto):
    vuelve a pedirlo para lo leído que siga descargado."""
    quedaban = [r for r in rutas if (base / r).exists() and not (base / r).stat().st_file_attributes & EN_LA_NUBE]
    for r in quedaban:
        liberar_espacio(base / r)
    return len(quedaban)


def procesar_foto(base: Path, ruta: str):
    """Corre en un hilo; no toca la BD. Regresa los campos de la fila."""
    p = base / ruta
    datos = p.read_bytes()  # una sola lectura: hash y decodificación salen de memoria
    try:
        fila = {"sha1": hashlib.sha1(datos).hexdigest()}
        with Image.open(io.BytesIO(datos)) as img:
            fila["ancho"], fila["alto"] = img.size
            fila.update(leer_exif(img))
            img.draft("RGB", (LADO_MINIATURA, LADO_MINIATURA))  # JPEG: decodifica reducido
            mini = ImageOps.exif_transpose(img).convert("RGB")
        mini.thumbnail((LADO_MINIATURA, LADO_MINIATURA), Image.LANCZOS)
        fila["dhash"] = str(dhash(mini))
        destino = MINIATURAS / f"{fila['sha1'][:16]}.jpg"
        if not destino.exists():
            mini.save(destino, "JPEG", quality=85, optimize=True)
        fila["miniatura"] = destino.name
        return fila
    finally:
        liberar_espacio(p)


def main():
    cfg = cargar_config(obligatorio=True)
    base = Path(cfg["ruta_fotos_luis_ponciano"])
    filas = inventario(base)
    vistos = {}  # (nombre en minúsculas, bytes) -> primera ruta
    a_leer, por_nombre = [], []
    for ruta, tam, nube in filas:
        clave = (ruta.rsplit("/", 1)[-1].lower(), tam)
        if clave in vistos:
            por_nombre.append((ruta, tam, vistos[clave]))
        else:
            vistos[clave] = ruta
            a_leer.append((ruta, tam, nube))
    print(f"{len(filas)} JPG; {len(por_nombre)} repetidos por nombre y tamaño; "
          f"{len(a_leer)} por leer ({sum(f[1] for f in a_leer) / 1e9:.1f} GB, "
          f"{sum(1 for f in a_leer if f[2])} solo en la nube)")
    if "--procesar" not in sys.argv:
        print("En seco. Para leerlas: --procesar [--limite N]")
        return

    MINIATURAS.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(RUTA_BD)
    c.execute(f"CREATE TABLE IF NOT EXISTS fotos_luis_ponciano ({COLUMNAS})")
    hechas = {r[0] for r in c.execute("SELECT ruta_relativa FROM fotos_luis_ponciano WHERE error IS NULL")}
    sha_visto = {s: r for r, s in c.execute(
        "SELECT ruta_relativa, sha1 FROM fotos_luis_ponciano WHERE duplicado_de IS NULL AND sha1 IS NOT NULL")}
    nuestras = json.loads(CACHE_HASH.read_text(encoding="utf-8"))
    ids_n, hash_n = list(nuestras), [int(h) for h in nuestras.values()]

    def guardar(ruta, tam, **campos):
        campos = {"ruta_relativa": ruta, "carpeta": carpeta_de(ruta), "entrega": entrega_de(ruta), "bytes": tam,
                  "error": None, "procesado_en": datetime.now().isoformat(sep=" ", timespec="seconds"), **campos}
        c.execute(f"INSERT OR REPLACE INTO fotos_luis_ponciano ({', '.join(campos)}) "
                  f"VALUES ({', '.join('?' * len(campos))})", list(campos.values()))
        c.commit()

    pendientes = [f for f in a_leer if f[0] not in hechas]
    if "--limite" in sys.argv:
        pendientes = pendientes[:int(sys.argv[sys.argv.index("--limite") + 1])]
    print(f"Faltan {len(pendientes)} por leer")
    with ThreadPoolExecutor(HILOS) as ex:
        futuros = [(f, ex.submit(procesar_foto, base, f[0])) for f in pendientes]
        for n, ((ruta, tam, _), futuro) in enumerate(futuros, 1):
            try:
                fila = futuro.result()
            except Exception as e:
                guardar(ruta, tam, error=f"{type(e).__name__}: {e}")
                print(f"  error {ruta}: {e}", flush=True)
                continue
            if fila["sha1"] in sha_visto:
                fila.update(duplicado_de=sha_visto[fila["sha1"]], metodo_duplicado="sha1", miniatura=None)
            else:
                sha_visto[fila["sha1"]] = ruta
                if hash_n:
                    dist = distancias_hash([int(fila["dhash"])], hash_n)[0]
                    i = int(dist.argmin())
                    if dist[i] <= UMBRAL_HASH:
                        fila.update(parecida_a_foto_id=int(ids_n[i]), dist_dhash=int(dist[i]))
            guardar(ruta, tam, **fila)
            if n % 50 == 0:
                liberar_pendientes(base, [f[0] for f in pendientes[max(0, n - 100):n - HILOS]])
            libre = shutil.disk_usage(MINIATURAS).free
            print(f"  {n}/{len(pendientes)} {ruta} ({libre / 1e9:.0f} GB libres)", flush=True)
            if libre < LIBRE_MINIMO:
                print("Poco espacio libre: OneDrive no está liberando a tiempo. Paro; volver a correr después.")
                ex.shutdown(cancel_futures=True)
                break

    leidas = [r for r, in c.execute("SELECT ruta_relativa FROM fotos_luis_ponciano WHERE metodo_duplicado IS NOT 'nombre+tamaño'")]
    print(f"Liberadas de nuevo: {liberar_pendientes(base, leidas)} que seguían descargadas")

    # los repetidos por nombre y tamaño heredan los datos de la copia que se leyó
    c.row_factory = sqlite3.Row
    for ruta, tam, original in por_nombre:
        fuente = c.execute("SELECT * FROM fotos_luis_ponciano WHERE ruta_relativa = ? AND error IS NULL",
                           (original,)).fetchone()
        if fuente and ruta not in hechas:
            heredado = {k: fuente[k] for k in ("sha1", "ancho", "alto", "fecha_tomada", "gps_lat", "gps_lon",
                                               "gps_alt", "camara", "orientacion", "dhash")}
            guardar(ruta, tam, duplicado_de=fuente["duplicado_de"] or original,
                    metodo_duplicado="nombre+tamaño", **heredado)

    for etiqueta, sql in [
        ("filas", "SELECT COUNT(*) FROM fotos_luis_ponciano"),
        ("únicas", "SELECT COUNT(*) FROM fotos_luis_ponciano WHERE duplicado_de IS NULL AND error IS NULL"),
        ("con GPS", "SELECT COUNT(*) FROM fotos_luis_ponciano WHERE duplicado_de IS NULL AND gps_lat IS NOT NULL"),
        ("parecidas a una foto nuestra", "SELECT COUNT(*) FROM fotos_luis_ponciano WHERE parecida_a_foto_id IS NOT NULL"),
        ("con error", "SELECT COUNT(*) FROM fotos_luis_ponciano WHERE error IS NOT NULL"),
    ]:
        print(f"{etiqueta}: {c.execute(sql).fetchone()[0]}")


if __name__ == "__main__":
    main()
