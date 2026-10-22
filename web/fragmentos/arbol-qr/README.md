# Fragmento "Árbol QR"

Un árbol pequeño en la esquina inferior derecha de la página. Al tocarlo se abre un panel; al tocar el árbol, la cámara sube y su copa se vuelve el centro de un código QR, listo para escanear con el celular o descargar e imprimir (carteles, lonas, letreros).

El árbol cambia solo con el tema del sitio:

| Floración del sitio | Árbol |
|---|---|
| Clavellina (dic-ene) | Clavellina |
| Rosa morada (feb) | Rosa morada |
| Jacaranda (mar) | Jacaranda |
| Primavera (abr) | Primavera |
| Tabachín (may-jun) | Tabachín |
| Galeana (nov) | Galeana |
| Lluvias (jul-oct) | Tabachín con hojas, bajo la lluvia |

En modo oscuro el árbol se ve de noche. El QR siempre sale claro, para que el celular lo lea.

## Qué se edita y cómo (Configuración del fragmento)

| Qué | Cómo |
|---|---|
| A dónde lleva el QR | Vacío (lo normal): a la página donde está el fragmento, sea cual sea. O una dirección: completa (`https://campuslab.iteso.mx/orquideas`) o del sitio (`/web/campuslab/orquideas`) |
| Texto bajo el QR al descargarlo | El nombre que sale impreso debajo del código |

Se pone **una vez por página**, en cualquier lugar (siempre flota en la esquina). En el editor de páginas no flota: se ve como una nota punteada que dice a dónde lleva el QR, para poder seleccionarlo.

## Si algo sale mal

- Una dirección de más de unos 210 caracteres no cabe en el QR: el QR lleva a la página donde está y la nota del editor lo avisa. Lo mismo con una dirección mal escrita.
- Para imprimir, usar "Descargar QR" (sale plano, en blanco y negro, con la dirección debajo) y probarlo con un celular antes de mandarlo a imprenta.

## Para quien mantiene el código

Necesita el Marco: lee la floración y el modo de `<html>` (`data-cl-flor`, `data-cl-modo`) y se vuelve a pintar cuando cambian. El motor es el del componente 15 de `web/fuentes/prototipos/componentes_plantilla.html` (generador de QR propio, nivel M, versiones 1 a 10); si se mejora uno, pasar el cambio al otro. Idea de ICQR (Louis Raillé); el código es propio. No se usa el nombre "ICQR".
