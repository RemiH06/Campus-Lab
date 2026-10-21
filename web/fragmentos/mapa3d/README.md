# Fragmento "Mapa 3D de los territorios"

Una maqueta en 3D de cada territorio del ITESO, con selector arriba. **Complementa a los mapas que ya existen, no los reemplaza:** el mapa 2D del catálogo (búsqueda por placa, árboles sin foto) y el mapa de ArcGIS del inventario siguen siendo los de trabajo; el 3D sirve para explorar y para presentar.

| Territorio | Qué se ve |
|---|---|
| Campus (Tlaquepaque) | Edificios, calles, andadores y canchas de OpenStreetMap; los 3,641 árboles del inventario con placa, cada uno a su **altura y copa reales** (los que florecen este mes, en su color de floración); las observaciones de Naturalista (unas 2,900) |
| Casa ITESO Clavigero | La manzana, las calles y los árboles del jardín |
| Predios en el Bosque La Primavera | El **relieve real** (de 1,710 a 2,275 m), el contorno de los dos predios y las observaciones de Naturalista |

Se gira, se acerca y se mueve; al pasar sobre un árbol aparece su especie, placa, altura y copa, y un clic lleva a su ficha. Las observaciones llevan a iNaturalist. Se busca un árbol por número de placa, y tocar una etiqueta (un edificio, un predio) lleva a ese lugar. Territorio y placa quedan en la URL: las flechas del navegador regresan y la liga se puede compartir. En celular el mapa se mueve con dos dedos, para no atrapar el scroll de la página. Sigue el modo claro/oscuro del sitio y solo se dibuja cuando algo cambia (no gasta batería quieto).

## De dónde sale cada cosa

| Qué | De dónde | Quién lo actualiza |
|---|---|---|
| Árboles | `inventario-arboles.csv` en Documentos y Medios | Cualquiera, en Excel (ver abajo) |
| Observaciones | iNaturalist, en vivo, por el rectángulo del territorio; cada navegador las guarda 24 h | Nadie: se actualizan solas. Si iNaturalist no responde, se ven las guardadas en el `territorio-*.json` |
| Edificios, calles, relieve, contorno | `territorio-*.json` | Solo si cambia la geografía (ver "Actualizar") |

El motor (600 KB) y los datos se descargan solo cuando el mapa está a punto de entrar en pantalla, así no le pesan a quien no baja hasta él.

## Piezas

| Pieza | Dónde va |
|---|---|
| `index.html`, `index.css`, `index.js`, `configuration.json` | Pestañas del fragmento (Diseño > Fragmentos > conjunto Campus Lab) |
| `web/fuentes/mapa3d/dist/cl-mapa3d.js` (602 KB) | Documentos y Medios, con el nombre `cl-mapa3d.js` |
| `territorio-campus.json`, `territorio-clavigero.json`, `territorio-primavera.json` | Documentos y Medios (se generan en `catalogo/salida/liferay_subir/mapa3d/`) |
| `inventario-arboles.csv` | Documentos y Medios (la primera versión la genera `web/scripts/generar_inventario_csv.py` en `catalogo/salida/liferay_subir/arboles/`) |

Los cinco archivos van en Documentos y Medios del sitio, con permiso de ver para Invitado (público), y con esos nombres: la URL corta queda `/documents/d/campuslab/<nombre sin extensión>`. Si falta alguno o no es público, quien tiene sesión iniciada ve en el mapa cuál falta; quien visita solo ve "El mapa 3D no está disponible por ahora".

El fragmento pide `cl-mapa3d.js` como texto y lo importa desde la memoria del navegador, así que funciona aunque Documentos y Medios no lo sirva con tipo de JavaScript. Si el navegador no tiene WebGL, se ve un aviso con liga al mapa 2D.

## Actualizar

- **Árboles (sin conocimientos técnicos):** en Documentos y Medios, descargar `inventario-arboles`, abrirlo en Excel, editar (una fila por árbol; `estado` "derribado" o "no encontrado" lo quita del mapa) y guardarlo como CSV. Subirlo con "Nueva versión" sobre el mismo archivo, nunca como archivo nuevo (si no, cambia su URL). Excel puede guardarlo con `;` o `,` y con o sin "UTF-8": el mapa lee cualquiera. Con sesión iniciada, el mapa avisa qué filas no pudo usar (sin placa, sin coordenada, placa repetida).
- **Geografía** (un edificio nuevo dibujado en openstreetmap.org, refrescar el respaldo de observaciones): `python web/scripts/generar_territorios_3d.py` y subir los tres `territorio-*.json` como nueva versión. `--forzar` vuelve a descargar OpenStreetMap, el polígono de los predios y el relieve.
- **El motor** (`web/fuentes/mapa3d/mapa3d.js`): en esa carpeta, `npm install` (una vez) y `npm run build`; subir `dist/cl-mapa3d.js` como nueva versión.
- **Probar sin Liferay:** desde la raíz del repo `python -m http.server 8048 --bind 127.0.0.1` y abrir `http://127.0.0.1:8048/web/fuentes/mapa3d/vista_local.html`.

## Fuentes y créditos (se muestran al pie del mapa)

- Calles, edificios y canchas: © colaboradores de OpenStreetMap, licencia ODbL (obliga a dar el crédito, ya incluido).
- Árboles: inventario del ITESO (`inventario-arboles.csv`, sembrado desde ArcGIS 2014-2018).
- Observaciones: Naturalista ITESO (iNaturalist); sin nombres de usuario.
- Contorno de los predios: lugar 185911 de iNaturalist.
- Relieve: Terrain Tiles de AWS (Mapzen; SRTM y otras fuentes públicas).

## Límites conocidos

- OpenStreetMap no tiene la altura de casi ningún edificio del campus: se usan los pisos donde existen (11) y 7.5 m (dos pisos) en el resto.
- La Casa Clavigero no está dibujada como edificio en OpenStreetMap; se marca con su etiqueta. Se puede agregar en openstreetmap.org (cualquiera puede editar) y volver a generar.
- Los árboles con coordenada mala en el inventario (8 placas, ver CLAUDE.md) no aparecen hasta corregirlos en el recorrido.
