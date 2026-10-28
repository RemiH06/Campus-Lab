#!/usr/bin/env bash
# Desde Aerilate: copia las marcas de Pixilate a salida/ (OneDrive las sube a la nube: segunda copia).
# Uso: bash respaldo.sh                      respaldar
#      bash respaldo.sh restaurar <archivo>  reemplazar las marcas de Pixilate (solo si se perdió el volumen)
set -euo pipefail
cd "$(dirname "$0")"
dir=../../salida/inventario_arboles/recorrido_2026
mkdir -p "$dir"

if [ "${1:-}" = "restaurar" ]; then
  scp -q "$2" pixilate:hojas-campo-marcas.jsonl
  scp -q restaurar.sh pixilate:hojas-campo-restaurar.sh
  ssh pixilate "wsl -d Debian -- bash /mnt/c/Users/Pixilate2/hojas-campo-restaurar.sh /mnt/c/Users/Pixilate2/hojas-campo-marcas.jsonl"
  ssh pixilate "del hojas-campo-marcas.jsonl"
  exit 0
fi

archivo="$dir/marcas_$(date +%Y%m%d-%H%M).jsonl"
ssh pixilate "wsl -d Debian -- docker exec hojas-campo cat /datos/marcas.jsonl" > "$archivo" 2>/dev/null || : > "$archivo"
cp "$archivo" "$dir/marcas.jsonl"
echo "$(wc -l < "$archivo") marcas en $archivo"
