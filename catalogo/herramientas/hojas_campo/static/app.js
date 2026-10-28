// Hojas de campo: funciona sin señal. Cada marca entra a una cola local y se sube cuando hay conexión;
// el servidor ignora las que ya tiene (por id), así que reenviar nunca duplica.
"use strict";
const $ = (s) => document.querySelector(s);
const leer = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
const guardar = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
const nuevoId = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
const sinAcentos = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const ESTADO = { revisado: "Revisado", no_esta: "No está", otra: "Otra especie", nuevo: "Árbol nuevo" };
const CLAVIGERO = "0";  // lejos del campus: fuera del mapa de "Todas"

let D = null, ARB = [], ZONA = new Map();   // árboles planos con su zona, zonas por id
let servidor = leer("hc_servidor", []);     // últimas marcas confirmadas por el servidor
let cola = leer("hc_cola", []);             // marcas que aún no sube el servidor
let filtro = leer("hc_filtro", "pendientes");
let abierto = null, ultimo = null, gpsActual = null, ruta = { v: "zonas", p: new URLSearchParams() };
// Lo marcado en esta vista sigue visible aunque el filtro sea "Pendientes": si la fila desapareciera,
// la de abajo subiría bajo el dedo y un doble toque marcaría un árbol sin revisarlo.
const recientes = new Set();

function indexar(datos) {
  D = datos; ARB = []; ZONA = new Map();
  D.jardines.forEach((z) => { ZONA.set(z.id, z); z.arboles.forEach((a, i) => ARB.push({ ...a, zona: z.id, n: i + 1 })); });
}
const llaveEspecie = (a) => a.cien || "Sin nombre científico: " + (a.comun || "sin nombre");
const zonaNombre = (a) => ZONA.get(a.zona).nombre;

// ---------- Marcas vigentes: servidor + cola, gana la más reciente por placa ----------
function vigentes() {
  const m = new Map();
  for (const x of [...servidor, ...cola]) { const p = m.get(x.placa); if (!p || x.ts >= p.ts) m.set(x.placa, x); }
  for (const [k, v] of m) if (v.estado === "borrar") m.delete(k);
  return m;
}
function marcar(datos) {
  const m = { id: nuevoId(), nota: "", especie_real: "", foto_swmaps: "", lat: null, lon: null, precision_m: null, ...datos, ts: new Date().toISOString() };
  recientes.add(m.placa); cola.push(m); guardar("hc_cola", cola); pintar(); programarSync();
  return m;
}

// ---------- Sincronización ----------
let enCurso = false, temporizador = null;
const programarSync = () => { clearTimeout(temporizador); temporizador = setTimeout(sincronizar, 1500); };
async function sincronizar() {
  if (enCurso) return; enCurso = true; pintarSync("Subiendo…");
  try {
    if (cola.length) {
      const r = await fetch("/api/marcas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ marcas: cola }) });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const ok = new Set((await r.json()).recibidas);
      cola = cola.filter((m) => !ok.has(m.id)); guardar("hc_cola", cola);
    }
    const r = await fetch("/api/marcas", { cache: "no-store" });
    if (r.ok) { servidor = (await r.json()).marcas; guardar("hc_servidor", servidor); }
    pintarSync();
  } catch (e) { pintarSync(null, true); }
  enCurso = false; pintar();
}
function pintarSync(texto, fallo) {
  const b = $("#sync");
  b.classList.toggle("pendiente", cola.length > 0);
  b.textContent = texto || (cola.length ? `${cola.length} sin subir${fallo ? " · sin conexión" : ""}` : "Todo guardado");
}
$("#sync").onclick = sincronizar;
addEventListener("online", sincronizar);
setInterval(() => { if (document.visibilityState === "visible") sincronizar(); }, 60000);

// ---------- Utilidades de vista ----------
function contar(lista, m) {
  let hechos = 0, exc = 0;
  for (const a of lista) { const x = m.get(a.placa); if (x) { hechos++; if (x.estado !== "revisado") exc++; } }
  return { hechos, exc, total: lista.length };
}
function tarjeta(href, titulo, sub, pct, detalle) {
  const li = document.createElement("li"), a = document.createElement("a");
  a.href = href;
  const b = document.createElement("b"); b.textContent = titulo; a.append(b);
  if (sub) { const i = document.createElement("i"); i.textContent = sub; a.append(i); }
  const s = document.createElement("span"); s.textContent = detalle; a.append(s);
  const barra = document.createElement("div"); barra.className = "barra-prog"; barra.setAttribute("aria-hidden", "true");
  const relleno = document.createElement("i"); relleno.style.width = pct + "%";  // por CSSOM: la CSP no permite style en línea
  barra.append(relleno); a.append(barra);
  li.append(a); return li;
}
function llenarZonas(sel, valor, conTodas) {
  sel.textContent = "";
  if (conTodas) sel.append(new Option("Todas las zonas", ""));
  for (const z of D.jardines) sel.append(new Option(z.nombre + (z.arboles.length ? ` (${z.arboles.length})` : " (sin inventario)"), z.id));
  sel.value = valor || "";
}
const enlace = (v, p) => {
  const q = new URLSearchParams(Object.entries(p).filter(([, x]) => x)).toString();
  return "#/" + v + (q ? "?" + q : "");
};

// ---------- Vista: zonas ----------
function pintarZonas(m) {
  const ul = $("#zonas"); ul.textContent = "";
  for (const z of D.jardines) {
    const lista = ARB.filter((a) => a.zona === z.id), c = contar(lista, m);
    const nuevos = [...m.values()].filter((x) => x.estado === "nuevo" && x.jardin === z.nombre).length;
    const pct = c.total ? Math.round(c.hechos / c.total * 100) : 0;
    ul.append(tarjeta(enlace("arboles", { zona: z.id }), z.nombre, "", pct, c.total
      ? `${c.hechos} de ${c.total} revisados (${pct} %)` + (c.exc ? ` · ${c.exc} con excepción` : "") + (nuevos ? ` · ${nuevos} nuevos` : "")
      : `Sin inventario: agrega lo que encuentres · ${nuevos} nuevos`));
  }
}

// ---------- Vista: especies ----------
function pintarEspecies(m) {
  const zona = ruta.p.get("zona") || "";
  llenarZonas($("#e-zona"), zona, true);
  const q = sinAcentos($("#e-buscar").value.trim());
  const grupos = new Map();
  for (const a of ARB) {
    if (zona && a.zona !== zona) continue;
    const k = llaveEspecie(a);
    if (!grupos.has(k)) grupos.set(k, { k, arboles: [], comunes: new Map() });
    const g = grupos.get(k); g.arboles.push(a); g.comunes.set(a.comun, (g.comunes.get(a.comun) || 0) + 1);
  }
  const lista = [...grupos.values()].map((g) => ({ ...g, comun: [...g.comunes].sort((x, y) => y[1] - x[1])[0][0] }))
    .filter((g) => !q || sinAcentos(g.k + " " + [...g.comunes.keys()].join(" ")).includes(q))
    .sort((x, y) => y.arboles.length - x.arboles.length || x.k.localeCompare(y.k));
  const tot = contar(lista.flatMap((g) => g.arboles), m);
  $("#e-resumen").textContent = `${lista.length} especies · ${tot.hechos} de ${tot.total} árboles revisados`;
  const ul = $("#especies"); ul.textContent = "";
  for (const g of lista) {
    const c = contar(g.arboles, m), pct = Math.round(c.hechos / c.total * 100);
    const zonas = new Set(g.arboles.map((a) => a.zona)).size;
    ul.append(tarjeta(enlace("arboles", { zona, especie: g.k }), g.comun || g.k, g.k.startsWith("Sin nombre") ? "" : g.k, pct,
      `${c.total} ${c.total === 1 ? "árbol" : "árboles"} · ${c.hechos} revisados` + (c.exc ? ` · ${c.exc} con excepción` : "") + (!zona && zonas > 1 ? ` · en ${zonas} zonas` : "")));
  }
}
$("#e-zona").onchange = () => { location.hash = enlace("especies", { zona: $("#e-zona").value }); };
$("#e-buscar").oninput = () => pintar();

// ---------- Vista: árboles ----------
function filaArbol(a, x, verZona) {
  const li = document.createElement("li");
  li.className = "arbol" + (x ? " " + x.estado : ""); li.id = "p-" + a.placa;
  const t = document.createElement("button"); t.type = "button"; t.className = "toque";
  t.setAttribute("aria-label", `Placa ${a.placa}, ${a.comun || "sin nombre"}. ${x ? ESTADO[x.estado] : "Pendiente"}. Tocar para ${x && x.estado === "revisado" ? "quitar revisado" : "marcar revisado"}`);
  t.innerHTML = `<span class="n"></span><span class="placa"></span><span class="nom"><b></b><i></i></span>`;
  t.querySelector(".n").textContent = a.nuevo ? "+" : a.n;
  t.querySelector(".placa").textContent = a.placa;
  t.querySelector("b").textContent = a.comun || "Sin nombre en inventario";
  t.querySelector("i").textContent = a.cien || "";
  const nom = t.querySelector(".nom");
  const extra = (txt, cls) => { const s = document.createElement("small"); s.textContent = txt; if (cls) s.className = cls; nom.append(s); };
  if (x) { const s = document.createElement("span"); s.className = "estado-txt"; s.textContent = ESTADO[x.estado] + (x.especie_real && !a.nuevo ? `: ${x.especie_real}` : "") + (x.nota ? ` · ${x.nota}` : ""); nom.append(s); }
  if (verZona) extra(a.nuevo ? x.jardin : zonaNombre(a), "previo");
  if (a.previo) extra(a.previo, "previo");
  if (a.aviso) extra(a.aviso);
  t.onclick = () => {
    if (a.nuevo) return abrirOpciones(a);
    if (x && x.estado === "revisado") { ultimo = marcar({ placa: a.placa, jardin: zonaNombre(a), estado: "borrar" }); avisar(`${a.placa}: sin marca`); }
    else if (x) abrirOpciones(a);  // ya tiene excepción: no la pisa un toque
    else { ultimo = marcar({ placa: a.placa, jardin: zonaNombre(a), estado: "revisado" }); avisar(`${a.placa} revisado`); }
  };
  const mas = document.createElement("button"); mas.type = "button"; mas.className = "mas"; mas.textContent = "Más";
  mas.setAttribute("aria-label", `Más opciones para la placa ${a.placa}`);
  mas.onclick = () => abrirOpciones(a);
  li.append(t, mas);
  return li;
}

function pintarArboles(m) {
  const zona = ruta.p.get("zona") || "", especie = ruta.p.get("especie") || "";
  llenarZonas($("#f-zona"), zona, true);
  const enZona = ARB.filter((a) => !zona || a.zona === zona);
  const selE = $("#f-especie"); selE.textContent = ""; selE.append(new Option("Todas las especies", ""));
  const cuenta = new Map(); for (const a of enZona) cuenta.set(llaveEspecie(a), (cuenta.get(llaveEspecie(a)) || 0) + 1);
  for (const [k, n] of [...cuenta].sort((x, y) => x[0].localeCompare(y[0]))) selE.append(new Option(`${k} (${n})`, k));
  if (especie && !cuenta.has(especie)) selE.append(new Option(especie + " (0)", especie));
  selE.value = especie;

  const base = enZona.filter((a) => !especie || llaveEspecie(a) === especie);
  const c = contar(base, m);
  $("#progreso").textContent = base.length ? `${c.hechos} de ${c.total} revisados · faltan ${c.total - c.hechos}` + (c.exc ? ` · ${c.exc} con excepción` : "")
    : (zona && !ZONA.get(zona).arboles.length ? "Zona sin inventario: agrega los árboles que encuentres" : "Ningún árbol con estos filtros");
  document.querySelectorAll(".filtros button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.f === filtro));
  const q = $("#buscar").value.trim(), ol = $("#lista"); ol.textContent = "";
  const verZona = !zona;
  // Árboles nuevos de la zona, arriba
  const nuevos = especie ? [] : [...m.values()].filter((x) => x.estado === "nuevo" && (!zona || x.jardin === ZONA.get(zona).nombre) && (!q || x.placa.includes(q)));
  for (const x of nuevos) ol.append(filaArbol({ placa: x.placa, comun: x.especie_real || "Árbol nuevo", cien: "", previo: "", aviso: "", nuevo: true }, x, verZona));
  let n = 0, ocultos = 0;
  for (const a of base) {
    const x = m.get(a.placa);
    if (q && !a.placa.startsWith(q)) continue;
    if (!q && filtro === "pendientes" && x && !recientes.has(a.placa)) continue;
    if (!q && filtro === "marcados" && !x) continue;
    if (n >= 300) { ocultos++; continue; }  // listas larguísimas: filtrar por zona o especie, o buscar placa
    n++; ol.append(filaArbol(a, x, verZona));
  }
  $("#lista-nota").textContent = ocultos ? `Y ${ocultos} más: elige zona o especie, o busca la placa.` : "";
  if (!$("#mapa-caja").hidden) pintarMapa(m, base, nuevos, zona);
}
$("#f-zona").onchange = () => { location.hash = enlace("arboles", { zona: $("#f-zona").value, especie: ruta.p.get("especie") }); };
$("#f-especie").onchange = () => { location.hash = enlace("arboles", { zona: ruta.p.get("zona"), especie: $("#f-especie").value }); };
document.querySelectorAll(".filtros button").forEach((b) => (b.onclick = () => { filtro = b.dataset.f; guardar("hc_filtro", filtro); recientes.clear(); pintar(); }));
$("#buscar").oninput = () => pintar();

// ---------- Ruteo ----------
function leerRuta() {
  const [v, q] = location.hash.replace(/^#\/?/, "").split("?");
  ruta = { v: ["arboles", "especies"].includes(v) ? v : "zonas", p: new URLSearchParams(q || "") };
}
function pintar() {
  if (!D) return;
  const m = vigentes();
  for (const v of ["zonas", "arboles", "especies"]) $("#v-" + v).hidden = ruta.v !== v;
  document.querySelectorAll(".pestanas a").forEach((a) => a.setAttribute("aria-current", a.dataset.v === ruta.v ? "page" : "false"));
  const zona = ruta.p.get("zona");
  $("#titulo").textContent = ruta.v === "zonas" ? "Hojas de campo" : (zona && ZONA.get(zona) ? ZONA.get(zona).nombre : "Todas las zonas");
  if (ruta.v === "zonas") pintarZonas(m); else if (ruta.v === "especies") pintarEspecies(m); else pintarArboles(m);
  pintarSync();
}
addEventListener("hashchange", () => { leerRuta(); $("#buscar").value = ""; recientes.clear(); pintar(); scrollTo(0, 0); });

// ---------- Aviso con deshacer ----------
let tAviso = null;
function avisar(texto) {
  $("#aviso-texto").textContent = texto; $("#aviso").hidden = false;
  clearTimeout(tAviso); tAviso = setTimeout(() => ($("#aviso").hidden = true), 5000);
}
$("#deshacer").onclick = () => {
  if (!ultimo) return;
  const i = cola.findIndex((m) => m.id === ultimo.id);
  if (i >= 0) { cola.splice(i, 1); guardar("hc_cola", cola); }          // aún no subía: se borra de la cola
  else marcar({ placa: ultimo.placa, jardin: ultimo.jardin, estado: "borrar" });  // ya subió: se anula con otra marca
  ultimo = null; $("#aviso").hidden = true; pintar();
};

// ---------- Ubicación ----------
function pedirGps(destino) {
  if (!navigator.geolocation) { destino.textContent = "Este navegador no da ubicación."; return; }
  destino.textContent = "Buscando tu ubicación…";
  navigator.geolocation.getCurrentPosition((p) => {
    gpsActual = { lat: p.coords.latitude, lon: p.coords.longitude, precision_m: Math.round(p.coords.accuracy) };
    destino.textContent = `Ubicación lista (± ${gpsActual.precision_m} m).`;
  }, (e) => { gpsActual = null; destino.textContent = "Sin ubicación: " + e.message; }, { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 });
}

// ---------- Opciones de un árbol ----------
let estadoElegido = null;
function abrirOpciones(a) {
  abierto = a; gpsActual = null;
  const x = vigentes().get(a.placa);
  estadoElegido = x ? x.estado : "revisado";
  $("#o-titulo").textContent = "Placa " + a.placa;
  $("#o-especie").textContent = [a.comun, a.cien].filter(Boolean).join(" · ");
  $("#o-extra").textContent = [a.nuevo ? x.jardin : zonaNombre(a), a.previo, a.aviso, a.obs ? "Revisión 2018: " + a.obs : ""].filter(Boolean).join(" · ");
  $("#o-real").value = x?.especie_real || ""; $("#o-nota").value = x?.nota || ""; $("#o-foto").value = x?.foto_swmaps || "";
  $("#o-gps").textContent = x?.lat ? `Ubicación guardada (± ${x.precision_m ?? "?"} m).` : "";
  $("#o-quitar").hidden = !x;
  pintarEstados();
  $("#opciones").showModal();
}
function pintarEstados() {
  document.querySelectorAll("#opciones .estados button").forEach((b) => {
    b.setAttribute("aria-pressed", b.dataset.e === estadoElegido);
    b.hidden = estadoElegido === "nuevo";
  });
  $("#o-real-caja").hidden = !(estadoElegido === "otra" || estadoElegido === "nuevo");
}
document.querySelectorAll("#opciones .estados button").forEach((b) => (b.onclick = () => { estadoElegido = b.dataset.e; pintarEstados(); }));
$("#o-gps-btn").onclick = () => pedirGps($("#o-gps"));
const zonaDe = (a, x) => (a.nuevo ? x.jardin : zonaNombre(a));
$("#o-guardar").onclick = () => {
  const x = vigentes().get(abierto.placa);
  ultimo = marcar({
    placa: abierto.placa, jardin: zonaDe(abierto, x), estado: estadoElegido,
    especie_real: $("#o-real").value.trim(), nota: $("#o-nota").value.trim(), foto_swmaps: $("#o-foto").value.trim(),
    lat: gpsActual?.lat ?? x?.lat ?? null, lon: gpsActual?.lon ?? x?.lon ?? null, precision_m: gpsActual?.precision_m ?? x?.precision_m ?? null,
  });
  $("#opciones").close(); avisar(`${abierto.placa}: ${ESTADO[estadoElegido]}`);
};
$("#o-quitar").onclick = () => {
  ultimo = marcar({ placa: abierto.placa, jardin: zonaDe(abierto, vigentes().get(abierto.placa)), estado: "borrar" });
  $("#opciones").close(); avisar(`${abierto.placa}: sin marca`);
};

// ---------- Árbol nuevo ----------
$("#nuevo").onclick = () => {
  for (const id of ["n-placa", "n-especie", "n-foto", "n-nota"]) $("#" + id).value = "";
  llenarZonas($("#n-zona"), ruta.p.get("zona") || D.jardines[0].id, false);
  gpsActual = null; $("#dlg-nuevo").showModal(); pedirGps($("#n-gps"));
};
$("#n-guardar").onclick = () => {
  const placa = $("#n-placa").value.trim().replace(/[^A-Za-z0-9-]/g, "") || "N-" + nuevoId().slice(0, 6);
  if (vigentes().has(placa) || ARB.some((a) => a.placa === placa)) {
    $("#n-gps").textContent = `La placa ${placa} ya existe: búscala en la lista y usa "Más".`; return;
  }
  ultimo = marcar({ placa, jardin: ZONA.get($("#n-zona").value).nombre, estado: "nuevo", especie_real: $("#n-especie").value.trim(),
    foto_swmaps: $("#n-foto").value.trim(), nota: $("#n-nota").value.trim(), ...(gpsActual || {}) });
  $("#dlg-nuevo").close(); avisar(`Árbol nuevo ${placa} guardado`);
};

// ---------- Mapa de lo que está en la lista (sin zoom: una zona cabe en la pantalla) ----------
const M = 111320, COS = Math.cos(20.607 * Math.PI / 180);
const xy = (lat, lon) => [(lon + 103.416) * M * COS, -(lat - 20.607) * M];
let vigia = null;
$("#ver-mapa").onclick = () => {
  const caja = $("#mapa-caja"); caja.hidden = !caja.hidden; $("#ver-mapa").setAttribute("aria-pressed", !caja.hidden);
  if (!caja.hidden) { pintar(); if (navigator.geolocation && vigia === null) vigia = navigator.geolocation.watchPosition(ponerYo, () => {}, { enableHighAccuracy: true }); }
  else if (vigia !== null) { navigator.geolocation.clearWatch(vigia); vigia = null; }
};
function pintarMapa(m, base, nuevos, zona) {
  const svg = $("#mapa"), pts = [];
  for (const a of base) if (a.lat && (zona || a.zona !== CLAVIGERO)) pts.push([a.placa, ...xy(a.lat, a.lon), m.get(a.placa)?.estado || ""]);
  for (const x of nuevos) if (x.lat) pts.push([x.placa, ...xy(x.lat, x.lon), "nuevo"]);
  if (!pts.length) { svg.innerHTML = ""; $("#mapa-nota").textContent = "Sin coordenadas para esta lista todavía."; return; }
  const xs = pts.map((p) => p[1]), ys = pts.map((p) => p[2]);
  const x0 = Math.min(...xs) - 15, x1 = Math.max(...xs) + 15, y0 = Math.min(...ys) - 15, y1 = Math.max(...ys) + 15;
  svg.setAttribute("viewBox", [x0, y0, x1 - x0, y1 - y0].join(" "));
  const r = Math.max((x1 - x0) / 140, 1.6);
  let h = "";
  for (const pl of D.edificios) {
    const c = pl.map(([la, lo]) => xy(la, lo));
    if (c.every(([x, y]) => x < x0 || x > x1 || y < y0 || y > y1)) continue;
    h += `<path class="m-edificio" d="M${c.map((p) => p.join(",")).join("L")}Z"/>`;
  }
  for (const [placa, x, y, e] of pts) h += `<circle class="m-arbol ${e}" data-p="${placa}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}"/>`;
  h += `<circle class="m-yo" r="${(r * 1.6).toFixed(1)}" cx="-99999" cy="-99999"/>`;
  svg.innerHTML = h;
  const sinCoord = base.filter((a) => !a.lat).length;
  $("#mapa-nota").textContent = "Toca un punto para ir a su placa en la lista." + (sinCoord ? ` ${sinCoord} sin coordenada no salen.` : "") + (!zona ? " Casa Clavígero no sale en este mapa." : "");
}
$("#mapa").addEventListener("click", (ev) => {
  const c = ev.target.closest("circle.m-arbol"); if (!c) return;
  const fila = document.getElementById("p-" + c.dataset.p);
  document.querySelectorAll(".foco").forEach((e) => e.classList.remove("foco"));
  c.classList.add("foco");
  if (fila) { fila.classList.add("foco"); fila.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" }); }
  else { $("#buscar").value = c.dataset.p; pintar(); }
});
function ponerYo(p) {
  const c = $("#mapa .m-yo"); if (!c) return;
  const [x, y] = xy(p.coords.latitude, p.coords.longitude);
  c.setAttribute("cx", x); c.setAttribute("cy", y);
}

// ---------- Arranque ----------
async function cargarDatos() {
  let datos = leer("hc_datos", null);
  try {
    const r = await fetch("/api/datos");
    if (r.ok) { datos = await r.json(); guardar("hc_datos", datos); }
  } catch (e) { /* sin red: se queda lo guardado */ }
  leerRuta();
  if (!datos) { $("#v-zonas").hidden = false; $("#zonas").textContent = "Sin datos todavía: abre esta página una vez con conexión."; return; }
  indexar(datos); pintar(); sincronizar();
}
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
cargarDatos();
