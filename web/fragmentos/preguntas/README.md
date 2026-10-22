# Fragmento "Preguntas"

Preguntas frecuentes en acordeón: se ve la lista de preguntas y cada respuesta se abre al tocarla. Sirve en cualquier página.

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Antetítulo, título, frase de ayuda | Clic y escribir |
| Preguntas y respuestas | Clic en el texto de la derecha y escribir |

**La única regla:** cada pregunta se marca como **Encabezado 3** (en la barra que aparece al escribir, el menú de estilos > "Encabezado 3"; también funcionan el 2 y el 4). Todo lo que va debajo, hasta la siguiente pregunta, es su respuesta: puede tener varios párrafos, listas, negritas y ligas.

- Pregunta nueva: escribir la pregunta, marcarla como Encabezado 3, Enter y escribir la respuesta.
- Si una pregunta se escribe en negritas en lugar de Encabezado 3, en la página no se separa de la anterior: queda pegada a la respuesta de arriba.

En el editor se ve como texto normal (para poder escribir); el acordeón solo aparece en la página publicada.

## Para quien mantiene el código

El JavaScript convierte cada `h2`-`h4` y lo que le sigue en un `<details>`. Sin JavaScript todo se lee como texto.
