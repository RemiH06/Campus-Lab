# Fragmento "Línea de tiempo"

Las fechas de cada edición (convocatoria, finalistas, exposición, premiación) en una línea por año. Lo que ya pasó va relleno, lo que viene va punteado y una marca dice "Estás aquí". Sirve para cualquier calendario por ediciones o temporadas.

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Antetítulo, título, texto | Clic y escribir |
| Las fechas | En Excel: archivo `fechas-naturalista` de Documentos y Medios (pasos en "Editar una lista en CSV" de `web/fragmentos/README.md`) |
| De qué archivo lee | Configuración > URL del CSV (solo si se usa en otra página con otro archivo) |

## Columnas del CSV

| Columna | Qué va | Ejemplo |
|---|---|---|
| Edición | El año de la edición; agrupa las filas | `2027` |
| Desde | Fecha: año-mes-día, o año-mes si aún no hay día | `2026-11-23` o `2026-11` |
| Hasta | Opcional: fin de un periodo (convocatoria, exposición) | `2027-03-12` |
| Etapa | Nombre corto | `Convocatoria` |
| Detalle | Opcional: una frase | `Dos categorías: semiprofesional y celular.` |

El orden de las filas no importa: la página las ordena por fecha.

## Si algo sale mal

Una fila con la fecha mal escrita (por ejemplo `23/11/2026`) no aparece, y en el editor de páginas un aviso dice su número de fila en Excel.

## Para quien mantiene el código

Lee el CSV con `window.clCSV` del Marco (espera el evento `cl-base` si carga antes).
