# web · sitio de Campus Lab en Liferay

Todo lo que se publica en campuslab.iteso.mx (Liferay DXP 7.4, tema ITESO-4). En las páginas que ya existen (sobre todo la portada) se respetan la distribución y las figuras actuales: se mejora, no se reinventa.

| Carpeta | Qué hay | Se pega o sube en Liferay |
|---|---|---|
| `fragmentos/` | Un fragmento por carpeta (`index.html`, `index.css`, `index.js`, `configuration.json`), cada uno con su README de pasos | Diseño > Fragmentos, conjunto "Campus Lab" |
| `fuentes/` | De donde salen los fragmentos y archivos: `prototipos/` (plantillas fuente de los prototipos), `comun/` (`cl-base.css`, `cl-kit.js`), `mapa3d/` (motor del mapa 3D) y `vista_local.html` (prueba local de las páginas de árboles) | `comun/*` y `mapa3d/dist/cl-mapa3d.js` van a Documentos y Medios |
| `contenidos/` | Textos ya listos para Contenidos Web "Basica" (Arboretum, Suculentas) y las páginas de árboles (`arboles/`) | Contenido Web (Código fuente) |
| `sitio_actual/` | Copia del sitio público tal como está (`campuslab/`, `bosque/`), para leer componentes sin entrar a Liferay | No se sube |
| `scripts/` | Generadores y pruebas (ver abajo) | No se sube |

Los fragmentos son el camino que funciona: se guardan como código, sin el limpiador del editor de Contenido Web. Los Contenidos Web "Contenido HTML" muestran el código como texto y "Basica" daña los `<script>` (ver `CLAUDE.md`).

## Scripts

Todos se corren desde la raíz del repo. Lo que generan con datos o fotos queda en `catalogo/salida/` (no va a git).

| Script | Para qué |
|---|---|
| `preparar_para_liferay.py` | Convierte un prototipo de `fuentes/prototipos/` en su fragmento de `fragmentos/` y separa su JSON de datos. Lo generado no se edita a mano |
| `probar_en_sitio.py` | Inyecta un fragmento en `/web/campuslab/temp` sin publicarlo y saca capturas (escritorio/celular, claro/oscuro). Requiere Playwright |
| `generar_datos_arboles.py` | `arboles.json`, `mapa-campus.json` y fotos de árboles para Documentos y Medios |
| `generar_territorios_3d.py` | `territorio-*.json` del mapa 3D |
| `redimensionar_imagenes.py` | Copias para web de las fotos (estándar `liferay_hd`) |
| `scraper_liferay.py` | Regenera `sitio_actual/` (`SCRAPER_BASE_URL=https://bosque.iteso.mx` para el sitio del bosque) |
| `scraper_fichas.py`, `sondeo_fichas_bosque.py` | Bajan y parsean las fichas de especie publicadas |

## Páginas de árboles (`contenidos/arboles/`)

| Pieza | Dónde va en Liferay | Se sube |
|---|---|---|
| `fuentes/comun/cl-base.css`, `fuentes/comun/cl-kit.js` | Documentos y Medios | una vez (y cada vez que cambie) |
| `arboles.json`, `mapa-campus.json` | Documentos y Medios | cada vez que cambien los datos |
| `fotos/*.jpg` | Documentos y Medios, carpeta propia | las nuevas o cambiadas |
| `contenidos/arboles/CL_ARBOLES_*_HTML.html` | Un Contenido Web por página | una vez |

Los JSON y las fotos los genera `python web/scripts/generar_datos_arboles.py` en `catalogo/salida/liferay_subir/arboles/` (ahí también queda `lista_subida.csv` con cada archivo, su peso y su autor). Al subir una versión nueva del mismo archivo en Documentos y Medios su URL no cambia, así que las páginas no se tocan.

Pendiente: pasarlas a fragmentos (rework con fragmentos atómicos), porque "Contenido HTML" no pinta el código. Mientras tanto, en cada `CL_ARBOLES_*_HTML.html` se reemplazan los `PEGAR_...`:

| Marcador | Qué va |
|---|---|
| `PEGAR_URL_CL_BASE_CSS`, `PEGAR_URL_CL_KIT_JS` | URL de cada archivo en Documentos y Medios |
| `PEGAR_URL_ARBOLES_JSON`, `PEGAR_URL_MAPA_CAMPUS_JSON` | URL de cada JSON |
| `PEGAR_PREFIJO_FOTOS` | la parte común de las URL de las fotos, sin el nombre |
| `PEGAR_URL_PAGINA_*` | dirección de cada página |

**Probar antes de subir:** `fuentes/vista_local.html` monta las tres páginas con los datos locales, sin servidor: `?vista=coleccion`, `?vista=especie&id=tabebuia-rosea`, `?vista=mapa`.

## Imágenes

Se suben en la mejor calidad útil para pantalla: el estándar `liferay_hd` de `scripts/redimensionar_imagenes.py` (2560 px por el lado largo; conserva el perfil de color y quita los metadatos EXIF, incluida la ubicación GPS). Liferay genera dos versiones más chicas de cada imagen (Adaptive Media): `?imageThumbnail=1` (300×300) y `?imagePreview=1` (1000 px de ancho). El kit pide la de 300 para el mosaico; en la ficha el navegador elige entre la de 1000 y la de 2560 según la pantalla. Para imprimir (lonas, carteles) se usa el original del volumen, nunca la copia de Liferay.

Las fotos nunca van a git: los originales viven en el volumen y las copias para web en `catalogo/salida/`.

Pendiente: créditos de autor. La mayoría de las fotos no tiene autor en la base de datos y la ficha muestra "Campus Lab ITESO"; revisar `lista_subida.csv` antes de publicar.
