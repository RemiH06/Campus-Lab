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

*En curso.*
