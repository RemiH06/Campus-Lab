"""
Redimensiona fotos para publicar en páginas de Campus Lab / Liferay.

Uso:
    python redimensionar_imagenes.py <carpeta_entrada> [--salida <carpeta_salida>] [--estandar liferay] [--forzar]

Por default, si <carpeta_entrada> es ".../Arboretum/imgs", la salida es
".../Arboretum/resized" (carpeta hermana "resized"), como ya está armado
en web/Pre/Arboretum/. Se puede apuntar a otra carpeta con --salida.

Nunca sobrescribe los originales: solo lee de <carpeta_entrada> y escribe
copias redimensionadas en <carpeta_salida>. Es resumible — si ya existe el
archivo de salida lo salta, a menos que se pase --forzar.

Para agregar un estándar nuevo (otro tamaño, otro requisito de otra
sección de la página), solo hay que agregar una entrada a ESTANDARES.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageOps

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# Cada estándar: (ancho_max, alto_max). La imagen se ajusta para caber
# dentro de esas dimensiones sin recortar ni deformar (mantiene proporción,
# nunca agranda una imagen más chica que el estándar).
ESTANDARES = {
    "liferay": (1280, 768),
}


def redimensionar_una(ruta_entrada: Path, ruta_salida: Path, ancho_max: int, alto_max: int) -> tuple[int, int]:
    with Image.open(ruta_entrada) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((ancho_max, alto_max), Image.LANCZOS)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        img.save(ruta_salida, "JPEG", quality=85, optimize=True)
        return img.size


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("carpeta_entrada", type=Path, help="Carpeta con las fotos originales")
    parser.add_argument("--salida", type=Path, default=None, help="Carpeta de salida (default: carpeta hermana 'resized')")
    parser.add_argument("--estandar", default="liferay", choices=sorted(ESTANDARES), help="Estándar de tamaño a usar")
    parser.add_argument("--forzar", action="store_true", help="Vuelve a generar aunque ya exista el archivo de salida")
    args = parser.parse_args()

    if not args.carpeta_entrada.is_dir():
        parser.error(f"No existe la carpeta: {args.carpeta_entrada}")

    carpeta_salida = args.salida or (args.carpeta_entrada.parent / "resized")
    ancho_max, alto_max = ESTANDARES[args.estandar]

    rutas = sorted(p for p in args.carpeta_entrada.iterdir() if p.suffix.lower() in EXTENSIONES_VALIDAS)
    if not rutas:
        print(f"No hay imágenes en {args.carpeta_entrada}")
        return

    print(f"Estándar '{args.estandar}': máximo {ancho_max}x{alto_max}")
    print(f"Entrada:  {args.carpeta_entrada}")
    print(f"Salida:   {carpeta_salida}\n")

    for ruta in rutas:
        destino = carpeta_salida / f"{ruta.stem}.jpg"
        if destino.exists() and not args.forzar:
            print(f"  [saltado, ya existe] {destino.name}")
            continue
        peso_antes = ruta.stat().st_size / 1024
        ancho, alto = redimensionar_una(ruta, destino, ancho_max, alto_max)
        peso_despues = destino.stat().st_size / 1024
        print(f"  {ruta.name} -> {destino.name}  ({ancho}x{alto}, {peso_antes:.0f} KB -> {peso_despues:.0f} KB)")


if __name__ == "__main__":
    main()
