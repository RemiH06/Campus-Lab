/* ══════════════════════════════════════════════════════════════════════════════════════════════════════
   Datos vivos del mapa 3D: lo que cambia y edita gente sin formación técnica, fuera del JSON del territorio.
   · Árboles: inventario-arboles.csv (Documentos y Medios), editado en Excel. Una fila por árbol con placa.
   · Observaciones: se piden a iNaturalist (API abierta, sin cuenta) por el rectángulo del territorio.
   El JSON del territorio solo trae la geografía (edificios, calles, relieve), que casi nunca cambia.
   ══════════════════════════════════════════════════════════════════════════════════════════════════════ */

/* ── CSV tolerante con lo que hace Excel: separador ";" o "," o tabulador, UTF-8 o ANSI (Windows-1252),
   comillas dobles, saltos de línea dentro de una celda, coma decimal. Encabezados sin acentos ni mayúsculas:
   "Nombre científico" y "nombre_cientifico" son la misma columna ── */
const clave = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

export function leerCSV(texto) {
  texto = texto.replace(/^﻿/, "");
  const primera = texto.slice(0, texto.indexOf("\n") >>> 0);
  const sep = [";", ",", "\t"].map((s) => [s, primera.split(s).length]).sort((a, b) => b[1] - a[1])[0][0];
  const filas = []; let fila = [], celda = "", comillas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (comillas) {
      if (c === '"' && texto[i + 1] === '"') { celda += '"'; i++; } else if (c === '"') comillas = false; else celda += c;
    } else if (c === '"') comillas = true;
    else if (c === sep) { fila.push(celda); celda = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && texto[i + 1] === "\n") i++; fila.push(celda); filas.push(fila); fila = []; celda = ""; }
    else celda += c;
  }
  if (celda || fila.length) { fila.push(celda); filas.push(fila); }
  const cab = (filas.shift() || []).map(clave);
  return filas.filter((f) => f.some((v) => v.trim())).map((f, n) => {
    const o = { _fila: n + 2 }; cab.forEach((k, j) => { if (k) o[k] = (f[j] || "").trim(); }); return o;
  });
}

export async function bajarCSV(url) {
  const r = await fetch(url, { credentials: "same-origin" });
  if (!r.ok || r.redirected) throw new Error("no se encontró " + url);
  const b = await r.arrayBuffer();
  let t; try { t = new TextDecoder("utf-8", { fatal: true }).decode(b); } catch (e) { t = new TextDecoder("windows-1252").decode(b); } /* "CSV" normal de Excel */
  return leerCSV(t);
}

const num = (v) => { v = String(v || "").trim().replace(/^(-?\d+),(\d+)$/, "$1.$2"); const n = parseFloat(v); return isFinite(n) ? n : null; };
export const slug = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

/* Misma proyección que web/scripts/generar_territorios_3d.py: metros desde el origen del territorio (x al este, z al sur) */
export function proyeccion(origen) {
  const [lat0, lon0] = origen, kx = Math.cos(lat0 * Math.PI / 180) * 111320;
  return { xz: (lat, lon) => [+((lon - lon0) * kx).toFixed(1), +((lat0 - lat) * 110574).toFixed(1)], latlon: (x, z) => [lat0 - z / 110574, lon0 + x / kx] };
}
const dentro = (x, z, e) => e[0] <= x && x <= e[2] && e[1] <= z && z <= e[3];

/* Árboles del territorio: [placa, x, z, alto, copa, especie] (especie = índice en E). Las filas que no sirven
   (sin placa, sin coordenada, fuera del territorio) se cuentan en avisos para que quien edita sepa cuáles corregir */
export function arbolesDe(filas, D) {
  const P = proyeccion(D.origen), E = [], idx = new Map(), arb = [], malas = [], vistas = new Set();
  for (const f of filas) {
    if ((f.territorio || "campus").toLowerCase() !== D.id) continue;
    if (/derrib|muert|no encontr/i.test(f.estado || "")) continue;
    const placa = (f.placa || "").replace(/\D/g, ""), lat = num(f.latitud), lon = num(f.longitud);
    if (!placa || lat == null || lon == null) { malas.push(f._fila); continue; }
    const [x, z] = P.xz(lat, lon);
    if (!dentro(x, z, D.ext)) { malas.push(f._fila); continue; }
    if (vistas.has(placa)) { malas.push(f._fila); continue; } vistas.add(placa);
    const sci = f.nombre_cientifico || "", com = f.nombre_comun || "", k = (sci || com).toLowerCase();
    let ei = -1;
    if (k) { if (!idx.has(k)) { idx.set(k, E.length); E.push({ id: sci ? slug(sci) : null, sci, com }); } ei = idx.get(k); }
    const alto = Math.min(num(f.altura_m) || 6, 40), copa = Math.min(num(f.copa_m) || alto * 0.6, 30);
    arb.push([+placa, x, z, +alto.toFixed(1), +copa.toFixed(1), ei]);
  }
  return { arb, E, malas };
}

/* ── Observaciones de iNaturalist dentro del rectángulo del territorio. Se piden por páginas de 200 (tres a la vez)
   con solo los campos que se dibujan, y se guardan 24 h en el navegador para no repetir la descarga ── */
const GRUPOS = { Plantae: "planta", Aves: "ave", Insecta: "insecto", Arachnida: "insecto", Fungi: "hongo", Mammalia: "mamifero", Reptilia: "reptil", Amphibia: "reptil" };
const CAMPOS = "(id:!t,location:!t,taxon:(name:!t,preferred_common_name:!t,iconic_taxon_name:!t))";

export async function observaciones(D) {
  const llave = "cl-inat-" + D.id, P = proyeccion(D.origen);
  try { const c = JSON.parse(localStorage.getItem(llave)); if (c && Date.now() - c.t < 864e5) return c.obs; } catch (e) { /* sin caché */ }
  const [n, w] = P.latlon(D.ext[0], D.ext[1]), [s, e] = P.latlon(D.ext[2], D.ext[3]);
  const pagina = (p) => fetch("https://api.inaturalist.org/v2/observations?" + new URLSearchParams({
    nelat: n, nelng: e, swlat: s, swlng: w, per_page: 200, page: p, order_by: "id", order: "asc", locale: "es-MX", fields: CAMPOS
  })).then((r) => { if (!r.ok) throw new Error("iNaturalist " + r.status); return r.json(); });
  const r1 = await pagina(1), total = Math.min(Math.ceil(r1.total_results / 200), 50), res = [r1];
  for (let p = 2; p <= total; p += 3) res.push(...await Promise.all([p, p + 1, p + 2].filter((q) => q <= total).map(pagina)));
  const obs = [];
  res.forEach((r) => r.results.forEach((o) => {
    if (!o.location) return;
    const [lat, lon] = o.location.split(",").map(Number), [x, z] = P.xz(lat, lon), t = o.taxon || {};
    if (dentro(x, z, D.ext)) obs.push([x, z, GRUPOS[t.iconic_taxon_name] || "otro", t.name || "", o.id, t.preferred_common_name || ""]);
  }));
  try { localStorage.setItem(llave, JSON.stringify({ t: Date.now(), obs })); } catch (e) { /* lleno o bloqueado: no pasa nada */ }
  return obs;
}
