# Fragmento "Mapa 3D de los territorios"

Una maqueta en 3D de cada territorio del ITESO, con selector arriba:

| Territorio | Qué se ve |
|---|---|
| Campus (Tlaquepaque) | Edificios, calles, andadores y canchas de OpenStreetMap; los 3,641 árboles del inventario con placa, cada uno a su **altura y copa reales** (los que florecen este mes, en su color de floración); 2,541 observaciones de Naturalista |
| Casa ITESO Clavigero | La manzana, las calles y los 82 árboles del jardín |
| Predios en el Bosque La Primavera | El **relieve real** (de 1,710 a 2,275 m), el contorno de los dos predios y 420 observaciones de Naturalista |

Se gira, se acerca y se mueve; al pasar sobre un árbol aparece su especie, placa, altura y copa, y un clic lleva a su ficha. Las observaciones llevan a iNaturalist. Se busca un árbol por número de placa, y tocar una etiqueta (un edificio, un predio) lleva a ese lugar. Territorio y placa quedan en la URL: las flechas del navegador regresan y la liga se puede compartir. En celular el mapa se mueve con dos dedos, para no atrapar el scroll de la página. Sigue el modo claro/oscuro del sitio y solo se dibuja cuando algo cambia (no gasta batería quieto).

## Piezas

| Pieza | Dónde va |
|---|---|
| `index.html`, `index.css`, `index.js`, `configuration.json` | Pestañas del fragmento (Diseño > Fragmentos > conjunto Campus Lab) |
| `web/rems_rework/mapa3d/dist/cl-mapa3d.js` (602 KB) | Documentos y Medios, con el nombre `cl-mapa3d.js` |
| `territorio-campus.json`, `territorio-clavigero.json`, `territorio-primavera.json` | Documentos y Medios (se generan en `reestructura/salida/liferay_subir/mapa3d/`) |
| `arboles.json` | Ya está en Documentos y Medios (el mismo del catálogo de árboles) |

El fragmento pide `cl-mapa3d.js` como texto y lo importa desde la memoria del navegador, así que funciona aunque Documentos y Medios no lo sirva con tipo de JavaScript. Si el navegador no tiene WebGL, se ve un aviso con liga al mapa 2D.

## Actualizar

- **Datos** (árboles nuevos, otra exportación del inventario, observaciones nuevas): `python web/scripts/generar_territorios_3d.py` y subir los tres `territorio-*.json` como nueva versión del mismo archivo. `--forzar` vuelve a descargar OpenStreetMap, el polígono de los predios y el relieve.
- **El motor** (`web/rems_rework/mapa3d/mapa3d.js`): en esa carpeta, `npm install` (una vez) y `npm run build`; subir `dist/cl-mapa3d.js` como nueva versión.
- **Probar sin Liferay:** desde la raíz del repo `python -m http.server 8048 --bind 127.0.0.1` y abrir `http://127.0.0.1:8048/web/rems_rework/mapa3d/vista_local.html`.

## Fuentes y créditos (se muestran al pie del mapa)

- Calles, edificios y canchas: © colaboradores de OpenStreetMap, licencia ODbL (obliga a dar el crédito, ya incluido).
- Árboles: inventario del ITESO 2014-2018 (ArcGIS).
- Observaciones: Naturalista ITESO (iNaturalist); sin nombres de usuario.
- Contorno de los predios: lugar 185911 de iNaturalist.
- Relieve: Terrain Tiles de AWS (Mapzen; SRTM y otras fuentes públicas).

## Límites conocidos

- OpenStreetMap no tiene la altura de casi ningún edificio del campus: se usan los pisos donde existen (11) y 7.5 m (dos pisos) en el resto.
- La Casa Clavigero no está dibujada como edificio en OpenStreetMap; se marca con su etiqueta. Se puede agregar en openstreetmap.org (cualquiera puede editar) y volver a generar.
- Los árboles con coordenada mala en el inventario (8 placas, ver CLAUDE.md) no aparecen hasta corregirlos en el recorrido.
