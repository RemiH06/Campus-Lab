# Fragmento "Concurso Naturalista"

El bloque del concurso de fotografía. Muestra una cosa distinta según la etapa, con una ficha de datos a la derecha y las bases completas plegadas debajo. Tiene la dirección `#concurso`: los botones "Participa" de la página llevan aquí.

## Etapas (Configuración del fragmento > "Qué se muestra")

| Etapa | Cuándo | Qué muestra |
|---|---|---|
| Próxima edición | Entre concursos | Cuándo sale la convocatoria y el botón para registrar especies desde ya. Con fecha de apertura, cuenta los días que faltan |
| Convocatoria abierta | Mientras se reciben fotos | Los 2 pasos para registrar una foto y el botón grande **"Registrar mi foto"**. Con fecha de cierre, cuenta los días que quedan |
| Cerrada, el jurado está revisando | Del cierre a los resultados | Un aviso de que ya cerró |
| Resultados | Después de la premiación | Un botón a la galería |

Cada etapa tiene **sus propios textos**: al cambiar de etapa aparecen los que se escribieron para esa etapa la vez anterior. Revisarlos antes de publicar.

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Textos de la etapa | Clic y escribir |
| **Liga del formulario de registro** | Etapa "Convocatoria abierta" > clic en el botón "Registrar mi foto" > pegar la liga del formulario nuevo. La de 2025 era `https://forms.office.com/r/BnS1NGdmYk`; cada edición tiene la suya |
| Ficha (quién participa, dónde, categorías, fotos) | Clic y escribir |
| Bases completas | Clic en "Bases completas" para abrirlas > clic en el texto. Cambiar también el título (por ejemplo "Bases completas (edición 2027)") |
| Fechas de apertura y cierre | Configuración. Se escriben año-mes-día: `2026-11-23` |

## Si algo sale mal

En el editor de páginas, un aviso punteado dice qué revisar: una fecha mal escrita, la convocatoria abierta sin fecha de cierre o una fecha de cierre que ya pasó. Ese aviso no lo ve quien visita la página.

## Para quien mantiene el código

Las etapas son bloques `[#if configuration.etapa == "…"]` de FreeMarker, cada uno con sus zonas editables. El JavaScript solo calcula la cuenta regresiva, los avisos y abre las bases con `#bases`.
