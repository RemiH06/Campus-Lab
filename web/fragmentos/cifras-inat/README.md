# Fragmento "Cifras iNaturalist"

Un texto a la izquierda y, a la derecha, tres cifras de un proyecto de iNaturalist que se actualizan solas: observaciones, especies y personas. En la landing Naturalista es la sección "Qué es Naturalista ITESO".

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Antetítulo, título, texto, botón | Clic y escribir (el texto admite negritas y ligas) |
| De qué proyecto son las cifras | Seleccionar el fragmento > Configuración > número del proyecto. Es el número que aparece en la página del proyecto en iNaturalist. Naturalista ITESO es 146508 |

Las cifras **no se escriben**: se piden a iNaturalist cuando alguien llega a esa parte de la página y se guardan un día en su navegador. Debajo dice la fecha de los datos.

## Si algo sale mal

- Si iNaturalist no responde, se ven las cifras con las que se armó la página (octubre de 2026). No es un error de la página.
- Si las cifras no corresponden, revisar el número del proyecto en la Configuración.

## Para quien mantiene el código

API abierta de iNaturalist, sin cuenta: `/v1/observations`, `/species_counts` y `/observers` con `per_page=0`. Se guarda en `localStorage` (`cl-cifras-<proyecto>`) 24 h.
