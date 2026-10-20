# Campus Lab ITESO · activos digitales

Campus Lab trata el campus del ITESO como laboratorio vivo de sustentabilidad y biodiversidad. Este repositorio ordena sus tres fuentes de información: el SharePoint del proyecto, el volumen de fotos de biodiversidad (`Y:\Galería`, solo dentro de la red de ITESO) y el sitio público en Liferay (campuslab.iteso.mx).

Lo que hay aquí es código y documentación. Las fotos, la base de datos y cualquier archivo con datos de personas **no viven en el repositorio**: se piden a la coordinación de Campus Lab al recibir el proyecto.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `catalogo/` | Identificación de especies en las fotos, inventario de árboles y herramientas de revisión |
| `web/` | Todo lo que se publica en Liferay: fragmentos, sus fuentes, contenidos y scripts ([web/README.md](web/README.md)) |
| `experimentos/` | Primera etapa (inventario de SharePoint, escaneo y migración del volumen). Ya se corrió; solo se consulta |
| `docs/` | [Cumplimiento](docs/CUMPLIMIENTO.md) (derechos, datos personales, servicios externos) y [dependencias](docs/DEPENDENCIAS.md) |
| `BITACORA.md` | Resumen semanal del avance, en lenguaje no técnico |

Dentro de `catalogo/`:

| Carpeta | Qué hay |
|---|---|
| `comun/` | Rutas del proyecto y conexión a la base de datos, compartidas por todo lo demás |
| `notebooks/` | Pasos del proceso de identificación (Pl@ntNet, iNaturalist, agrupamiento por espécimen, resolución de nombres, renombrado, taxonomía GBIF) |
| `scripts/` | Cruce con las observaciones de Naturalista ITESO |
| `listas/` | Listas oficiales de especies (árboles, orquídeas, flores de La Primavera) |
| `herramientas/` | Pequeñas aplicaciones locales para revisar fotos en el navegador |

## Para empezar

1. Pedir la base de datos (`campuslab_volumen.db`) y colocarla en `experimentos/bd/`.
2. Copiar `catalogo/config_local.example.json` a `catalogo/config_local.json` y llenarlo (llave de Pl@ntNet, nombre de quien revisa, carpeta local de fotos si se trabaja fuera de la red de ITESO).
3. Python 3.11 o más reciente. Las herramientas usan `fastapi`, `uvicorn`, `pillow`, `numpy` y `requests`; los notebooks, además, `pandas` y `openpyxl`.

Cada herramienta se abre con `python backend.py` desde su carpeta y queda en `http://localhost:<puerto>`:

| Herramienta | Puerto | Para qué |
|---|---|---|
| `revision_web` | 8040 | Confirmar o rechazar la especie sugerida de una foto |
| `galeria_animal_en_planta` | 8042 | Marcar qué hay en cada foto (ave, insecto, planta…) |
| `clustering_especimen` | 8043 | Agrupar fotos del mismo ejemplar |
| `buscar_foto` | 8044 | Ver una foto por número, con sus vecinas |
| `galeria_especies` | 8045 | Catálogo de fotos por especie, género o grupo |
| `revision_grupos` | 8046 | Confirmar la especie de un grupo completo |
| `partes_arbol` | 8047 | Etiquetar qué parte del árbol muestra cada foto |

## Reglas

- **Ninguna imagen va al repositorio**, ni siquiera ignorada por git: por tamaño y por derechos de autor. Las fotos públicas viven en Documentos y Medios de Liferay.
- **Nada con nombres, correos o rutas de una computadora va a git.** Por eso `config_local.json`, `catalogo/salida/`, `experimentos/bd/` y similares están en `.gitignore`. Los notebooks se guardan sin salidas (`jupyter nbconvert --clear-output --inplace <archivo>.ipynb`).
- **Todo proceso que cambia muchas cosas a la vez se corre primero en seco**: genera un plan en Excel y solo actúa al cambiar a mano su bandera `EJECUTAR_..._REAL`. Se puede cortar a la mitad y volver a correr.
- **Una decisión humana nunca se pisa sola**: ningún proceso automático vuelve a confirmar una foto que alguien ya rechazó.
- Las carpetas sincronizadas de OneDrive/SharePoint solo se leen; nunca se mueve ni se borra nada ahí.
