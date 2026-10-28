#!/usr/bin/env bash
# Corre DENTRO del WSL de Pixilate (lo llama desplegar.sh). Desempaca, levanta y revisa.
# Uso: bash pixilate.sh <ruta del .tgz> <usuario de Tailscale permitido>
set -euo pipefail
paquete="$1"; usuario="$2"
destino="$HOME/srv/hojas-campo"
mkdir -p "$destino" "$HOME/.config"
tar -xzf "$paquete" -C "$destino"
if [ ! -f "$HOME/.config/hojas-campo.env" ]; then
  printf 'HOJAS_CAMPO_USUARIOS=%s\n' "$usuario" > "$HOME/.config/hojas-campo.env"
fi
chmod 600 "$HOME/.config/hojas-campo.env"
cd "$destino"
docker compose up -d --build
docker compose restart hojas-campo   # vuelve a leer datos_campo.json si cambió
docker compose ps
