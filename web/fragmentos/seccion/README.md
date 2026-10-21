# Fragmento "Sección Campus Lab" (prueba de edición sin código)

Un bloque de título, texto, botón y foto que cualquier persona edita **desde el editor de páginas, sin tocar código**: hace clic sobre el texto y escribe, o hace clic en la foto y elige otra de Documentos y Medios. El diseño (colores, tipografía, acomodo, modo claro/oscuro) no se puede romper desde ahí. Es la prueba del pendiente "edición de contenido sin código"; si funciona, todos los fragmentos del rework se arman igual.

| Archivo | Pestaña del fragmento |
|---|---|
| `index.html` | HTML |
| `index.css` | CSS |
| `index.js` | JavaScript |
| `configuration.json` | Configuración |

## Qué se edita y cómo

| Qué | Cómo, en el editor de páginas |
|---|---|
| Antetítulo, título | Clic sobre el texto y escribir |
| Texto | Clic y escribir; la barra que aparece permite negritas, listas y ligas |
| Botón | Clic: cambiar el texto y la liga a donde lleva |
| Foto | Clic en la foto > elegir una de Documentos y Medios (o subir una) |
| Paleta de floración, mostrar foto o botón, lado de la foto | Seleccionar el fragmento > pestaña de Configuración (listas y casillas) |

"La del sitio" usa la floración que la persona eligió en cualquier selector del sitio (el de los prototipos, el del catálogo) y, si no eligió ninguna, la del mes según el calendario. Las demás opciones fijan una paleta para esta sección.

El modo claro/oscuro lo pone el **Marco** (hay que tenerlo en la página o en la Master Page): la sección lo sigue sola, también cuando alguien usa el botón de modo del Marco o el de un prototipo.

## Editar el texto desde un Contenido Web (opcional)

En vez de escribir sobre la página, cada zona editable se puede **mapear** a un campo de un Contenido Web: seleccionar la zona > "Mapeo" > elegir el Contenido Web y el campo. Así el texto se cambia en el formulario de Contenido Web de siempre y la página lo muestra con este diseño. Hace falta un Contenido Web con una Estructura que tenga esos campos (título, texto, imagen); falta confirmar si la cuenta de Campus Lab puede crear Estructuras.

## Crear el fragmento

1. Diseño > Fragmentos > conjunto **Campus Lab** > Nuevo > Fragmento básico. Nombre: "Sección Campus Lab".
2. Pegar cada archivo en su pestaña (incluida Configuración) y Publicar.
3. En cualquier página de contenido: arrastrarlo desde el panel de fragmentos, editar el texto y publicar.

Liferay procesa las partes entre `[#if …]` y `${configuration.…}` (FreeMarker, activo por defecto en los fragmentos de 7.4). Si al pegar el HTML aparecen como texto, avisar: se cambian por JavaScript.

## Pendiente

Por ahora trae sus propios colores. En el rework, la base común (colores, tipografía, paletas) vivirá en el Marco, que va en todas las páginas por la Master Page, y cada fragmento atómico solo traerá su acomodo.
