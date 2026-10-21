# Árbol de voxeles sobre su código QR (ICQR)

- Fuente: Louis Raillé (@louis_rlee), https://www.instagram.com/reel/Dee1YrKocWA/, visto el 21-oct-2026
- Formato: reel, ~12 s, sin voz

## Idea central
Cualquier enlace se vuelve un árbol de cubos en vista isométrica cuyo suelo es el código QR de ese enlace. Al tocar el árbol, la vista gira a cenital, el árbol se pliega y queda un QR que sí se escanea.

## Recursos
| Recurso | Qué es | Verificado | Enlace |
|---|---|---|---|
| ICQR | La herramienta del reel (el autor dice que es de código abierto y la manda por comentario) | No | (por comentario en el reel) |

## Texto en pantalla
Selector de temporada (Spring, Summer, Autumn), muestras de color de la copa, botón de sonido, campo de URL y botón de exportar. Pista: "Tap the tree to see QR code".

## Aplicación
- Campus Lab, prototipo de componentes, #15 "Árbol con su QR" (hecho el 21-oct): la especie elige el color de la copa, las temporadas son las de Guadalajara (floración, lluvias, secas), el QR lleva a la ficha `/w/<especie>` y "Descargar QR" baja un PNG para letreros y placas. Canvas sin librerías; el generador de QR es propio y se verificó con un lector real (zxing). Sin sonido. (inferido)
- Letreros físicos de los jardines: el mismo QR del componente sirve para imprimir. (inferido)
