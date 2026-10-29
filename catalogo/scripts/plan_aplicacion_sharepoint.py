# -*- coding: utf-8 -*-
"""F1 de la reestructura en el SharePoint oficial: una acción para CADA archivo que hay hoy en la biblioteca.

Solo lee (la carpeta sincronizada y la copia local de la estructura nueva) y escribe
salida/Plan_Aplicacion_SharePoint.xlsx. No mueve nada; eso es la F2, sobre este plan.

Acciones:
  MOVER       documento que se queda: va a su ruta de la estructura nueva (columna "Destino vN" más nueva del plan)
  SUBIR       archivo que no está en SharePoint (del repo o fusionado) y se agrega en su ruta
  POR BORRAR  duplicado, versión vieja, vacío o copia: se queda en su carpeta anterior (sin número) y se borra al final
  BORRAR      basura del sistema (desktop.ini, candados .lock de ArcGIS)
  IMAGEN F3   imagen: se queda donde está; en F3 se verifica contra el volumen y en SharePoint queda su copia de 1024 px
  REVISAR     no hay regla clara o no se pudo leer; lo decide una persona antes de la F2
  CREAR CARPETA  carpeta vacía de la estructura nueva (bandeja de entrada, páginas de Textos del sitio)

Las rutas de destino se acortan con ACORTAR: OneDrive no baja archivos con ruta de 260 caracteres o más.

Volver a correrlo justo antes de la F2: SharePoint sigue cambiando y el plan sale de lo que haya ese día.
Uso: python plan_aplicacion_sharepoint.py
"""
import hashlib
import io
import os
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.rutas import SALIDA, cargar_config  # noqa: E402

PLAN = SALIDA / "Plan_Reestructura_Documentos_SharePoint.xlsx"
SALIDA_PLAN = SALIDA / "Plan_Aplicacion_SharePoint.xlsx"
POR_BORRAR = "00. Por borrar"
IMAGENES_F3 = "00. Imágenes por pasar al volumen"

IMAGEN = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".nef", ".dng", ".cr2", ".cr3", ".gif", ".webp",
          ".bmp", ".arw", ".raf", ".jfif"}
BASURA = {".ini", ".lock"}
LIBRO_ORIG = "CAMPUS LAB (Maya)/5. Proyecto libro Aves ITESO/"
LIBRO_NUEVO = "5. Proyecto libro Aves ITESO/"          # la que Maya subió a la raíz en octubre
LIBRO_TEMPORAL = "Temporal/5. Proyecto libro Aves ITESO/"  # la misma, subida en septiembre
LIBRO = "04. Produccion de Informacion/Libro Aves de casa"
NAT = "05. Actividades/Concurso Naturalista ITESO"
DIF_NAT = "06. Comunicacion y Difusion/Difusion/Por actividad/Concurso Naturalista ITESO"

# Archivos y carpetas que llegaron después del plan (29-oct). Prefijo de la ruta de hoy -> carpeta destino.
# Gana el prefijo más largo; lo que sigue después del prefijo se conserva.
NUEVOS = {
    "Actividades e intervenciones/Concurso Naturalista/2027_Foto_Naturalista_ITESO/": f"{NAT}/2027/",
    "Actividades e intervenciones/Concurso Naturalista/Patrocinio Sony/Propuesta de terminos Sony_Concurso Naturalista ITESO 2026-27.docx":
        "05. Actividades/Patrocinio Sony/Patrocinio Sony 2026-2027/Propuesta de terminos Sony_Concurso Naturalista ITESO 2026-27.docx",
    "Actividades e intervenciones/Concurso Naturalista/2025_Foto_Naturalista ITESO/Lonas/": f"{DIF_NAT}/2025/Lonas/Editables de diseño/",
    "Actividades e intervenciones/Concurso Naturalista/2025_Foto_Naturalista ITESO/24B_": f"{DIF_NAT}/2025/Editables de diseño/24B_",
    "Actividades e intervenciones/Info espacios/Arboretum/Arboretum_MASTER.docx":
        "04. Produccion de Informacion/Fichas de espacios del campus/Arboretum/Arboretum_MASTER.docx",
    "Bases de datos/Revisión de especies ambiguas/": "09. Bases de Datos Tabulares/Revisión con especialistas/",
    f"{LIBRO_ORIG}Ilustración/Ilustraciones finales/": f"{LIBRO}/Ilustracion/Ilustraciones finales/",
}
# Carpetas del libro que no existían en el plan
LIBRO_CARPETAS = {
    "": LIBRO,
    "Libro aves Capítulos": f"{LIBRO}/Capitulos",
    "Proceso ante el comité editorial": f"{LIBRO}/Proceso editorial/Comité editorial",
    "Ilustración": f"{LIBRO}/Ilustracion",
    "Fotos": f"{LIBRO}/Fotos (indices y creditos)",
}
TIPOS = {
    "Documentos": {".docx", ".doc", ".pdf", ".pptx", ".ppt", ".txt", ".rtf", ".pub", ".odt", ".mpp", ""},
    "Tablas": {".xlsx", ".xls", ".xlsm", ".csv"},
    "Videos": {".mp4", ".mov"},
    "Audios": {".mp3", ".wav", ".m4a"},
    "Editables de diseño": {".ai", ".indd", ".idml", ".psb", ".psd", ".eps", ".lst"},
    "Comprimidos": {".zip"},
    "Enlaces y web": {".url", ".html", ".json"},
}
CARPETAS_POR_TIPO = set(TIPOS)

# Carpetas que la F2 crea vacías (ningún archivo las genera): la bandeja de entrada del mapa y una por página del
# mapa del sitio del retrabajo, para la copia de sus textos.
_TEXTOS = "03. Sitio Web Campus Lab/Textos del sitio (retrabajo)"
CARPETAS_VACIAS = ["00. Bandeja de entrada"] + [f"{_TEXTOS}/{p}" for p in (
    "Portada", "Qué es Campus Lab", "Mapas", "Explorador de especies", "Biodiversidad/Árboles", "Biodiversidad/Aves",
    "Biodiversidad/Orquídeas", "Biodiversidad/Suculentas", "Biodiversidad/Flores silvestres", "Biodiversidad/Jardines",
    "Biodiversidad/Agua", "Experiencias en el campus/Naturalista ITESO",
    "Experiencias en el campus/Avistamientos y recorridos")]

# Decisiones de Remi sobre casos REVISAR (29-oct). Ruta de hoy (o de la fila del plan) -> (acción, destino o None
# para dejar el que propuso el script).
DECISIONES = {
    f"{LIBRO_NUEVO}606a7658-99ca-497b-b4e5-4709844901d7.pdf": ("MOVER", None),
    f"{LIBRO_NUEVO}Borrador de ideas para libro Aves de casa.docx": ("MOVER", None),  # se conservan las dos versiones
    "Bases de datos/EXCEL/BASE DATOS GENERAL.xlsx": ("SUBIR", None),  # ya no está en SharePoint: desde la copia local
}


def carpeta_por_tipo(ext):
    return next((t for t, e in TIPOS.items() if ext.lower() in e), "Otros")


# Rutas cortas para las fichas del libro (29-oct): con la ruta de la carpeta sincronizada (~64 caracteres) y
# nombres de ficha de hasta 83, "Capitulos/6. Guía…/Fichas anteriores/…/Aves Majo 2024 CARPETA PROVISIONAL/"
# pasaba de 260 y OneDrive ya no podía bajar esos archivos ("La operación de nube no es válida").
_G6 = re.escape(f"{LIBRO}/Capitulos/6. Guía para observar las aves/")
_FG = f"{LIBRO}/Fichas de la guía"
ACORTAR = [
    (_G6 + r"Todas las fichas revisión final 2024/", f"{_FG}/Finales 2024/"),
    (_G6 + r"Fichas anteriores/Todas las fichas 2024 divididas por nombre/Aves (\w+) 2024 CARPETA PROVISIONAL/", f"{_FG}/Anteriores/2024 por persona/\\1/"),
    (_G6 + r"Fichas anteriores/A Todas las fichas 2024/", f"{_FG}/Anteriores/2024 (todas)/"),
    (_G6 + r"Fichas anteriores/Todas las fichas 2023/Aves ([^/]+)/", f"{_FG}/Anteriores/2023 por persona/\\1/"),
    (_G6 + r"Fichas anteriores/Todas las fichas 2023/(?:Documentos/)?", f"{_FG}/Anteriores/2023 (todas)/"),
    (_G6 + r"Fichas anteriores/", f"{_FG}/Anteriores/"),
    (_G6 + r"Plantilla y listas/", f"{LIBRO}/Capitulos/6. Guía para observar las aves/"),
]


def acortar(destino):
    for patron, nuevo in ACORTAR:
        destino, n = re.subn("^" + patron, nuevo.replace("\\\\", "\\"), destino)
        if n:
            break
    return destino


def nfc(t):
    return unicodedata.normalize("NFC", t)


def clave(nombre):
    return nfc(nombre).casefold()


def larga(p):
    """Ruta con prefijo \\\\?\\ : sin él, Windows no abre rutas de 260 caracteres o más (pasa en las fichas del libro)."""
    s = str(Path(p).resolve())
    return s if s.startswith("\\\\?\\") or os.name != "nt" else "\\\\?\\" + s


def leer(p):
    try:
        with open(larga(p), "rb") as f:
            return f.read()
    except OSError:  # OneDrive no pudo bajar el archivo (¿OneDrive.exe apagado?)
        return None


def texto_office(datos):
    """Texto de un .docx/.xlsx/.pptx: dos archivos con el mismo texto difieren solo en metadatos (SharePoint los reescribe al subir)."""
    try:
        z = zipfile.ZipFile(io.BytesIO(datos))
        partes = sorted(n for n in z.namelist() if re.fullmatch(r"word/document\.xml|xl/sharedStrings\.xml|ppt/slides/slide\d+\.xml", n))
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", " ".join(z.read(n).decode("utf-8", "ignore") for n in partes))).strip() or None
    except (zipfile.BadZipFile, KeyError):
        return None


def mismo_contenido(a, b):
    if a == b:
        return "idéntico"
    ta = texto_office(a)
    return "mismo texto" if ta and ta == texto_office(b) else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = cargar_config(obligatorio=True)
    sp = Path(cfg["ruta_sharepoint_sincronizado"])
    local = Path(cfg["ruta_destino_reestructura"])

    # 1. Inventario de hoy
    hoy = {}
    for d, _, fs in os.walk(sp):
        for f in fs:
            p = Path(d, f)
            hoy[nfc(str(p.relative_to(sp)).replace(os.sep, "/"))] = p
    print(f"SharePoint hoy: {len(hoy)} archivos")

    # 2. Plan de documentos
    plan = pd.read_excel(PLAN)
    col_origen = plan.columns[0]
    col_dest = max((c for c in plan.columns if re.fullmatch(r"Destino v\d+", c)), key=lambda c: int(c[9:]))
    plan[col_origen] = plan[col_origen].map(lambda t: nfc(t) if isinstance(t, str) else t)
    acciones = {}  # ruta de hoy -> (accion, destino, motivo)
    subir = []
    destinos_planeados = {}  # clave de destino -> ruta
    sin_origen = []
    for o, accion_v2, accion_v1, dest in zip(plan[col_origen], plan["Accion v2"], plan["Accion"], plan[col_dest]):
        if not isinstance(o, str):
            continue
        se_queda = accion_v2 in ("MOVER", "COPIAR")
        if o.startswith("VOLUMEN: "):
            subir.append((o, "IMAGEN F3", dest, "ilustración del volumen: en SharePoint solo su copia reducida"))
        elif o.startswith("NUEVO: "):
            subir.append((o, "SUBIR", dest, "no existe en SharePoint (repo o fusionado)"))
        elif o not in hoy:
            sin_origen.append((o, se_queda, dest, accion_v2 if se_queda else accion_v1))
            continue
        elif se_queda:
            acciones[o] = ("MOVER", dest, "")
        else:
            motivo = accion_v2 if isinstance(accion_v2, str) and accion_v2.startswith("QUITAR") else accion_v1
            acciones[o] = ("POR BORRAR", f"{POR_BORRAR}/{o}", str(motivo))
        if se_queda and isinstance(dest, str):
            destinos_planeados[clave(dest)] = dest

    # 3. Filas del plan cuyo archivo cambió de lugar: se buscan por nombre y tamaño entre lo que no está en el plan
    # (también entre las marcadas POR BORRAR: si la copia que se quedaba desapareció, otra igual toma su lugar)
    libres = defaultdict(list)
    for r, p in hoy.items():
        if r not in acciones or acciones[r][0] == "POR BORRAR":
            libres[clave(PurePosixPath(r).name)].append(r)
    manifiesto = pd.read_csv(local / "_manifiesto.csv")
    bytes_de = dict(zip(manifiesto.destino.map(clave), manifiesto.bytes))
    for o, se_queda, dest, motivo in sin_origen:
        cands = libres.get(clave(PurePosixPath(o).name), [])
        if se_queda and isinstance(dest, str):
            cands_tam = [c for c in cands if hoy[c].stat().st_size == bytes_de.get(clave(dest))] or cands
        else:
            cands_tam = cands
        if len(cands_tam) == 1 and (cands_tam[0] not in acciones or se_queda):
            nueva = cands_tam[0]
            if se_queda:
                acciones[nueva] = ("MOVER", dest, f"cambió de lugar (antes {o})")
            else:
                acciones[nueva] = ("POR BORRAR", f"{POR_BORRAR}/{nueva}", f"{motivo}; cambió de lugar (antes {o})")
        elif se_queda:  # ya no está en SharePoint (alguien lo borró): se puede volver a subir desde la copia local
            subir.append((o, "REVISAR", dest, "ya no está en SharePoint; propuesta: subirlo desde la copia local"))

    # 4. Lo que llegó después del plan
    #    4a. mapa de carpetas del libro a partir de cómo quedó el libro original
    dirs_libro = defaultdict(Counter)
    for o, (acc, dest, _) in acciones.items():
        if o.startswith(LIBRO_ORIG) and acc == "MOVER":
            sub = str(PurePosixPath(o[len(LIBRO_ORIG):]).parent).replace(".", "") if "/" in o[len(LIBRO_ORIG):] else ""
            dirs_libro[sub][str(PurePosixPath(dest).parent)] += 1
    carpetas_libro = dict(LIBRO_CARPETAS)
    for sub, c in dirs_libro.items():  # carpetas con el mismo nombre en origen y destino
        destino_dir, _ = c.most_common(1)[0]
        a, b = PurePosixPath(sub), PurePosixPath(destino_dir)
        while a.name and a.name == b.name:
            carpetas_libro.setdefault(str(a), str(b))
            a, b = a.parent, b.parent

    def destino_libro(sub):
        carpeta = str(PurePosixPath(sub).parent) if "/" in sub else ""
        if carpeta in dirs_libro:
            (d, n), total = dirs_libro[carpeta].most_common(1)[0], sum(dirs_libro[carpeta].values())
            return f"{d}/{PurePosixPath(sub).name}", (n / total < 0.8)
        a = PurePosixPath(carpeta)
        resto = []
        while str(a) not in carpetas_libro and str(a) != ".":
            resto.insert(0, a.name)
            a = a.parent
        base = carpetas_libro.get(str(a) if str(a) != "." else "", LIBRO)
        destino = "/".join([base, *resto, PurePosixPath(sub).name])
        return re.sub(r"/(?:" + "|".join(map(re.escape, CARPETAS_POR_TIPO)) + r")(?=/[^/]+$)", "", destino), False

    #    4b. índice de lo que ya queda en la estructura nueva (copia local) para comparar el libro de octubre
    por_nombre = defaultdict(list)
    for d in manifiesto.destino:
        por_nombre[clave(PurePosixPath(d).name)].append(d)
    destino_por_sha1 = dict(zip(manifiesto.sha1, manifiesto.destino))

    no_leidos = 0
    for r, p in sorted(hoy.items()):
        if r in acciones:
            continue
        nombre, ext = PurePosixPath(r).name, PurePosixPath(r).suffix.lower()
        if ext in BASURA or nombre.startswith(".849C"):
            acciones[r] = ("BORRAR", "", "archivo del sistema")
        elif r.startswith(LIBRO_TEMPORAL):
            acciones[r] = ("POR BORRAR", f"{POR_BORRAR}/{r}", f"copia de la carpeta {LIBRO_NUEVO} (misma subida, septiembre)")
        elif ext in IMAGEN or (ext == ".psd" and "Fotos practica" in r):
            acciones[r] = ("IMAGEN F3", f"{IMAGENES_F3}/{r}", "")
        elif (pref := max((k for k in NUEVOS if r.startswith(k)), key=len, default=None)) is not None:
            acciones[r] = ("MOVER", NUEVOS[pref] + r[len(pref):], "llegó después del plan")
        elif r.startswith(LIBRO_ORIG) and ext == ".psd":  # copias de las ilustraciones finales dentro de Fotos
            acciones[r] = ("POR BORRAR", f"{POR_BORRAR}/{r}", "copia de la ilustración en Ilustraciones finales")
        elif r.startswith(LIBRO_NUEVO):
            sub = r[len(LIBRO_NUEVO):]
            datos = leer(p)
            if datos is None:
                acciones[r] = ("REVISAR", "", "OneDrive no lo baja (ruta de 260 caracteres o más): se lee después de "
                                              "acortar su carpeta en el paso 0 de la F2")
                no_leidos += 1
                continue
            igual = None
            for cand in por_nombre.get(clave(nombre), []):
                if (rel := mismo_contenido(datos, leer(local / cand) or b"")):
                    igual = (cand, rel)
                    break
            if igual:
                acciones[r] = ("POR BORRAR", f"{POR_BORRAR}/{r}", f"{igual[1]} a {igual[0]}")
                continue
            dest, dudoso = destino_libro(sub)
            if clave(dest) in destinos_planeados or por_nombre.get(clave(nombre)):  # mismo nombre, otro contenido
                base = PurePosixPath(dest)
                dest = str(base.with_name(f"{base.stem} (subida oct-2026){base.suffix}"))
                motivo = "otro contenido con el mismo nombre: se conservan las dos versiones"
            else:
                motivo = "nuevo en la subida de octubre"
            acciones[r] = ("REVISAR" if dudoso else "MOVER", dest, motivo + ("; carpeta de origen repartida en varias, revisar destino" if dudoso else ""))
        else:  # sin regla: si es idéntico a algo que ya se queda, es una copia más
            datos = leer(p)
            h = hashlib.sha1(datos).hexdigest() if datos is not None else None
            if h in destino_por_sha1:
                acciones[r] = ("POR BORRAR", "", f"idéntico a {destino_por_sha1[h]}")
            else:
                acciones[r] = ("REVISAR", "", "sin regla")

    # 5. Árbol final: sin destinos repetidos y sin sueltos junto a carpetas (salvo excepciones). Los sueltos que
    #    queden junto a subcarpetas van a una carpeta por tipo de archivo, como en la estructura v2.
    filas = [{"ruta_actual": r, "accion": a, "destino": d, "motivo": m, "bytes": hoy[r].stat().st_size}
             for r, (a, d, m) in acciones.items()]
    filas += [{"ruta_actual": o, "accion": a, "destino": d, "motivo": m, "bytes": None} for o, a, d, m in subir]
    filas += [{"ruta_actual": "", "accion": "CREAR CARPETA", "destino": c, "motivo": "carpeta vacía de la estructura nueva",
               "bytes": None} for c in CARPETAS_VACIAS]
    df = pd.DataFrame(filas)
    for ruta, (accion, destino) in DECISIONES.items():
        sel = (df.ruta_actual == ruta) & (df.accion == "REVISAR")
        df.loc[sel, "accion"] = accion
        df.loc[sel, "motivo"] = df.loc[sel, "motivo"] + " | decidido por Remi (29-oct)"
        if destino:
            df.loc[sel, "destino"] = destino
    sel = df.accion.isin(["MOVER", "SUBIR", "REVISAR"]) & df.destino.astype(bool)
    df.loc[sel, "destino"] = df.loc[sel, "destino"].map(acortar)
    # Lo que no se queda no se mueve: sigue en su carpeta anterior (sin número) hasta la F3 y el borrado final.
    # Moverlo a "00. Por borrar/…" alargaba rutas que ya eran largas y duplicaba la sincronización.
    df.loc[df.accion == "POR BORRAR", "destino"] = ""
    df.loc[df.accion == "IMAGEN F3", "destino"] = df.loc[df.accion == "IMAGEN F3", "destino"].where(
        df.ruta_actual.str.startswith("VOLUMEN: "), "")
    df = df.sort_values(["accion", "destino", "ruta_actual"]).reset_index(drop=True)
    protegidas = ("07. Cartografia y SIG/SIG/", "07. Cartografia y SIG/Copia de SIG MAPA", "/AVES ENTREGAR 3 de nov/",
                  "/Carpeta Guia Aves online/", "/Pagina guardada/", "/Textos del sitio (retrabajo)/")
    finales_idx = df.index[df.accion.isin(["MOVER", "SUBIR", "REVISAR"]) & df.destino.astype(bool)]
    for _ in range(5):
        archivos_en, hijos = defaultdict(list), defaultdict(set)
        for i in finales_idx:
            p = PurePosixPath(df.at[i, "destino"])
            archivos_en[str(p.parent)].append(i)
            for a, b in zip(p.parents[1:], p.parents[:-1]):
                if str(a) != ".":
                    hijos[str(a)].add(b.name)
        mezcla = sorted(c for c in archivos_en if hijos.get(c) and "/" in c and not any(x in c + "/" for x in protegidas))
        for c in mezcla:
            for i in archivos_en[c]:
                p = PurePosixPath(df.at[i, "destino"])
                df.at[i, "destino"] = str(p.parent / carpeta_por_tipo(p.suffix) / p.name)
        if not mezcla:
            break
    finales = df.loc[finales_idx]
    repetidos = finales[finales.destino.map(clave).duplicated(keep=False)]

    resumen = df.groupby("accion").agg(archivos=("ruta_actual", "size"), GB=("bytes", lambda b: round(b.sum() / 1e9, 2)))
    print(resumen.to_string())
    print("destinos repetidos:", len(repetidos))
    # Windows (la carpeta sincronizada) se atora con rutas de 260 caracteres o más; SharePoint acepta hasta 400
    df["largo_en_pc"] = df.destino.map(lambda d: len(str(sp)) + 1 + len(d) if isinstance(d, str) and d else None)
    print("destinos con ruta de 260 caracteres o más en esta PC:", int((df.largo_en_pc >= 260).sum()),
          "| la más larga:", int(df.largo_en_pc.max()))
    if no_leidos:
        print(f"{no_leidos} archivos no se pudieron leer (rutas largas en OneDrive): se comparan en el paso 0 de la F2")
    with pd.ExcelWriter(SALIDA_PLAN) as w:
        resumen.to_excel(w, sheet_name="Resumen")
        df.to_excel(w, sheet_name="Acciones", index=False)
        df[df.accion == "REVISAR"].to_excel(w, sheet_name="Revisar", index=False)
        repetidos.to_excel(w, sheet_name="Destinos repetidos", index=False)
    print(f"Plan: {SALIDA_PLAN}")


if __name__ == "__main__":
    main()
