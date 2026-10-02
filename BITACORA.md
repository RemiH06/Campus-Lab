# Bitácora — Reestructura de activos digitales, Campus Lab

Registro semanal de avance, en el formato que pide ITESO para la beca (Tareas y aprendizajes / Compromisos para la siguiente semana, máx. 500 caracteres cada uno). Complementa al `CLAUDE.md`, que es la referencia técnica del proyecto — esta bitácora es la versión legible para quien no vaya a tocar código.

## Semana 1

**Tareas y aprendizajes**

Se levantó el inventario de SharePoint (11,992 elementos), se propuso una taxonomía cruzada con el Miro y se detectaron consolidaciones (Concurso Naturalista, sitio de aves) y duplicados por nombre+tamaño y por carpeta, documentado en un notebook reproducible. Se inició el escaneo del volumen de fotos con un parser de autor/especie por ruta. Aprendizaje: diagnosticar bloqueos de entorno y priorizar metadatos sobre contenido cuando bastan para decidir con confianza.

**Compromisos para la siguiente semana**

Correr el escaneo completo del volumen (FOTOS, ORQUIDEAS_GUIA) en Y:\Galería, revisar casos de baja/media confianza en autor y especie, y decidir el triage hacia las tablas normalizadas de la base de datos. Obtener acceso a Liferay el martes y revisar el instructivo para definir si hay API o si la publicación será manual. Confirmar con Maya si el repositorio será público o privado antes de crearlo. Avanzar en el cruce SharePoint-volumen y el README del proyecto.

## Semana 2

**Tareas y aprendizajes**

Se corrió la migración completa del volumen de fotos (6,074 archivos), con la convención RAMA-autor-especie-hash y hash determinístico (SHA1 de la ruta original) para evitar duplicados al repetir el proceso. Se obtuvo acceso a Liferay. Se construyó la interfaz de revisión humana de especies (confirmar/rechazar por texto, con auditoría y campos de familia/género). Aprendizaje: normalizar acentos igual en ambos lados de una comparación, o los nombres comunes nunca coinciden.

**Compromisos para la siguiente semana**

Explorar a fondo el panel de Liferay para entender permisos reales y si existe API o solo edición manual. Seguir resolviendo la cola de especies pendientes de revisión. Confirmar con Maya si el repositorio será público o privado. Avanzar el cruce SharePoint-volumen y esbozar el README/bitácora del proyecto.

## Semana 3

**Tareas y aprendizajes**

Al explorar Liferay: sin permisos de administrador; la exportación completa (LAR) falla por una referencia rota en una plantilla; se pidió a la OSI, vía Brenda, el export y más permisos. En paralelo: bloques de HTML reales (no inventados) para Espacios > Arboretum, entregada y en espera de aprobación, más un script de redimensionado de imágenes. En fotos: 943 resueltas por nombre común (61 especies), triage CLIP planta/animal/tipo sobre el resto, y renombrado físico de esas 943 en el volumen.

**Compromisos para la siguiente semana**

Usar la exportación de Liferay en cuanto la entregue la OSI (si la entrega). Terminar de construir y usar el nuevo revisor web (reemplaza el notebook) para la cola de especies pendientes, incluida la propagación por grupo de espécimen. Actualizar el filtro de candidatas de Pl@ntNet para aprovechar la clasificación CLIP. Seguir con más páginas de espacios (Huerto, Jardín meditativo) con el mismo enfoque de bloques reales.

## Semana 4

**Tareas y aprendizajes**

Se terminó y movió a producción el revisor web de especies (puerto 8040), con propagación por grupo de espécimen. Se resolvió la cola de Pl@ntNet por lotes y se corrigieron nombres comunes mal resueltos a nombre científico. Aprendizaje costoso: cualquier re-resolución automática debe excluir fotos ya rechazadas a mano, o un rechazo se revierte solo (pasó con 19 fotos reales, revertidas).

**Compromisos para la siguiente semana**

Construir la identificación por visión (BioCLIP/iNaturalist) para lo que Pl@ntNet no cubre (animales), y una herramienta de revisión humana para todo el catálogo, no solo plantas. Empezar a explorar agrupar fotos del mismo espécimen dentro de un género para reducir revisión foto por foto.

## Semana 5

**Tareas y aprendizajes**

Se construyó el pipeline de identificación con la API de visión de iNaturalist (con manejo de límite de peticiones y refresco de token) y la herramienta de revisión ave/insecto/mamífero/hongo/anfibio_reptil/planta (puerto 8042) para todo el catálogo. Se descubrieron y excluyeron 167 archivos no-imagen (RAW/video/documentos) colados en el escaneo original, y 18 fotos genuinamente corruptas (0 bytes). Se construyó el agrupamiento por espécimen dentro de un género (puerto 8043).

**Compromisos para la siguiente semana**

Decidir y ejecutar la estrategia de agrupar primero y confirmar por grupo completo después, en vez de foto por foto. Extender el agrupamiento para cubrir también las fotos de animales identificadas por iNaturalist, no solo plantas. Construir un buscador de foto individual por número para casos puntuales.

## Semana 6

**Tareas y aprendizajes**

Se adoptó agrupar antes de confirmar, con preconfirmado automático por umbral de similitud. Se construyó el buscador de foto por ID (8044) y un barrido de duplicados exactos en todo el catálogo (3,588 fotos), que reveló el patrón de "doble sujeto" (ave y planta en la misma escena, cada una con su propia fila). Se armó un catálogo navegable por especie/género/grupo con filtro de tamaño (8045) y un reporte de duplicados de SharePoint con links reales para Maya.

**Compromisos para la siguiente semana**

Seguir agrupando géneros pendientes en el puerto 8043, revisando de paso los casos de conflicto (2+ especies en un mismo grupo) y las etiquetas de género que quedan desincronizadas al confirmar una especie por otra vía.

## Semana 7

**Tareas y aprendizajes**

Se corrigió que el género no se sincronizaba al confirmar especie por otra vía. Se construyó un chequeo geográfico contra GBIF que validó casi todas las decisiones previas. Se construyó el confirmador de grupo completo (8046), con limbo por orden/familia y panel de especies similares. Pistas en el nombre de archivo y por OCR permitieron confirmar cientos de fotos. Se retomó el inventario de árboles: se encontró el mapa ArcGIS existente y se georreferenció el Jardín Contemplativo.

**Compromisos para la siguiente semana**

Confirmar los grupos de espécimen pendientes que no sean orquídeas ni suculentas (esos se revisan aparte, con ayuda de Hugo de Alba). Enviar el correo a Miriam Andrade para identificación de suculentas. Reunir y capturar a mano las placas metálicas sueltas de árboles antes de seguir con el inventario maestro.
