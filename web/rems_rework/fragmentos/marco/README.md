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
- **Modo claro/oscuro** para header y footer, con botón sol/luna en la barra superior y en la de celular. Usa la misma elección que el kit (`cl-modo` en el navegador) o, si no hay, la del sistema. Sin JavaScript queda en claro.
- **Contraste:** el hover del menú (2.4:1) y los enlaces grises del menú de celular (2.4:1) no pasaban AA; ahora 9.5:1 y 5.4:1.
- **Footer en celular:** sin el hueco de ~100 px antes de los acordeones.
- **Banderas e ícono de sesión** con texto para lectores de pantalla.

Los enlaces de idioma y de inicio de sesión **no necesitaban corrección**: Liferay ya les pone el `p_l_id` y la ruta de cada página (incluido `?…`). El `p_l_id=8550&redirect=/` del inventario en `web/liferay_actual/` es solo de la portada, que es donde se raspó.

## Crear el fragmento (una vez)

1. Diseño > Fragmentos > conjunto **Campus Lab** > Nuevo > Fragmento básico. Nombre: "Marco Campus Lab".
2. Pegar cada archivo en su pestaña y Publicar.
3. Arrastrarlo a la Master Page (o, para probar, a cualquier página de contenido). Va una sola vez por página: si queda dos veces, el segundo no hace nada.

## Probarlo sin publicar

```
python web/camino_b/probar_en_sitio.py web/rems_rework/fragmentos/marco
```

Inyecta el fragmento en `/web/campuslab/temp`, saca capturas (escritorio y celular, claro y oscuro, arriba, con scroll y al final) en `reestructura/salida/capturas/` e imprime el salto medido al bajar 1, 60 y 400 px.
