# Mapa de cumplimiento y documentación

Estado al 20 de octubre de 2026. Para revisiones de derechos, datos personales, seguridad o auditoría, y para quien continúe el proyecto. Cada tema dice qué hay, dónde está documentado y qué falta. Sin nombres de personas a propósito (el repositorio puede volverse público); los nombres viven en documentos internos fuera de git.

## Resumen

| Tema | Estado | Dónde está | Lo más urgente |
|---|---|---|---|
| Derechos de las fotos propias | Parcial | Base de datos (`fotos.autor_id`), carpetas de autor del volumen | Solo 22 % de las fotos confirmadas tiene autor registrado |
| Fotos de terceros (iNaturalist, concurso) | Parcial | Tabla `inat_fotos` (licencia por foto), convocatoria del concurso | Confirmar si la convocatoria cede derechos de uso a ITESO |
| Datos personales | Parcial | Carpetas `perso/`, `salida/`, `entrada/` (fuera de git) | Copias locales en una computadora personal |
| Licencias de software y datos | Completo | [docs/DEPENDENCIAS.md](DEPENDENCIAS.md) | Elegir licencia del repositorio si se publica |
| Servicios externos | Completo en inventario, falta revisar términos | Esta página | Términos de Pl@ntNet e iNaturalist para fotos enviadas |
| Uso de inteligencia artificial | Sin documentar formalmente | Esta página | Declararlo y revisar contra la política de ITESO |
| Seguridad (credenciales, accesos) | Bien en el repositorio | `.gitignore`, `config_local.json` | Traspaso de accesos al terminar la beca |
| Accesibilidad | Parcial | READMEs de cada fragmento | Revisión completa con lector de pantalla |
| Documentación técnica y traspaso | Parcial | `README.md` (20-oct), `BITACORA.md`, READMEs; `CLAUDE.md` e `HISTORIAL.md` fuera de git | Las reglas técnicas y los aprendizajes completos todavía no están en el repositorio |

## Derechos de las fotos

- **Fotos del volumen de Campus Lab:** 5,969 registros, 1,671 con autor identificado (28 %). De las 4,038 confirmadas, 897 tienen autor (22 %). La convención de nombres guarda el autor cuando se conoce, pero muchas fotos heredadas llegaron sin él.
- **Concurso Naturalista:** la convocatoria 2025 pedía registrar cada foto en iNaturalist con licencia Creative Commons (CC BY-NC sugerida). Una licencia no comercial con crédito permite el uso institucional de difusión, pero **no hay registro de una cesión expresa de derechos a ITESO**; antes de imprimir (carteles, lonas) conviene avisar a cada autor. Las fotos de promoción 2025 tienen su tabla de créditos (`catalogo/salida/naturalista_2025_promo/`).
- **Fotos de iNaturalist del proyecto Naturalista ITESO:** 4,499 fotos. Licencias: CC BY-NC 3,464; sin licencia (todos los derechos reservados) 970; CC BY-NC-SA 60; CC BY 3; CC0 2. **Las 970 sin licencia no se pueden publicar** sin permiso de su autor; las demás, solo con crédito y sin fines comerciales.
- **Contenido de terceros en SharePoint:** la carpeta de ilustraciones de *Birds of the World* (obra protegida) no debe publicarse; está marcada para revisión.
- **Regla:** toda imagen que se publique debe tener anotados su origen, su autor y su licencia. Ante cualquier reclamo de derechos, no responder ni pagar sin el visto bueno de Jurídico de ITESO.

## Datos personales

- **Qué hay:** nombres de autores de fotos; en los registros del concurso, también correos, teléfonos y fechas de nacimiento de participantes; correos de especialistas; registros de jardinería.
- **Dónde:** SharePoint de ITESO (origen), una copia local en la computadora de la becaria y las carpetas `perso/`, `salida/` y `entrada/` del proyecto. Todas están excluidas de git; se verificó el 20 de octubre que ningún archivo con datos personales esté en el repositorio ni en su historial.
- **Lo que se publica:** solo el nombre del autor junto a su foto, como crédito. El mapa 3D muestra observaciones de iNaturalist sin nombre de usuario.
- **Pendiente:** al terminar la beca, borrar las copias locales y dejar todo solo en el SharePoint de ITESO. Revisar con la coordinación si el aviso de privacidad del concurso cubre el uso de los datos más allá del certamen (Ley Federal de Protección de Datos Personales en Posesión de los Particulares).

## Servicios externos

| Servicio | Para qué | Qué se le envía | Pendiente |
|---|---|---|---|
| Pl@ntNet | Sugerir especie de plantas | 1,604 fotos (redimensionadas) | Revisar sus términos sobre las imágenes recibidas |
| iNaturalist (visión) | Sugerir especie | 3,129 fotos | Igual |
| iNaturalist (lectura), GBIF | Nombres, observaciones, distribución | Solo nombres científicos y coordenadas | Ninguno |
| OpenStreetMap (Overpass), Terrain Tiles de AWS | Mapa 3D | Solo coordenadas de la zona | Crédito ODbL ya puesto en el mapa |

Ninguno se llama desde el sitio público: solo al preparar datos.

## Uso de inteligencia artificial

- **Identificación de especies:** Pl@ntNet, la visión de iNaturalist y BioCLIP (este último corre en una computadora propia) **solo sugieren**; ninguna identificación se publica sin confirmación humana o de especialista, y cada decisión queda auditada en la tabla `identificaciones_revisadas` (quién, cuándo, qué).
- **Asistente de programación y documentación:** el código, los scripts y buena parte de la documentación se escribieron con Claude (Anthropic) mediante Claude Code. Durante el trabajo, el asistente leyó archivos del proyecto, incluidos algunos con datos personales (hojas del concurso, directorios). **Pendiente:** declararlo formalmente y revisarlo contra la política de ITESO sobre uso de IA y datos personales.

## Seguridad

- Credenciales (llaves de API, tokens) solo en `config_local.json`, excluido de git. Sin secretos en el repositorio ni en su historial (búsqueda del 20 de octubre).
- El sitio público no carga nada de terceros salvo lo que ya trae el tema de ITESO (ver DEPENDENCIAS.md).
- **Pendiente:** el acceso a Liferay y a SharePoint es personal de la becaria; al terminar, la coordinación debe dar los permisos a quien siga, sin compartir contraseñas.

## Accesibilidad

Se verificó el contraste (WCAG AA o mejor) de toda paleta nueva, se agregaron textos para lectores de pantalla donde el tema no los tenía, todo funciona con teclado, sin JavaScript queda legible y se respeta "reducir movimiento". **Pendiente:** una revisión completa con lector de pantalla (NVDA o VoiceOver).

## Documentación y traspaso

| Documento | Para quién | En git |
|---|---|---|
| `BITACORA.md` | Coordinación, beca (resumen semanal) | Sí |
| `docs/DEPENDENCIAS.md` | Revisión de dependencias y costos | Sí |
| READMEs de cada fragmento y herramienta | Quien mantenga el sitio | Sí |
| `CLAUDE.md` (referencia técnica completa, decisiones, bugs resueltos) | Quien continúe el proyecto | **No** (tiene nombres reales) |
| Directorio de contactos, correos con especialistas | Coordinación | No (datos personales) |

**Pendiente principal:** preparar una versión de `CLAUDE.md` sin datos personales que sí viva en el repositorio, para que el traspaso no dependa de una copia local.

## Créditos que el proyecto debe dar

- Fotos: a cada autor, siempre que se publique su foto.
- Mapas: "© colaboradores de OpenStreetMap" (ODbL).
- Observaciones: Naturalista ITESO / iNaturalist, con el autor de cada foto si se publica.
- Inventario de árboles: levantamiento 2014-2018 del ITESO.
- Identificaciones confirmadas por especialistas: anotadas por foto en la base de datos (`fuente_validacion`).

## Pendientes, en orden

- [ ] Versión de `CLAUDE.md` sin datos personales dentro del repositorio (el `README.md` del 20-oct cubre estructura, arranque y reglas; faltan los aprendizajes y la referencia de la base de datos).
- [ ] Declarar el uso de IA y revisarlo con la política de ITESO.
- [ ] Revisar si el concurso cede derechos de uso a ITESO; si no, agregarlo a la convocatoria 2027.
- [ ] Completar la autoría de las fotos confirmadas (hoy 22 %).
- [ ] Revisar los términos de Pl@ntNet e iNaturalist sobre las fotos enviadas.
- [ ] Decidir si el repositorio es público y, en ese caso, su licencia.
- [ ] Al terminar la beca: borrar copias locales con datos personales y traspasar accesos por la vía institucional.
- [ ] Revisión con lector de pantalla.
