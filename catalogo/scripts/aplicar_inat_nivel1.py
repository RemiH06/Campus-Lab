# -*- coding: utf-8 -*-
"""Aplica la identificación de iNaturalist ITESO a fotos nuestras que son la MISMA foto que
una observación de iNaturalist (Cruce_fotos_iNaturalist.xlsx, cruce_fotos_inat.py), solo en
los casos más seguros ("nivel 1", acordado con Remi el 13-oct):

  - todas las fotos de la unidad (grupo de espécimen completo, o la foto suelta si no tiene
    grupo) tienen pareja en iNaturalist, y todas dicen la misma especie;
  - grado de investigación, 2+ acuerdos y 0 desacuerdos en cada observación;
  - mismo reino que lo nuestro (si no, es foto con dos sujetos, no error);
  - no es solo un cambio de nombre (si GBIF dice que nuestro nombre es sinónimo del de
    iNaturalist, la especie es la misma y no se toca aquí);
  - fuera de orquídeas/suculentas y de los grupos enviados a especialistas;
  - nunca pisa un rechazo manual previo de ese mismo nombre en esa foto.

Todo lo demás va a la hoja "Nivel 2" del plan, para revisar a ojo.

Al aplicar: confirma la especie de iNaturalist (misma lógica que revision_grupos, 8046),
registra como rechazado el nombre anterior (para que ningún script automático, como la
resolución por nombre de carpeta, lo vuelva a poner) y sincroniza especimen_embeddings.genero.

Uso: python aplicar_inat_nivel1.py   (plan en seco: salida/inaturalist_iteso/Plan_iNat_nivel1.xlsx)
     cambiar EJECUTAR_REAL a True después de revisar el plan, y volver a correr.
"""
import glob
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).parent))
from cruce_fotos_inat import binomio  # noqa: E402

EJECUTAR_REAL = False
# Fuera del nivel 1 por decisión de Remi (13-oct): Taraxacum campylodes/officinale es un tema de
# nomenclatura (GBIF acepta los dos), se resuelve al elegir una sola fuente de nombres.
EXCLUIR_GRUPOS = {557}

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # catalogo/, para importar comun/
from comun.rutas import RUTA_BD, RUTA_CONFIG, SALIDA  # noqa: E402
CARPETA = SALIDA / "inaturalist_iteso"
ORQ_SUC = {  # mismo conjunto que ORQUIDEAS_SUCULENTAS en revision_grupos/backend.py
    "laelia", "bletia", "habenaria", "spathoglottis", "epidendrum", "scaphyglottis", "rhynchostele",
    "malaxis", "platystele", "arundina", "sacoila", "cyrtopodium", "rodriguezia", "myrmecophila",
    "paphiopedilum", "phaius", "dendrobium", "cymbidium", "bolusiella", "clowesia", "stanhopea",
    "brassavola", "oncidium", "encyclia", "mormodes", "trichocentrum", "alatiglossum", "prosthechea",
    "austrocylindropuntia", "kroenleinia", "cotyledon", "quetzalcoatlia", "aeonium", "echeveria",
    "mammillaria", "astrophytum", "echinopsis", "ferocactus", "melocactus", "copiapoa", "frailea",
    "haworthiopsis", "sedum", "graptopetalum", "opuntia",
}
RANGOS = {"species", "subspecies", "variety", "form"}
REINO_ICONICO = {"Plantae": "Plantae", "Fungi": "Fungi"}  # lo demás (Aves, Insecta...) es Animalia


def gbif(nombre, ruta="species/match"):
    time.sleep(0.2)
    with urllib.request.urlopen(f"https://api.gbif.org/v1/{ruta}?" + urllib.parse.urlencode({"name": nombre}), timeout=30) as r:
        return json.load(r)


def solo_nombre(nuestro, suyo):
    """True si GBIF considera que nuestro nombre y el de iNat son la misma especie."""
    a, b = gbif(nuestro), gbif(suyo)
    clave = lambda m: m.get("acceptedUsageKey") or m.get("usageKey")  # noqa: E731
    return m_ok(a) and m_ok(b) and (clave(a) == clave(b) or binomio(a.get("species")) == binomio(b.get("species")))


def m_ok(m):
    return m.get("matchType") == "EXACT"


def nombre_especie(taxon):
    """'Setophaga coronata auduboni' -> 'Setophaga coronata' (se confirma a nivel especie)."""
    return " ".join(taxon.split(" ")[:2])


def main():
    c = sqlite3.connect(RUTA_BD)
    ws = openpyxl.load_workbook(CARPETA / "Cruce_fotos_iNaturalist.xlsx")["Pares"]
    enc = [x.value for x in ws[1]]
    pares = [dict(zip(enc, r)) for r in ws.iter_rows(min_row=2, values_only=True)]

    expertos = {}
    for f in glob.glob(str(SALIDA / "revision_expertos" / "Revision_*.xlsx")):
        h = openpyxl.load_workbook(f).worksheets[1]
        cab = [x.value for x in h[1]]
        for r in h.iter_rows(min_row=2, values_only=True):
            if r[cab.index("grupo_id")]:
                expertos[r[cab.index("grupo_id")]] = Path(f).stem.replace("Revision_", "")

    grupo_de = dict(c.execute("SELECT foto_id, grupo_id FROM especimen_grupos_confirmados"))
    miembros = defaultdict(list)
    for f, g in grupo_de.items():
        miembros[g].append(f)
    reino_genero = {g.lower(): r for g, r in c.execute("SELECT genero, reino FROM genero_taxonomia") if g}
    iconico = dict(c.execute("SELECT taxon_nombre, reino_iconico FROM inat_observaciones"))
    rechazos = {(f, n) for f, n in c.execute(
        "SELECT foto_id, especie_sugerida FROM identificaciones_revisadas WHERE decision='rechazada'")}

    # votos por foto: solo pares de categorías 2, 3 y 4 (desacuerdo o sin especie nuestra)
    votos = defaultdict(list)
    for p in pares:
        if p["categoria"][0] in "1234" and p["inat_rango"] in RANGOS:
            votos[p["foto_id"]].append(p)
    candidatas = {p["foto_id"] for p in pares if p["categoria"][0] in "234"}

    unidades = {}
    for f in candidatas:
        g = grupo_de.get(f)
        unidades[("grupo", g) if g else ("foto", f)] = miembros[g] if g else [f]

    nivel1, nivel2 = [], []
    for (tipo, uid), fotos in sorted(unidades.items(), key=lambda x: (x[0][0], x[0][1])):
        nuestra = {}
        for f in fotos:
            fila = c.execute("""SELECT f.estado, e.nombre_cientifico FROM fotos f
                                LEFT JOIN especies e ON e.id=f.especie_id WHERE f.id=?""", (f,)).fetchone()
            nuestra[f] = fila
        nombres_nuestros = sorted({n for _, n in nuestra.values() if n})
        vs = [v for f in fotos for v in votos.get(f, [])]
        propuestas = sorted({nombre_especie(v["inat_taxon"]) for v in vs})
        motivo = []
        if not vs:
            motivo.append("sin observación de iNat a nivel especie")
        if len(propuestas) > 1:
            motivo.append("iNat dice especies distintas dentro de la unidad")
        sin_par = [f for f in fotos if not votos.get(f)]
        if sin_par:
            motivo.append(f"{len(sin_par)} de {len(fotos)} fotos sin pareja en iNat")
        if any(v["inat_grado"] != "research" or (v["inat_acuerdos"] or 0) < 2 or (v["inat_desacuerdos"] or 0) > 0 for v in vs):
            motivo.append("alguna observación sin investigación, con <2 acuerdos o con desacuerdo")
        propuesta = propuestas[0] if len(propuestas) == 1 else None
        if propuesta and binomio(propuesta) in {binomio(n) for n in nombres_nuestros} and len(nombres_nuestros) == 1:
            continue  # ya coincide (p. ej. otra foto del grupo era la del desacuerdo por sinónimo)
        genero = (propuesta or (nombres_nuestros[0] if nombres_nuestros else "")).split(" ")[0].lower()
        if genero in ORQ_SUC or any(n.split(" ")[0].lower() in ORQ_SUC for n in nombres_nuestros):
            motivo.append("orquídea o suculenta (va con especialistas)")
        if tipo == "grupo" and uid in EXCLUIR_GRUPOS:
            motivo.append("excluido a mano: decisión de nomenclatura pendiente")
        if tipo == "grupo" and uid in expertos:
            motivo.append(f"grupo en el Excel de especialistas ({expertos[uid]})")
        r_i = REINO_ICONICO.get(iconico.get(vs[0]["inat_taxon"]), "Animalia") if vs else None
        for n in nombres_nuestros:
            r_n = reino_genero.get(n.split(" ")[0].lower())
            if r_n is None:
                motivo.append(f"reino de {n.split(' ')[0]} desconocido (¿doble sujeto?)")
            elif r_i and r_n != r_i:
                motivo.append("reino distinto: doble sujeto, no error")
        if propuesta and nombres_nuestros and not motivo and any(solo_nombre(n, propuesta) for n in nombres_nuestros):
            motivo.append("solo cambio de nombre (GBIF los considera la misma especie)")

        bloqueadas = [f for f in fotos if propuesta and (f, propuesta) in rechazos]
        fila = [tipo, uid, len(fotos), ", ".join(str(f) for f in sorted(fotos)),
                " / ".join(nombres_nuestros) or "(sin especie)",
                " / ".join(sorted({e for e, _ in nuestra.values()})),
                propuesta or " / ".join(propuestas),
                min((v["inat_acuerdos"] or 0) for v in vs) if vs else None,
                " ".join(sorted({v["observacion"] for v in vs})),
                f"http://localhost:8046/?grupos={uid}" if tipo == "grupo" else f"http://localhost:8044/?id={uid}"]
        if motivo:
            nivel2.append(fila + ["; ".join(motivo)])
        else:
            nivel1.append(fila + [", ".join(map(str, bloqueadas))])

    cab = ["unidad", "id", "n_fotos", "fotos", "nuestra", "estado", "iNat", "acuerdos_min", "observaciones", "revisar"]
    wb = openpyxl.Workbook()
    h1 = wb.active
    h1.title = "Nivel 1 (aplicar)"
    h1.append(cab + ["bloqueadas_por_rechazo_previo"])
    for f in nivel1:
        h1.append(f)
    h2 = wb.create_sheet("Nivel 2 (a ojo)")
    h2.append(cab + ["por_que_no_es_nivel_1"])
    for f in nivel2:
        h2.append(f)
    for h in (h1, h2):
        for celda in h[1]:
            celda.font = Font(bold=True)
        h.freeze_panes = "A2"
        h.auto_filter.ref = h.dimensions
        for col, ancho in zip("ABCDEFGHIJK", [7, 7, 8, 28, 30, 22, 28, 9, 50, 34, 60]):
            h.column_dimensions[col].width = ancho
    destino = CARPETA / "Plan_iNat_nivel1.xlsx"
    wb.save(destino)
    print(f"Plan: {destino}")
    print(f"Nivel 1: {len(nivel1)} unidades, {sum(f[2] for f in nivel1)} fotos")
    for f in nivel1:
        print(f"   {f[0]} {f[1]}: {f[4]} -> {f[6]} ({f[2]} fotos, {f[7]} acuerdos)" + (f" BLOQUEADAS {f[10]}" if f[10] else ""))
    print(f"Nivel 2: {len(nivel2)} unidades")

    if not EJECUTAR_REAL:
        print("EJECUTAR_REAL = False: no se cambió nada.")
        return
    revisor = json.loads(RUTA_CONFIG.read_text(encoding="utf-8")).get("nombre_revisor", "Remi")
    ahora = datetime.now().isoformat(sep=" ", timespec="seconds")
    total = 0
    for f_plan in nivel1:
        nombre = f_plan[6]
        fila = c.execute("SELECT id FROM especies WHERE nombre_cientifico=?", (nombre,)).fetchone()
        especie_id = fila[0] if fila else c.execute(
            "INSERT INTO especies (nombre_cientifico, sugerido_por, fuente_validacion) VALUES (?,?,?)",
            (nombre, "iNaturalist", "iNaturalist ITESO, grado investigación, misma foto (13-oct)")).lastrowid
        for foto in map(int, f_plan[3].split(", ")):
            if (foto, nombre) in rechazos:
                continue
            anterior = c.execute("""SELECT e.nombre_cientifico FROM fotos f JOIN especies e ON e.id=f.especie_id
                                    WHERE f.id=?""", (foto,)).fetchone()
            if anterior and anterior[0] != nombre:
                c.execute("INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, decision, revisor, fecha) VALUES (?,?,?,?,?)",
                          (foto, anterior[0], "rechazada", f"{revisor} (vía iNaturalist)", ahora))
            c.execute("UPDATE fotos SET estado='usable', especie_id=? WHERE id=?", (especie_id, foto))
            c.execute("INSERT INTO identificaciones_revisadas (foto_id, especie_sugerida, decision, revisor, fecha) VALUES (?,?,?,?,?)",
                      (foto, nombre, "confirmada (iNaturalist)", revisor, ahora))
            c.execute("UPDATE especimen_embeddings SET genero=? WHERE foto_id=?", (nombre.split(" ")[0], foto))
            c.commit()  # por fila: otras herramientas leen la BD a la vez
            total += 1
    print(f"Aplicado: {total} fotos.")


if __name__ == "__main__":
    main()
