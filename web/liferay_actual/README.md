# Copia local de campuslab.iteso.mx (Liferay)

Foto del sitio público tal como estaba el 8-oct-2026, para poder leer y mejorar sus componentes
sin entrar a Liferay uno por uno. La genera `reestructura/notebooks/scraper_liferay.py` (solo lee páginas públicas).

## Qué hay aquí

- `mapa_del_sitio.json`: cada página y los componentes que usa, en orden de aparición.
- `componentes_indice.json`: cada componente con su título, ID, tamaño, iframes y las páginas donde aparece.
- `componentes/<ID>__<TITULO>.html`: el código de cada componente tal como lo publica Liferay.

## Cómo encontrar un componente en Liferay

Cada componente es un **Contenido Web**. Su `<ID>` (primer número del archivo) y su `<TITULO>` son los que
se buscan en Panel de control > Contenido Web. En la página publicada vive dentro de
`<div class="journal-content-article" data-analytics-asset-id="<ID>" data-analytics-asset-title="<TITULO>">`.

## Qué se puede cambiar desde Liferay y qué no

- **Sí:** el código de `componentes/*.html`. Es HTML con su CSS y JavaScript dentro del propio contenido.
- **No (es del tema):** lo que rodea a los componentes (estructura general de la página, hojas de estilo del tema, scripts globales).
- **Ojo:** esto es el HTML ya publicado, no la fuente. Si un contenido usa una plantilla (por ejemplo `Detalle BN6`, 413542),
  aquí se ve lo que la plantilla produjo, no el código de la plantilla ni los campos con los que se llenó.

## Dónde está cada cosa

- Compartidos en todas las páginas: `Navegación` (351492), `Footer-Top` (788792), `Footer Bottom` (789459).
- Catálogos con todas las tarjetas en un solo componente: orquídeas (19984432), aves (5157578),
  arboretum oriente (22626683) y sur (22691094), suculentas (2945478).
- Ficha de cada especie: `/web/general/detalle?group_id=<ID>`, que muestra el Contenido Web `<ID>` con la plantilla `Detalle BN6`.
- Árboles: `HTML_MAPA` (7667552) solo trae el iframe del mapa de ArcGIS.

## Cosas por arreglar que ya se ven

- En `CL_ORQUIDEAS_CONTENIDO_HTML` hay un enlace roto: `href="hhttps://campuslab.iteso.mx/web/general/detalle?group_id=19899224"` (una "h" de más).
- Las fichas de especie (333 páginas de detalle) no están aquí: se bajaron aparte con `scraper_fichas.py` a `reestructura/salida/sitio_campuslab/` (ver `CLAUDE.md`). El HTML de cada una es texto pegado a mano, no campos estructurados.
- Los nombres de archivo van sin acentos ni ñ (`Navegacion`, no `Navegación`).

## Cómo regenerar

```
cd reestructura/notebooks
python scraper_liferay.py
```
