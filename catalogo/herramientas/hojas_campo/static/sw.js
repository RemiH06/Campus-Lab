// Service worker: guarda la página y los datos para abrirla sin señal en el jardín.
// Red primero (con tope de 4 s para señal débil), caché si no hay red. Las marcas NO pasan por aquí:
// las encola app.js en localStorage y las sube cuando hay conexión.
const CACHE = "hojas-campo-v2";
const BASE = ["/", "/app.js", "/app.css", "/manifest.webmanifest", "/icono.svg", "/api/datos"];

self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(BASE)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname === "/api/marcas" || url.pathname.endsWith(".csv")) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const r = await Promise.race([fetch(e.request), new Promise((_, no) => setTimeout(() => no(new Error("lento")), 4000))]);
      if (r.ok) cache.put(e.request, r.clone());
      return r;
    } catch (err) {
      return (await cache.match(e.request)) || (await cache.match("/")) || Response.error();
    }
  })());
});
