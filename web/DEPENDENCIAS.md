# Dependencias del sitio de Campus Lab

Revisado el 20 de octubre de 2026, a pedido de Maya: que nada de lo que usamos sea de paga, incompatible o un problema a futuro.

**Respuesta corta:** lo que se publica en Liferay no usa ninguna librería, plugin ni servicio externo. Todo es HTML, CSS y JavaScript escritos aquí, guardados como fragmentos de Liferay, más archivos (JSON y fotos) en Documentos y Medios del propio sitio. No hay nada que pagar, que caduque ni que dependa de una empresa externa.

## Lo que se publica en Liferay

| Pieza | De qué depende | Costo | Riesgo a futuro |
|---|---|---|---|
| Fragmentos (Marco, prototipos, rework) | Liferay DXP, que ITESO ya tiene con licencia | Ninguno extra | Los fragmentos son una función estándar de Liferay 7.4. Si OSI actualiza Liferay, se prueban de nuevo, pero no hay código de terceros que romper |
| Marco (corrige header y footer) | Los ids y clases del tema ITESO-4 | Ninguno | Si OSI cambia el header del tema, las correcciones dejan de aplicar (el header se ve como hoy, sin romperse). Revisarlo si cambia el tema |
| Tipografía | Degular, que ya carga el tema de ITESO | Ninguno (la licencia es de ITESO; nosotros no la distribuimos) | Si el tema dejara de cargarla, el navegador usa su fuente del sistema. No descargamos fuentes de ningún servicio |
| Datos (JSON) y fotos | Documentos y Medios del sitio | Ninguno | Ninguno. Liferay genera sus versiones chicas de las fotos (Adaptive Media, ya activo) |
| Mapa de árboles del rework | Las coordenadas exportadas del inventario, dibujadas por el propio código | Ninguno | No usa Google Maps, ArcGIS ni ningún servicio de mapas |
| Preferencias del visitante (modo claro/oscuro, paleta) | El almacenamiento local del navegador | Ninguno | Ninguno; si el navegador lo bloquea, la página funciona en claro |

**Compatibilidad con navegadores.** Se usan funciones de CSS de 2023-2024 (`light-dark()`, `color-mix()`, `:has()`). Los navegadores que no las tienen ven la página en modo claro con colores fijos: nunca se quedan sin color ni sin contenido. Probado en escritorio (1280, 1920 y 2560 px) y en celular (390 px).

**Sin jQuery ni otras librerías.** El JavaScript no depende del jQuery que trae el tema: si ITESO lo quita, nuestras piezas siguen funcionando.

## Enlaces a servicios externos (solo ligas, no dependencias)

La página enlaza a iNaturalist, xeno-canto y Naturalista.mx, pero no carga nada de ellos. Si alguno cambia, la liga se corrige y la página sigue igual.

**Fotos de terceros:** las fotos de iNaturalist o del concurso Naturalista tienen la licencia que eligió cada autor (casi todas CC BY-NC: uso no comercial con crédito). Publicarlas siempre con el nombre del autor.

## Herramientas de trabajo (no van al sitio)

Solo corren en la computadora de quien mantiene el proyecto, para preparar datos y probar páginas. Todas son gratuitas y de código abierto.

| Herramienta | Para qué | Licencia |
|---|---|---|
| Python 3 | Scripts del repo | PSF (libre) |
| Pillow | Redimensionar fotos | MIT-CMU (libre) |
| Playwright | Probar fragmentos sobre la página real | Apache 2.0 (libre) |
| FastAPI, NumPy, requests | Herramientas internas de revisión de fotos (`reestructura/herramientas/`) | MIT / BSD / Apache 2.0 (libres) |
| Figtree en las vistas previas locales | Fuente de respaldo al ver los prototipos fuera de Liferay, desde Bunny Fonts | SIL OFL (libre); no llega a Liferay |

Servicios de consulta usados al preparar datos, nunca desde el sitio: GBIF (abierto), API de lectura de iNaturalist (abierta) y Pl@ntNet (gratuita con límite diario de consultas).

## Qué revisar si algo cambia

- **OSI actualiza Liferay o el tema:** volver a probar los fragmentos con `python web/camino_b/probar_en_sitio.py <carpeta del fragmento>`.
- **Antes de agregar cualquier librería nueva:** que sea de código abierto, que se pueda copiar dentro del fragmento o de Documentos y Medios (no cargarla desde un CDN externo) y anotarla en este archivo.
