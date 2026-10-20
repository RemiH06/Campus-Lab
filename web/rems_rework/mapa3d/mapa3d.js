/* ══════════════════════════════════════════════════════════════════════════════════════════════════════
   Mapa 3D de los territorios del ITESO · Three.js r186 (MIT), WebGLRenderer.
   Se empaqueta con esbuild junto con Three en un solo archivo (cl-mapa3d.js) que vive en Documentos y Medios;
   el fragmento lo carga solo en la página del mapa. Datos: web/scripts/generar_territorios_3d.py.
   Una maqueta: edificios extruidos, calles, áreas verdes, relieve (bosque), cada árbol del inventario a su
   altura y copa reales (los que florecen este mes, en su color) y lo observado en Naturalista.
   Se dibuja solo cuando algo cambia. Sin WebGL, montar() devuelve null y el fragmento deja su aviso.
   ══════════════════════════════════════════════════════════════════════════════════════════════════════ */
import * as THREE from "three";
import { MapControls } from "three/addons/controls/MapControls.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";

/* Floraciones del campus: especie → meses (las mismas paletas del kit) */
const FLORACION = [
  { sci: "pseudobombax ellipticum", meses: [12, 1], color: ["#c2416a", "#f2809c"] },
  { sci: "tabebuia rosea", meses: [2], color: ["#c45a9c", "#f08cc8"] },
  { sci: "handroanthus impetiginosus", meses: [2], color: ["#c45a9c", "#f08cc8"] },
  { sci: "jacaranda mimosifolia", meses: [3], color: ["#7b5cc8", "#b8a0f5"] },
  { sci: "roseodendron donnell-smithii", meses: [4], color: ["#e0ab12", "#f4cc4e"] },
  { sci: "delonix regia", meses: [5, 6], color: ["#d9431f", "#ff7d55"] },
  { sci: "spathodea campanulata", meses: [11], color: ["#e06a12", "#ff9e4e"] }
];
const GRUPO = { planta: ["#3f8f5a", "#7fd09a"], ave: ["#2f6fa8", "#7fbede"], insecto: ["#b5651d", "#f0a868"], hongo: ["#8a5a8c", "#d8a8da"],
  mamifero: ["#7a5a3e", "#c9a27e"], reptil: ["#5f7434", "#a8c46a"], otro: ["#5d6873", "#b4c3ce"] };
const NOMBRE_GRUPO = { planta: "Plantas", ave: "Aves", insecto: "Insectos y arañas", hongo: "Hongos", mamifero: "Mamíferos", reptil: "Reptiles y anfibios", otro: "Otros" };

/* Colores de la maqueta: [claro, oscuro] */
const PAL = {
  suelo: ["#d3d6cf", "#141d22"], dentro: ["#dde6d6", "#18262a"], verde: ["#bfd8b0", "#1d3329"], calle: ["#f7f6f1", "#3a4a52"],
  andador: ["#eadfc8", "#465450"], edificio: ["#efe7da", "#3a4650"], borde: ["#3f6b4f", "#4f9a69"], tronco: ["#7a5a3e", "#8a6c52"],
  copa: ["#4f8a5b", "#3f7a52"], resalte: ["#12283a", "#e3ece9"], cielo: ["#f3f6f5", "#0c171e"]
};

const reduce = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const hash = (n) => { n = Math.imul(n ^ (n >>> 16), 0x45d9f3b); n = Math.imul(n ^ (n >>> 16), 0x45d9f3b); return ((n ^ (n >>> 16)) >>> 0) / 4294967296; };
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

function pares(a, desde) { const p = []; for (let i = desde; i + 1 < a.length; i += 2) p.push([a[i], a[i + 1]]); return p; }

/* Relieve: altura en (x, z) por interpolación bilineal de la malla */
function alturaEn(ter, x, z) {
  if (!ter) return 0;
  const fx = (x - ter.x0) / ter.paso, fz = (z - ter.z0) / ter.paso, n = ter.n;
  const i = Math.max(0, Math.min(n - 2, Math.floor(fx))), j = Math.max(0, Math.min(n - 2, Math.floor(fz)));
  const tx = Math.min(1, Math.max(0, fx - i)), tz = Math.min(1, Math.max(0, fz - j)), y = ter.y;
  const a = y[j * n + i], b = y[j * n + i + 1], c = y[(j + 1) * n + i], d = y[(j + 1) * n + i + 1];
  return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
}

/* Franja de ancho w sobre una polilínea (calles), pegada al relieve */
function franja(pts, w, y0, ter) {
  const pos = [], idx = [];
  for (let k = 0; k < pts.length; k++) {
    const [x, z] = pts[k], a = pts[Math.max(0, k - 1)], b = pts[Math.min(pts.length - 1, k + 1)];
    let dx = b[0] - a[0], dz = b[1] - a[1]; const l = Math.hypot(dx, dz) || 1; dx /= l; dz /= l;
    const nx = -dz * w / 2, nz = dx * w / 2, y = y0 + alturaEn(ter, x, z);
    pos.push(x + nx, y, z + nz, x - nx, y, z - nz);
    if (k) { const o = (k - 1) * 2; idx.push(o, o + 1, o + 2, o + 1, o + 3, o + 2); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}

function enPoli(x, z, p) {
  let c = false;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    const [xi, zi] = p[i], [xj, zj] = p[j];
    if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) c = !c;
  }
  return c;
}

function forma(pts) { const s = new THREE.Shape(); pts.forEach(([x, z], i) => (i ? s.lineTo(x, -z) : s.moveTo(x, -z))); return s; }
function plano(pts, y) { const g = new THREE.ShapeGeometry(forma(pts)); g.rotateX(-Math.PI / 2); g.translate(0, y, 0); return g; }

export async function montar(el, op) {
  const canvas = document.createElement("canvas");
  canvas.className = "m3d-lienzo"; canvas.setAttribute("aria-hidden", "true");
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }); } catch (e) { return null; }
  el.querySelector(".m3d-vista").prepend(canvas);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  const grande = () => el.clientWidth >= 760;
  renderer.shadowMap.enabled = grande(); renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 1, 20000);
  const controls = new MapControls(camera, canvas);
  controls.enableDamping = !reduce(); controls.dampingFactor = 0.12; controls.maxPolarAngle = Math.PI * 0.42; controls.screenSpacePanning = false;
  controls.enableZoom = false; /* la rueda no secuestra el scroll de la página: se activa al tocar el mapa */
  controls.touches = { ONE: null, TWO: THREE.TOUCH.DOLLY_PAN }; /* en celular, un dedo sigue haciendo scroll; el mapa va con dos */
  canvas.addEventListener("pointerdown", () => { controls.enableZoom = true; });
  canvas.addEventListener("pointerleave", () => { controls.enableZoom = false; });

  const hemi = new THREE.HemisphereLight(0xffffff, 0x8a8170, 2.2); scene.add(hemi);
  const sol = new THREE.DirectionalLight(0xfff4e0, 2.4); sol.castShadow = true; sol.shadow.mapSize.set(2048, 2048); sol.shadow.bias = -0.0004;
  scene.add(sol, sol.target);

  const raiz = new THREE.Group(); scene.add(raiz);
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  const tip = el.querySelector(".m3d-tip"), estado = el.querySelector(".m3d-estado");
  let D = null, E = [], copas = null, troncos = null, puntos = null, anillo = null, capas = { arb: true, obs: true }, oscuro = false;
  const mes = new Date().getMonth() + 1;
  const flor = new Map(); FLORACION.forEach((f) => f.meses.includes(mes) && flor.set(f.sci, f));

  /* ── Etiquetas de lugares: los nombres de edificio ("Edificio A") solo de cerca; las que chocan, la de atrás se oculta ── */
  const capaEtq = document.createElement("div"); capaEtq.className = "m3d-etqs";
  el.querySelector(".m3d-vista").append(capaEtq);
  let etqs = [];
  function armarEtiquetas() {
    capaEtq.innerHTML = ""; etqs = (D.etq || []).map(([x, z, alto, texto]) => {
      /* tocar una etiqueta lleva a ese lugar (en el bosque, de un predio al otro) */
      const n = document.createElement("button"); n.type = "button"; n.textContent = texto; capaEtq.append(n);
      const y0 = alturaEn(D.ter, x, z), lejos = D.ter ? 520 : 110, v = new THREE.Vector3(x, y0 + alto + (D.ter ? 40 : 4), z);
      n.onclick = () => volar(new THREE.Vector3(x, y0, z), new THREE.Vector3(x + lejos * 0.45, y0 + lejos * 0.8, z + lejos * 0.7));
      return { n, v, menor: /^(Edificio |Q\d)/.test(texto) };
    });
  }
  const tmp = new THREE.Vector3();
  function ponerEtiquetas() {
    const w = canvas.clientWidth, h = canvas.clientHeight, dist = camera.position.distanceTo(controls.target), puestas = [];
    etqs.map((e) => { tmp.copy(e.v).project(camera); return { e, x: (tmp.x + 1) / 2 * w, y: (1 - tmp.y) / 2 * h, z: tmp.z }; })
      .sort((a, b) => a.z - b.z)
      .forEach(({ e, x, y, z }) => {
        let ver = z < 1 && x > 0 && x < w && y > 0 && y < h && (!e.menor || dist < 420);
        const ancho = e.n.offsetWidth || e.n.textContent.length * 7, caja = [x - ancho / 2, y - 22, x + ancho / 2, y];
        if (ver && puestas.some((c) => caja[0] < c[2] && caja[2] > c[0] && caja[1] < c[3] && caja[3] > c[1])) ver = false;
        if (ver) puestas.push(caja);
        e.n.hidden = !ver; if (ver) e.n.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -100%)`;
      });
  }

  /* ── Dibujo a demanda: solo cuando algo cambia; el amortiguado de los controles pide cuadros mientras dura ── */
  let pedido = false;
  function render() { pedido = false; const mov = controls.update(); renderer.render(scene, camera); ponerEtiquetas(); if (mov) pedir(); }
  function pedir() { if (!pedido) { pedido = true; requestAnimationFrame(render); } }
  controls.addEventListener("change", pedir);
  const ro = new ResizeObserver(() => {
    const v = el.querySelector(".m3d-vista"), w = v.clientWidth, h = v.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); pedir();
  });
  ro.observe(el.querySelector(".m3d-vista"));

  const col = (par) => new THREE.Color(par[oscuro ? 1 : 0]);

  function limpiar() {
    raiz.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) [].concat(o.material).forEach((m) => m.dispose()); });
    raiz.clear(); copas = troncos = puntos = anillo = null;
  }

  function construir() {
    limpiar();
    const ter = D.ter, [x0, z0, x1, z1] = D.ext, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, W = x1 - x0, H = z1 - z0;
    /* suelo o relieve */
    if (ter) {
      const n = ter.n, g = new THREE.PlaneGeometry(ter.paso * (n - 1), ter.paso * (n - 1), n - 1, n - 1);
      g.rotateX(-Math.PI / 2);
      g.translate(ter.x0 + ter.paso * (n - 1) / 2, 0, ter.z0 + ter.paso * (n - 1) / 2);
      const p = g.attributes.position, cs = [], top = Math.max(...ter.y), polis = D.lim.map((l) => pares(l, 0));
      const c0 = new THREE.Color(oscuro ? "#24382c" : "#a9bd98"), c1 = new THREE.Color(oscuro ? "#4a4536" : "#c9b98f");
      const cDentro = new THREE.Color(oscuro ? "#3f7a52" : "#7fb36a"), c = new THREE.Color();
      for (let k = 0; k < p.count; k++) {
        const y = ter.y[k]; p.setY(k, y);
        c.copy(c0).lerp(c1, Math.pow(y / top, 1.4));
        if (polis.some((pl) => enPoli(p.getX(k), p.getZ(k), pl))) c.lerp(cDentro, 0.75);
        cs.push(c.r, c.g, c.b);
      }
      g.setAttribute("color", new THREE.Float32BufferAttribute(cs, 3)); g.computeVertexNormals();
      const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true })); m.receiveShadow = true; raiz.add(m);
    } else {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(W * 1.6, H * 1.6).rotateX(-Math.PI / 2).translate(cx, -0.05, cz), new THREE.MeshLambertMaterial({ color: col(PAL.suelo) }));
      m.receiveShadow = true; raiz.add(m);
    }
    /* contorno del territorio: relleno (plano) y borde que sigue el relieve */
    for (const l of D.lim) {
      const pts = pares(l, 0);
      if (!ter) { const m = new THREE.Mesh(plano(pts, 0.02), new THREE.MeshLambertMaterial({ color: col(PAL.dentro) })); m.receiveShadow = true; raiz.add(m); }
      const cerrado = pts.concat([pts[0], pts[1] || pts[0]]);
      raiz.add(new THREE.Mesh(franja(cerrado, ter ? 16 : 1.8, ter ? 2.5 : 0.25, ter), new THREE.MeshBasicMaterial({ color: col(PAL.borde), side: THREE.DoubleSide })));
    }
    /* áreas verdes */
    const vs = D.ver.map((v) => { try { return plano(pares(v, 0), 0.06); } catch (e) { return null; } }).filter(Boolean);
    if (vs.length && !ter) { const m = new THREE.Mesh(mergeGeometries(vs), new THREE.MeshLambertMaterial({ color: col(PAL.verde) })); m.receiveShadow = true; raiz.add(m); }
    /* calles y andadores (los angostos, en otro tono) */
    const anchas = [], angostas = [];
    for (const c of D.cam) (c[0] >= 5 ? anchas : angostas).push(franja(pares(c, 1), c[0], ter ? 1.2 : 0.1 + (c[0] >= 5 ? 0 : 0.03), ter));
    if (anchas.length) raiz.add(Object.assign(new THREE.Mesh(mergeGeometries(anchas), new THREE.MeshLambertMaterial({ color: col(PAL.calle) })), { receiveShadow: true }));
    if (angostas.length) raiz.add(Object.assign(new THREE.Mesh(mergeGeometries(angostas), new THREE.MeshLambertMaterial({ color: col(PAL.andador) })), { receiveShadow: true }));
    /* edificios */
    const bs = [];
    for (const b of D.bld) {
      try { const g = new THREE.ExtrudeGeometry(forma(pares(b, 1)), { depth: b[0], bevelEnabled: false }); g.rotateX(-Math.PI / 2); bs.push(g); } catch (e) { /* contorno mal cerrado */ }
    }
    if (bs.length) {
      const m = new THREE.Mesh(mergeGeometries(bs), new THREE.MeshLambertMaterial({ color: col(PAL.edificio) }));
      m.castShadow = m.receiveShadow = true; raiz.add(m);
    }
    /* árboles: tronco y copa instanciados (una llamada de dibujo cada uno) */
    const A = D.arb || [];
    if (A.length) {
      const gT = new THREE.CylinderGeometry(0.18, 0.26, 1, 6).translate(0, 0.5, 0), gC = new THREE.IcosahedronGeometry(0.5, 1);
      troncos = new THREE.InstancedMesh(gT, new THREE.MeshLambertMaterial({ color: col(PAL.tronco) }), A.length);
      copas = new THREE.InstancedMesh(gC, new THREE.MeshLambertMaterial({ flatShading: true }), A.length);
      troncos.castShadow = copas.castShadow = true; copas.receiveShadow = true;
      const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), c = new THREE.Color(), base = col(PAL.copa);
      A.forEach(([placa, x, z, alto, copa, ei], i) => {
        /* proporción de árbol real: la copa ocupa los dos tercios de arriba y nunca es más angosta que ~45 % de la altura */
        const y0 = alturaEn(ter, x, z), hc = Math.max(1.6, alto * 0.66), ht = Math.max(0.6, alto - hc * 0.85), r = Math.max(0.8, copa / 2, alto * 0.22);
        const grosor = Math.max(0.6, Math.min(2.2, r / 3));
        troncos.setMatrixAt(i, m4.compose(p.set(x, y0, z), q, s.set(grosor, ht, grosor)));
        copas.setMatrixAt(i, m4.compose(p.set(x, y0 + ht + hc * 0.35, z), q.setFromAxisAngle(s.set(0, 1, 0), hash(placa) * 6.28), s.set(r * 2, hc, r * 2)));
        q.identity();
        const e = E[ei], f = e && flor.get(e.sci.toLowerCase());
        if (f) c.set(f.color[oscuro ? 1 : 0]); else c.copy(base).offsetHSL((hash(placa * 7) - 0.5) * 0.05, (hash(placa * 13) - 0.5) * 0.12, (hash(placa * 3) - 0.5) * 0.08);
        copas.setColorAt(i, c);
      });
      troncos.computeBoundingSphere(); copas.computeBoundingSphere();
      troncos.visible = copas.visible = capas.arb; raiz.add(troncos, copas);
    }
    /* observaciones de iNaturalist: pines del color de su grupo */
    if (D.obs.length) {
      const g = new THREE.ConeGeometry(1, 2.6, 8).rotateX(Math.PI).translate(0, 1.3, 0);
      puntos = new THREE.InstancedMesh(g, new THREE.MeshLambertMaterial(), D.obs.length);
      const m4 = new THREE.Matrix4(), c = new THREE.Color(), k = ter ? 9 : 1.4;
      D.obs.forEach(([x, z, gr], i) => {
        const y = alturaEn(ter, x, z) + (ter ? 4 : 2.2);
        puntos.setMatrixAt(i, m4.makeScale(k, k, k).setPosition(x, y, z)); puntos.setColorAt(i, c.set((GRUPO[gr] || GRUPO.otro)[oscuro ? 1 : 0]));
      });
      puntos.computeBoundingSphere(); puntos.visible = capas.obs; raiz.add(puntos);
    }
    /* sol y sombras ajustados al tamaño del territorio */
    const R = Math.max(W, H) * 0.6, topY = ter ? Math.max(...ter.y) : 30;
    sol.position.set(cx - R * 0.6, R * 0.9 + topY, cz - R * 0.4); sol.target.position.set(cx, 0, cz);
    Object.assign(sol.shadow.camera, { left: -R, right: R, top: R, bottom: -R, near: 1, far: R * 4 }); sol.shadow.camera.updateProjectionMatrix();
    hemi.color.set(oscuro ? "#9fb4c8" : "#ffffff"); hemi.groundColor.set(oscuro ? "#1a2026" : "#8a8170"); hemi.intensity = oscuro ? 1.1 : 2.2; sol.intensity = oscuro ? 0.7 : 2.4;
    el.style.setProperty("--m3d-cielo", PAL.cielo[oscuro ? 1 : 0]);
  }

  function encuadre(saltar) {
    const [x0, z0, x1, z1] = D.ext, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, R = Math.max(x1 - x0, z1 - z0);
    const y0 = D.ter ? Math.max(...D.ter.y) * 0.4 : 0, d = R / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * (camera.aspect < 1 ? 1.5 : 0.95);
    volar(new THREE.Vector3(cx, y0, cz), new THREE.Vector3(cx + d * 0.32, y0 + d * 0.78, cz + d * 0.62), saltar);
    controls.minDistance = 25; controls.maxDistance = R * 3;
  }

  let anim = null;
  function volar(objetivo, pos, saltar) {
    if (anim) cancelAnimationFrame(anim);
    if (saltar || reduce()) { controls.target.copy(objetivo); camera.position.copy(pos); controls.update(); pedir(); return; }
    const t0 = performance.now(), a = controls.target.clone(), b = camera.position.clone(), dur = 900;
    const paso = (t) => {
      const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      controls.target.lerpVectors(a, objetivo, e); camera.position.lerpVectors(b, pos, e); controls.update(); renderer.render(scene, camera); ponerEtiquetas();
      anim = k < 1 ? requestAnimationFrame(paso) : null;
    };
    anim = requestAnimationFrame(paso);
  }

  /* ── Buscar una placa: vuela hacia el árbol y lo marca con un anillo ── */
  function irAPlaca(placa) {
    const A = D.arb || [], i = A.findIndex((a) => String(a[0]) === String(placa));
    if (i < 0) { estado.textContent = placa ? `No encontramos la placa ${placa} en este territorio.` : ""; return false; }
    const [, x, z, alto, copa, ei] = A[i], y = alturaEn(D.ter, x, z);
    if (anillo) { raiz.remove(anillo); anillo.traverse((o) => { if (o.geometry) { o.geometry.dispose(); o.material.dispose(); } }); }
    /* marca: anillo en el suelo y un cono flotando sobre la copa (se ve aunque las copas vecinas tapen el anillo) */
    const mat = () => new THREE.MeshBasicMaterial({ color: col(PAL.resalte), side: THREE.DoubleSide }), r = Math.max(copa / 2, alto * 0.22);
    anillo = new THREE.Group();
    anillo.add(new THREE.Mesh(new THREE.RingGeometry(r + 1, r + 2.2, 40).rotateX(-Math.PI / 2).translate(0, 0.3, 0), mat()));
    anillo.add(new THREE.Mesh(new THREE.ConeGeometry(2.2, 5, 16).rotateX(Math.PI).translate(0, alto + 7, 0), mat()));
    anillo.position.set(x, y, z); raiz.add(anillo);
    const e = E[ei]; estado.textContent = `Placa ${placa}: ${e ? e.com || e.sci : "especie sin registrar"}, ${alto} m de alto.`;
    volar(new THREE.Vector3(x, y + alto / 2, z), new THREE.Vector3(x + 55, y + 120, z + 85));
    return true;
  }

  /* ── Señalar con el puntero: árbol u observación bajo el cursor ── */
  function aQue(ev) {
    const r = canvas.getBoundingClientRect();
    ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const obj = [copas, puntos].filter((o) => o && o.visible), hit = ray.intersectObjects(obj, false)[0];
    if (!hit) return null;
    if (hit.object === copas) { const a = D.arb[hit.instanceId], e = E[a[5]]; return { tipo: "arb", a, e, x: ev.clientX - r.left, y: ev.clientY - r.top }; }
    return { tipo: "obs", o: D.obs[hit.instanceId], x: ev.clientX - r.left, y: ev.clientY - r.top };
  }
  function mostrarTip(h) {
    if (!h) { tip.hidden = true; delete tip.dataset.h; canvas.style.cursor = ""; return; }
    if (h.tipo === "arb") {
      const [placa, , , alto, copa] = h.a;
      tip.innerHTML = `<b>${esc(h.e ? h.e.com || h.e.sci : "Especie sin registrar")}</b>${h.e ? `<i>${esc(h.e.sci)}</i>` : ""}<span>Placa ${placa} · ${alto} m de alto · copa de ${copa} m</span>` +
        (h.e && op.ficha ? `<span class="m3d-tip-accion">Toca para ver la ficha</span>` : "");
    } else {
      const [, , gr, nombre] = h.o;
      tip.innerHTML = `<b>${esc(nombre || "Sin identificar")}</b><span>${esc(NOMBRE_GRUPO[gr] || "Otros")} · observado en Naturalista</span><span class="m3d-tip-accion">Toca para verlo en iNaturalist</span>`;
    }
    tip.dataset.h = JSON.stringify(h); tip.hidden = false; canvas.style.cursor = "pointer";
    const v = canvas.getBoundingClientRect(); tip.style.left = Math.min(h.x + 14, v.width - tip.offsetWidth - 8) + "px"; tip.style.top = Math.max(8, h.y - tip.offsetHeight - 12) + "px";
  }
  let movido = false, abajo = null;
  canvas.addEventListener("pointermove", (ev) => { if (abajo && Math.hypot(ev.clientX - abajo[0], ev.clientY - abajo[1]) > 5) movido = true; if (ev.pointerType === "mouse" && !ev.buttons) mostrarTip(aQue(ev)); });
  canvas.addEventListener("pointerleave", () => mostrarTip(null));
  canvas.addEventListener("pointerdown", (ev) => { abajo = [ev.clientX, ev.clientY]; movido = false; });
  canvas.addEventListener("pointerup", (ev) => {
    if (movido) return; const h = aQue(ev); if (!h) { mostrarTip(null); return; }
    if (ev.pointerType !== "mouse") { mostrarTip(h); return; } /* en celular, el primer toque muestra; el botón de la ficha lleva */
    abrir(h);
  });
  tip.addEventListener("click", () => tip.dataset.h && abrir(JSON.parse(tip.dataset.h)));
  function abrir(h) {
    if (h.tipo === "arb" && h.e && op.ficha) location.href = op.ficha + (op.ficha.includes("?") ? "&" : "?") + "id=" + encodeURIComponent(h.e.id);
    if (h.tipo === "obs") window.open("https://www.inaturalist.org/observations/" + h.o[4], "_blank", "noopener");
  }

  /* ── Modo claro/oscuro: el del contenedor (color-scheme que pone el Marco o el kit) ── */
  /* mismo orden que el resto del sitio: elección guardada, modo del componente, el del dispositivo */
  function leerModo() {
    let m = null; try { m = localStorage.getItem("cl-modo"); } catch (e) { /* sin almacenamiento */ }
    m = m || (el.closest("[data-modo]") || { dataset: {} }).dataset.modo || document.documentElement.dataset.clModo;
    return m ? m === "oscuro" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function aplicarModo() { const o = leerModo(); if (o !== oscuro && D) { oscuro = o; construir(); pedir(); } else oscuro = o; }
  document.addEventListener("cl-modo", () => setTimeout(aplicarModo, 0));
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => setTimeout(aplicarModo, 0));

  return {
    async cargar(datos, arboles) {
      estado.textContent = "Cargando el territorio…";
      const [d, a] = await Promise.all([fetch(datos, { credentials: "same-origin" }).then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }),
        arboles ? fetch(arboles, { credentials: "same-origin" }).then((r) => (r.ok ? r.json() : null)).catch(() => null) : null]);
      D = d; E = (a && a.especies) || E; oscuro = leerModo(); mostrarTip(null);
      construir(); armarEtiquetas(); encuadre(true); pedir();
      estado.textContent = ""; return D;
    },
    capa(nombre, visible) { capas[nombre] = visible; if (nombre === "arb" && copas) copas.visible = troncos.visible = visible; if (nombre === "obs" && puntos) puntos.visible = visible; pedir(); },
    irAPlaca, inicio: () => encuadre(false),
    zoom(f) { const v = camera.position.clone().sub(controls.target).multiplyScalar(f); if (v.length() > controls.minDistance && v.length() < controls.maxDistance) { camera.position.copy(controls.target).add(v); pedir(); } },
    girar(grados) { const v = camera.position.clone().sub(controls.target).applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(grados)); camera.position.copy(controls.target).add(v); pedir(); },
    resumen() {
      const g = {}; (D.obs || []).forEach((o) => { g[o[2]] = (g[o[2]] || 0) + 1; });
      const fl = (D.arb || []).filter((a) => E[a[5]] && flor.get(E[a[5]].sci.toLowerCase()));
      const fm = [...new Set(fl.map((a) => E[a[5]].com || E[a[5]].sci))];
      return { arboles: (D.arb || []).length, obs: g, florecen: fm, colores: [...flor.values()].map((f) => f.color[oscuro ? 1 : 0]), grupos: GRUPO, nombres: NOMBRE_GRUPO, oscuro };
    },
    destruir() { ro.disconnect(); controls.dispose(); limpiar(); renderer.dispose(); canvas.remove(); }
  };
}
