# Fragmento "Marco Campus Lab"

Corrige el header y el footer del tema ITESO-4 **encima**, sin reemplazarlos: los pone el tema en todas las páginas (Contenido Web "Navegación" 351492, `footer788792`, `footerbotton788792`) y así se conservan sus enlaces, Google Tag Manager y la tipografía Degular. Se coloca una sola vez en la Master Page; en la página publicada no se ve nada propio del fragmento.

| Archivo | Pestaña del fragmento |
|---|---|
| `index.html` | HTML (solo un aviso visible en el editor de páginas) |
| `index.css` | CSS |
| `index.js` | JavaScript |

Sin configuración.

## Qué corrige

- **Salto al hacer scroll.** El jQuery del tema ponía `position: fixed` a la barra superior al primer pixel de scroll: el contenido subía 50 px de golpe (56 en celular) y aparecía otra barra encima. Ahora el header es `sticky`; al bajar se pliegan la barra superior y la de "Programas…" y el header toma ese mismo alto como margen, así el contenido no se mueve (medido: 0 px). Con sesión iniciada se acomoda bajo el menú de control de Liferay.
- **Menú principal partido en dos renglones** de 1024 a 1440 px ("Familias" y "Contacto" quedaban tapados). Ahora cabe en uno de 992 a 1920 px.
- **Modo claro/oscuro** para header y footer, con botón sol/luna en la barra superior y en la de celular. Sin elección guardada sigue el modo del dispositivo y lo resuelve el CSS, así que la página sale en su modo desde el primer instante (sin parpadeo). Si alguien elige con el botón, se guarda (`cl-modo`, la misma clave del kit) y manda en todas las páginas; los dos botones (Marco y kit) se avisan entre sí.
- **Buscador (portlet de ITESO):** panel, casilla de la lupa y campo con colores congruentes en claro y oscuro (antes el panel seguía azul brillante de noche y el botón de borrar salía gris). En celular: la X alineada con los otros íconos, campo de 64 px, enlaces en dos columnas sin salirse de la pantalla.
- **Menú hamburguesa de celular:** un solo fondo, separador entre los dos grupos, renglones de 44 px, el ícono cambia a X mientras está abierto. El buscador y el menú ya no se abren a la vez.
- **Contraste:** el hover del menú (2.4:1) y los enlaces grises del menú de celular (2.4:1) no pasaban AA; ahora 9.5:1 y 5.4:1.
- **Footer en celular:** sin el hueco de ~100 px antes de los acordeones.
- **Banderas e ícono de sesión** con texto para lectores de pantalla.

Los enlaces de idioma y de inicio de sesión **no necesitaban corrección**: Liferay ya les pone el `p_l_id` y la ruta de cada página (incluido `?…`). El `p_l_id=8550&redirect=/` del inventario en `web/sitio_actual/campuslab/` es solo de la portada, que es donde se raspó.

## Crear el fragmento (una vez)

1. Diseño > Fragmentos > conjunto **Campus Lab** > Nuevo > Fragmento básico. Nombre: "Marco Campus Lab".
2. Pegar cada archivo en su pestaña y Publicar.
3. Arrastrarlo a la Master Page, **lo más arriba posible** (o, para probar, a cualquier página de contenido). Así su JavaScript corre pronto y, si alguien eligió el modo contrario al de su dispositivo, el cambio casi no se nota. Va una sola vez por página: si queda dos veces, el segundo no hace nada.

## Probarlo sin publicar

```
python web/scripts/probar_en_sitio.py web/fragmentos/marco
```

Inyecta el fragmento en `/web/campuslab/temp`, saca capturas (escritorio y celular, claro y oscuro, arriba, con scroll y al final) en `catalogo/salida/capturas/` e imprime el salto medido al bajar 1, 60 y 400 px.
