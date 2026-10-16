# Fragmentos de prueba (camino B)

Cada carpeta es un fragmento de Liferay. Se generan con `web/camino_b/preparar_para_liferay.py`; no se editan a mano.

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

Si se cambia el fragmento (pegar una versión nueva y publicar), Liferay pregunta si se propaga a las páginas que lo usan.
