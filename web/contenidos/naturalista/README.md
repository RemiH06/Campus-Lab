# Landing Naturalista ITESO

Una sola página en Campus Lab (`campuslab.iteso.mx/naturalista`) que junta el registro de biodiversidad en iNaturalist, el concurso de fotografía y las galerías. Sustituye a tres páginas: [Naturalistas](https://campuslab.iteso.mx/web/general/detalle?group_id=1777149), [Prepárate para el concurso](https://www.iteso.mx/web/general/detalle?group_id=22128620) (CPC) y [Convocatoria 2025](https://campuslab.iteso.mx/web/general/detalle?group_id=8457292). La propuesta que se le hizo a Mayra está en el doc "Propuesta: landing Naturalista ITESO".

`pagina.json` es la receta: qué fragmentos van, en qué orden, con qué Configuración y qué se escribe en sus zonas editables cuando cambia lo que ya traen.

## Orden de la página

| # | Fragmento | Qué muestra | Cómo se edita |
|---|---|---|---|
| 1 | Marco | Base de colores, modo y lector de CSV (va en la Master Page) | no se edita |
| 2 | Portada | Foto ganadora, título y dos botones | clic en texto, botones y foto |
| 3 | Cifras iNaturalist | Qué es Naturalista ITESO y las cifras del proyecto en vivo | clic en el texto; el número de proyecto en Configuración |
| 4 | Pasos | Prepárate en 3 pasos | clic en cada paso |
| 5 | Concurso | Lo que toca según la etapa (próxima, abierta con botón de registro, jurado, resultados), ficha y bases | Configuración > etapa y fechas; clic en textos y en el botón de registro (la liga al formulario) |
| 6 | Línea de tiempo | Fechas de cada edición, con "hoy" | Excel: `fechas-naturalista.csv` |
| 7 | Itesodex | Las 526 especies de la lista oficial y cuáles faltan por fotografiar | Excel: `itesodex-naturalista.csv` |
| 8 | Galería | Premiadas, menciones y finalistas por edición | Excel: `galeria-naturalista.csv` + una foto por resultado en Documentos y Medios |
| 9 | Preguntas | Acordeón de preguntas frecuentes | clic en el texto: cada pregunta es un "Encabezado 3" y su respuesta va debajo |
| 10 | Sección | Contacto (el fragmento `seccion` de siempre, sin foto) | clic en el texto |
| 11 | Árbol QR | Árbol en la esquina inferior derecha; al abrirlo su copa se vuelve el QR de la página | Configuración > a dónde lleva y texto de la descarga |

El árbol QR cambia solo con el tema del sitio: es el árbol de la floración elegida (o la del mes; en lluvias, un tabachín bajo la lluvia) y de noche se oscurece con el modo oscuro. El QR siempre sale claro para que se pueda leer.

## Armarla en Liferay (una vez)

1. **Marco nuevo.** Pegar `web/fragmentos/marco/index.css` e `index.js` en el fragmento "Marco Campus Lab" y Propagar (Ver usos). Trae la base que usan los fragmentos nuevos; sin él se ven sin colores.
2. **Fragmentos nuevos** en el conjunto Campus Lab (Nuevo > Fragmento básico, pegar cada archivo en su pestaña): Portada, Cifras iNaturalist, Pasos, Concurso, Línea de tiempo, Itesodex, Galería, Preguntas, Árbol QR (carpetas con el mismo nombre en `web/fragmentos/`).
3. **Documentos y Medios**, carpeta pública de Campus Lab:
   - `fechas-naturalista.csv`, `galeria-naturalista.csv`, `itesodex-naturalista.csv` (de `catalogo/salida/liferay_subir/naturalista/`). Su URL corta queda como `/documents/d/campuslab/fechas-naturalista`, que es la que traen los fragmentos.
   - Las fotos de `catalogo/salida/liferay_subir/naturalista/fotos/` (una por resultado, 1600 px), con el mismo nombre de archivo. La página pide sola la versión de 1000 px (Adaptive Media).
4. **Página de contenido** nueva, URL amigable `/naturalista`, con la Master Page que tenga el Marco. Arrastrar los fragmentos en el orden de la tabla; en Sección (contacto) escribir los textos de `pagina.json` y quitar la foto en su Configuración.
5. Antes de publicar: revisar con `launch-checklist` (título, descripción e imagen para redes).

Para probar sin Liferay: `python web/scripts/vista_pagina.py web/contenidos/naturalista/pagina.json` y abrir `catalogo/salida/vistas/naturalista.html` (tiene una barra para cambiar floración y modo).

## Actualizar datos

Cada fragmento tiene su guía (qué se edita, columnas del CSV, qué hacer si algo sale mal) en `web/fragmentos/<fragmento>/README.md`, y los pasos para editar cualquier CSV están en `web/fragmentos/README.md`.

- **Fechas de la edición 2027:** abrir `fechas-naturalista.csv` en Excel, cambiar la fila de 2027 (fechas como `2026-11-23`; si solo se sabe el mes, `2026-11`), guardar como "CSV UTF-8" y subirlo como **nueva versión del mismo archivo**. Poner también las fechas en la Configuración del fragmento Concurso para la cuenta regresiva.
- **Al abrir la convocatoria:** Concurso > Configuración > etapa "Convocatoria abierta" y escribir la liga del formulario nuevo en el botón "Registrar mi foto" (la de 2025 era `https://forms.office.com/r/BnS1NGdmYk`).
- **Ganadores:** agregar filas a `galeria-naturalista.csv` (edicion, categoria, resultado, titulo, autor, especie, nombre_cientifico, foto, album). Sin correos ni datos de contacto.
- **Itesodex:** cuando se confirme la foto de una especie que se buscaba, cambiar su Estado a `Fotografiada` en `itesodex-naturalista.csv`. El script solo sembró los CSV una vez; volver a correrlo con `--forzar` pisa lo editado.

## Pendiente

- 11 de los 18 resultados de 2025 aún sin foto ("Foto por subir"): están en `Y:\Galería\...\Concurso Naturalista 2025\Participantes originales` (solo en la red del ITESO); faltan unir por autor y título.
- Resultados de 2023: por ahora solo el álbum de Facebook. Fuente: `Guion Naturalista ITESO 2023.pdf` y el Excel de evaluación 2023.
- Confirmar con Maya la respuesta sobre licencias en Preguntas (CC BY-NC y uso en sitios y exposiciones sin fines de lucro).
- Avisar a quienes aparecen en la galería antes de publicar.
- Redirigir las tres páginas viejas a esta (ver la propuesta).
