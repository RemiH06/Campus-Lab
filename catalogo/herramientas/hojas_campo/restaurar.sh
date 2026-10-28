#!/usr/bin/env bash
# Corre DENTRO del WSL de Pixilate (lo llama respaldo.sh restaurar). Reemplaza las marcas del volumen.
set -euo pipefail
docker exec -i hojas-campo sh -c 'cat > /datos/marcas.jsonl' < "$1"
echo "Restauradas $(wc -l < "$1") marcas"
