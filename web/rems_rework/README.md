# rems_rework · retrabajo del sitio de Campus Lab

Páginas nuevas y rehechas para campuslab.iteso.mx, listas para subir a Liferay pieza por pieza. En las páginas que ya existen (sobre todo la portada) se respetan la distribución y las figuras actuales: se mejora, no se reinventa.

## Cómo está armado

| Pieza | Dónde va en Liferay | Se sube |
|---|---|---|
| `comun/cl-base.css` | Documentos y Medios | una vez (y cada vez que cambie) |
| `comun/cl-kit.js` | Documentos y Medios | una vez (y cada vez que cambie) |
| `arboles.json`, `mapa-campus.json` | Documentos y Medios | cada vez que cambien los datos |
| `fotos/*.jpg` | Documentos y Medios, carpeta propia | las nuevas o cambiadas |
| `arboles/CL_ARBOLES_*_HTML.html` | Un Contenido Web "Contenido HTML" por página | una vez |

Los JSON y las fotos no viven en el repo: los genera `python web/scripts/generar_datos_arboles.py` en `reestructura/salida/liferay_subir/arboles/` (ahí también queda `lista_subida.csv` con cada archivo, su peso y su autor).

Al reemplazar un archivo en Documentos y Medios (subir una versión nueva del mismo), su URL "Latest Version" no cambia, así que los Contenidos Web no se tocan.

## Orden de subida

0. **Prueba técnica** (`prueba_subida/`): subir `cl-prueba.css`, `cl-prueba.js` y `reestructura/salida/liferay_subir/prueba/prueba-foto-rosa-morada.jpg`; pegar sus tres URL en `CL_PRUEBA_SUBIDA_HTML.html` y verlo en vista previa. Confirma que el CSS y el JS cargan desde Documentos y Medios y qué tamaños de foto da Liferay.
1. Subir `cl-base.css` y `cl-kit.js`.
2. Generar los datos y subir `arboles.json` y `mapa-campus.json`.
3. Subir las fotos (`fotos/`, se pueden arrastrar varias a la vez).
4. Crear las tres páginas (colección, ficha, mapa), ocultas del menú mientras son prueba.
5. En cada `CL_ARBOLES_*_HTML.html`, reemplazar los `PEGAR_...` y pegarlo en su Contenido Web.

| Marcador | Qué va |
|---|---|
| `PEGAR_URL_CL_BASE_CSS`, `PEGAR_URL_CL_KIT_JS` | URL "Latest Version" de cada archivo |
| `PEGAR_URL_ARBOLES_JSON`, `PEGAR_URL_MAPA_CAMPUS_JSON` | URL "Latest Version" de cada JSON |
| `PEGAR_PREFIJO_FOTOS` | la parte común de las URL de las fotos, sin el nombre (por confirmar con la prueba 0) |
| `PEGAR_URL_PAGINA_*` | dirección de cada página creada en el paso 4 |

## Probar antes de subir

`vista_local.html` monta las tres páginas con los datos locales, sin servidor: `vista_local.html?vista=coleccion`, `?vista=especie&id=tabebuia-rosea`, `?vista=mapa`.

## Imágenes

Se suben en la mejor calidad útil para pantalla: el estándar `liferay_hd` de `web/scripts/redimensionar_imagenes.py` (2560 px por el lado largo, de la foto más pesada de cada parte; conserva el perfil de color y quita los metadatos EXIF, incluida la ubicación GPS). Liferay genera dos versiones más chicas de cada imagen (Adaptive Media, ya activo en el sitio): `?imageThumbnail=1` (300×300) y `?imagePreview=1` (1000 px de ancho). El kit pide la de 300 para el mosaico; en la ficha el navegador elige entre la de 1000 y el archivo de 2560 según la pantalla. Para imprimir (lonas, carteles) se usa el original del volumen, nunca la copia de Liferay.

Pendiente: créditos de autor. La mayoría de las fotos no tiene autor en la base de datos y la ficha muestra "Campus Lab ITESO"; revisar `lista_subida.csv` antes de publicar.
