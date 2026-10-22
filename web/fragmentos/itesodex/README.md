# Fragmento "Itesodex"

Todas las especies de la lista oficial del ITESO y cuáles ya tienen foto en el archivo de Campus Lab. Arriba, una barra por grupo; abajo, una tarjeta por especie con filtros y buscador. Abre mostrando las que se buscan, para invitar a fotografiarlas. Tiene la dirección `#itesodex`.

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Antetítulo, título, texto, nota final | Clic y escribir |
| Las especies | En Excel: archivo `itesodex-naturalista` de Documentos y Medios (pasos en "Editar una lista en CSV" de `web/fragmentos/README.md`) |
| Qué se ve al abrir la página | Configuración > "Qué se ve al abrir la página" |

## Columnas del CSV

| Columna | Qué va |
|---|---|
| Grupo | `Árboles`, `Aves`, `Orquídeas`, `Suculentas` o `Flores de La Primavera`. Un grupo nuevo aparece solo, con la silueta de árbol |
| Nombre común | Opcional |
| Nombre científico | Obligatorio. Sin autor: `Jacaranda mimosifolia`, no `Jacaranda mimosifolia D. Don` |
| Estado | `Fotografiada`, `Solo en iNaturalist` o `Se busca` |
| Fotos en Campus Lab | Opcional, un número |
| Observaciones en iNaturalist | Opcional, un número |
| Enlace a iNaturalist | Opcional: la liga a la especie, como `https://mexico.inaturalist.org/taxa/53344`. Con ella sale "Ver cómo es" (una foto de referencia de iNaturalist con su crédito) |
| Dónde buscar | Opcional, para árboles: jardines con cuántos hay, como `7 - Arboretum II (2)` |

## Las tareas de siempre

- **Alguien fotografió una especie que se buscaba:** cuando la foto ya está confirmada en el archivo, cambiar su Estado a `Fotografiada`. Si se sabe, poner cuántas fotos hay.
- **Alguien la registró en iNaturalist pero no hay foto en el archivo:** Estado `Solo en iNaturalist`.
- **Especie nueva en la lista oficial:** agregar una fila al final. El número que aparece en la tarjeta (#001, #002…) es el orden de la fila.
- **Una especie se quitó de la lista:** borrar su fila.

## Si algo sale mal

Una fila sin nombre científico, o con un estado que no es ninguno de los tres, no aparece. En el editor de páginas un aviso dice su número de fila en Excel.

## Para quien mantiene el código

El CSV se sembró una vez desde la base de datos con `python web/scripts/generar_naturalista.py` (cruce con iNaturalist del 13-oct y el inventario de árboles). Desde ahí **el CSV es la fuente de la verdad**: volver a sembrarlo con `--forzar` pisa lo que se haya editado a mano.
