# Fragmento "Galería"

Las fotos premiadas de cada edición del concurso: una pestaña por año, las de 1er y 2º lugar grandes, luego menciones honoríficas y finalistas. Al tocar una foto se abre en grande. Tiene la dirección `#galeria`.

## Qué se edita y cómo

| Qué | Cómo |
|---|---|
| Antetítulo, título, texto | Clic y escribir |
| Los resultados | En Excel: archivo `galeria-naturalista` de Documentos y Medios (pasos en "Editar una lista en CSV" de `web/fragmentos/README.md`) |
| Las fotos | Subirlas a Documentos y Medios, carpeta de Campus Lab, y escribir su nombre en la columna Foto |

## Columnas del CSV

| Columna | Qué va | Ejemplo |
|---|---|---|
| Edición | Año; una pestaña por año | `2025` |
| Categoría | Opcional | `Semiprofesional` |
| Resultado | Decide en qué grupo sale: con "lugar" va en Premiadas, con "Mención" en Menciones, con "Finalista" en Finalistas | `1er lugar` |
| Título | El título de la foto | `Polinizando` |
| Autor | Nombre completo, como aparece en los resultados. **Sin correos ni teléfonos** | |
| Especie | Nombre común | `Abeja de sudor a rayas` |
| Nombre científico | Opcional | `Agapostemon sp.` |
| Foto | El nombre del archivo en Documentos y Medios (con o sin `.jpg`). Vacía: sale "Foto por subir" | `naturalista-2025-02-abeja-de-sudor` |
| Álbum | Opcional, basta en una fila de la edición: liga al álbum completo | |

Una fila con solo Edición y Álbum sirve para una edición cuyos resultados aún no se capturan: sale la pestaña con la liga al álbum.

## Sobre las fotos

- Una foto por resultado, tal cual o reducida a unos 1600 px (mejor: así no se publica el original completo). La página pide sola una versión de 1000 px, así que carga rápido aunque el archivo pese más.
- El nombre del archivo, sin espacios ni acentos (`naturalista-2027-01-colibri`), porque también es su dirección.
- **Antes de publicar, avisar a cada autor** que su foto va a estar en la página.

## Si algo sale mal

- "Foto por subir" aunque la foto ya está: revisar que el nombre en la columna Foto sea igual al del archivo.
- Una fila sin Edición no aparece, y en el editor de páginas un aviso dice su número de fila.

## Para quien mantiene el código

La foto se pide como `<carpeta><nombre><terminación><variante>` (Configuración); la variante por omisión es `?imagePreview=1` de Adaptive Media (1000 px, confirmado sobre la URL corta el 22-oct). Si falla, se pide el archivo sin variante. Lee el CSV con `window.clCSV` del Marco.
