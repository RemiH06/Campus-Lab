# Fragmentos de Liferay

Cada carpeta es un fragmento del conjunto "Campus Lab".

| Fragmento | Qué es | Cómo se edita |
|---|---|---|
| `marco/` | Corrige header y footer del tema; va una vez en la Master Page | a mano (ver su README) |
| `seccion/` | Bloque con zonas editables sin código | a mano (ver su README) |
| `mapa3d/` | Mapa 3D de los territorios | a mano; el motor sale de `web/fuentes/mapa3d/` |
| `portada/`, `cifras-inat/`, `pasos/`, `concurso/`, `linea-tiempo/`, `itesodex/`, `galeria/`, `preguntas/`, `arbol-qr/` | Piezas de la landing Naturalista (y de cualquier página que las necesite). Usan la base de colores del Marco y leen sus listas de CSV en Documentos y Medios | a mano; cómo se arma la página en `web/contenidos/naturalista/README.md` |
| `prototipo-plantillas/`, `prototipo-componentes/` | Prototipos de prueba en `/temp` | **no a mano**: se regeneran con `web/scripts/preparar_para_liferay.py` desde `web/fuentes/prototipos/` |

| Archivo | Pestaña del fragmento |
|---|---|
| `index.html` | HTML |
| `index.css` | CSS |
| `index.js` | JavaScript |
| `configuration.json` | Configuración |

## Crear el fragmento (una vez)

1. Diseño > Fragmentos. Crear un conjunto llamado **Campus Lab** (si no existe).
2. Dentro del conjunto: Nuevo > Fragmento básico. Nombre: "Prototipo plantillas" (o "Prototipo componentes").
3. Pegar cada archivo en su pestaña y Publicar.

## Usarlo en una página

1. Constructor del sitio > Páginas > editar la página (por ejemplo `/temp`).
2. Quitar el Web Content Display que tenga.
3. En el panel de fragmentos, abrir el conjunto **Campus Lab** y arrastrar el fragmento.
4. Publicar la página.

El fragmento lee su JSON de `/documents/d/campuslab/prototipo-...`. Si algún día cambia la URL, se corrige sin código: seleccionar el fragmento en la página > Configuración > "URL del JSON de datos".

## Al cambiar un fragmento que ya está en una página

Pegar la versión nueva y publicar el fragmento **no cambia las páginas que ya lo usan**: siguen mostrando la versión anterior (confirmado el 21-oct en `/temp`, que siguió con el código viejo después de pegar el nuevo). Para que la página tome la nueva:

1. Editar la página, **quitar el fragmento y volverlo a colocar** desde el panel de fragmentos (no hace falta borrarlo de Diseño > Fragmentos), o bien Diseño > Fragmentos > menú del fragmento > Ver usos > seleccionar las páginas > Propagar.
2. Volver a poner su Configuración si se había cambiado, y los textos o fotos si se habían escrito sobre la página (al quitarlo se pierden).
3. Publicar la página.

Para saber qué versión está publicada sin entrar a Liferay: abrir la página y buscar en el código fuente (Ctrl+U) algo que solo tenga la versión nueva.
