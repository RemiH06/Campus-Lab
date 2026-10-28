"""Hojas de campo del inventario de árboles 2026 (puerto 8049), para el celular vía Tailscale.

Corre en Pixilate dentro de Docker (WSL), solo en 127.0.0.1; `tailscale serve --https=8049` lo publica
a la tailnet. Datos de solo lectura en datos_campo.json (lo arma preparar.py en Aerilate). Marcas en
un archivo de solo agregar (una línea JSON por marca, gana la más reciente por placa). El celular
guarda su propia cola y la sube cuando hay conexión, así que la página funciona sin señal.

Configuración por entorno:
  HOJAS_CAMPO_DATOS     ruta de datos_campo.json
  HOJAS_CAMPO_MARCAS    ruta de marcas.jsonl
  HOJAS_CAMPO_USUARIOS  logins de Tailscale permitidos, separados por coma (vacío = nadie)
  HOJAS_CAMPO_LOCAL=1   solo para probar en local sin Tailscale
"""
import csv
import io
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

AQUI = Path(__file__).resolve().parent
STATIC = AQUI / "static"
DATOS_RUTA = Path(os.environ.get("HOJAS_CAMPO_DATOS", AQUI / "datos_campo.json"))
MARCAS = Path(os.environ.get("HOJAS_CAMPO_MARCAS", AQUI / "marcas.jsonl"))
USUARIOS = {u.strip() for u in os.environ.get("HOJAS_CAMPO_USUARIOS", "").split(",") if u.strip()}
LOCAL = os.environ.get("HOJAS_CAMPO_LOCAL") == "1"

DATOS = json.loads(DATOS_RUTA.read_text(encoding="utf-8"))
POR_PLACA = {a["placa"]: a | {"jardin": z["nombre"]} for z in DATOS["jardines"] for a in z["arboles"]}
candado = threading.Lock()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def identidad_y_cabeceras(request: Request, call_next):
    # `tailscale serve` pone esta cabecera con el usuario de quien pide; sin ella, la petición no vino por Tailscale
    usuario = request.headers.get("tailscale-user-login", "")
    if request.url.path != "/salud" and not LOCAL and usuario not in USUARIOS:
        return JSONResponse({"error": "Solo por Tailscale"}, status_code=403)
    request.state.usuario = usuario or "local"
    r = await call_next(request)
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["Referrer-Policy"] = "no-referrer"
    r.headers["Strict-Transport-Security"] = "max-age=31536000"
    r.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' https://fonts.bunny.net; font-src https://fonts.bunny.net; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
    return r


class Marca(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9-]{8,64}$")
    placa: str = Field(pattern=r"^[A-Za-z0-9-]{1,24}$")
    jardin: str = Field(max_length=80)
    estado: Literal["revisado", "no_esta", "otra", "nuevo", "borrar"]
    nota: str = Field("", max_length=500)
    especie_real: str = Field("", max_length=120)
    foto_swmaps: str = Field("", max_length=40)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    precision_m: float | None = Field(None, ge=0, le=100000)
    ts: str = Field(max_length=40)


class Lote(BaseModel):
    marcas: list[Marca] = Field(max_length=2000)


def leer_marcas():
    if not MARCAS.exists():
        return []
    return [json.loads(l) for l in MARCAS.read_text(encoding="utf-8").splitlines() if l.strip()]


def vigentes():
    """La marca más reciente (por ts del celular) de cada placa; 'borrar' la quita."""
    ultima = {}
    for m in leer_marcas():
        if m["placa"] not in ultima or m["ts"] >= ultima[m["placa"]]["ts"]:
            ultima[m["placa"]] = m
    return [m for m in ultima.values() if m["estado"] != "borrar"]


@app.get("/salud")
def salud():
    return {"ok": True}


@app.get("/api/datos")
def datos():
    return DATOS


@app.get("/api/marcas")
def marcas():
    return {"marcas": vigentes()}


@app.post("/api/marcas")
def subir(lote: Lote, request: Request):
    for m in lote.marcas:
        if m.estado not in ("nuevo", "borrar") and m.placa not in POR_PLACA:  # los nuevos traen placa propia
            raise HTTPException(422, f"Placa desconocida: {m.placa}")
    with candado:
        vistos = {m["id"] for m in leer_marcas()}  # idempotente: reenviar la cola no duplica
        MARCAS.parent.mkdir(parents=True, exist_ok=True)
        nuevas = 0
        with MARCAS.open("a", encoding="utf-8") as f:
            for m in lote.marcas:
                if m.id in vistos:
                    continue
                fila = m.model_dump() | {"usuario": request.state.usuario,
                                         "recibido": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                vistos.add(m.id)
                nuevas += 1
            f.flush()
            os.fsync(f.fileno())
    return {"recibidas": [m.id for m in lote.marcas], "nuevas": nuevas}


@app.get("/api/exportar.csv")
def exportar():
    seguro = lambda v: "'" + v if isinstance(v, str) and v[:1] in "=+-@" else v  # noqa: E731  (fórmulas en Excel)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["placa", "jardin", "estado", "especie_inventario", "especie_real", "nota", "foto_swmaps",
                "lat", "lon", "precision_m", "fecha_marca", "usuario"])
    for m in sorted(vigentes(), key=lambda m: (m["jardin"], m["placa"])):
        a = POR_PLACA.get(m["placa"], {})
        w.writerow([seguro(x) for x in [m["placa"], m["jardin"], m["estado"], a.get("cien", ""), m["especie_real"],
                                        m["nota"], m["foto_swmaps"], m["lat"], m["lon"], m["precision_m"], m["ts"],
                                        m["usuario"]]])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=recorrido_2026_marcas.csv"})


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/{archivo}")
def estatico(archivo: str):
    permitidos = {"app.js": "text/javascript", "app.css": "text/css", "sw.js": "text/javascript",
                  "manifest.webmanifest": "application/manifest+json", "icono.svg": "image/svg+xml"}
    if archivo not in permitidos:
        raise HTTPException(404)
    return FileResponse(STATIC / archivo, media_type=permitidos[archivo], headers={"Cache-Control": "no-cache"})
