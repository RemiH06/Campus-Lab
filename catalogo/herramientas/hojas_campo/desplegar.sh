#!/usr/bin/env bash
# Desde Aerilate (Git Bash): rearma los datos y despliega en Pixilate (Docker en WSL + tailscale serve).
# Uso: bash desplegar.sh            Apagar lo expuesto: ssh pixilate "tailscale serve --https=8049 off"
set -euo pipefail
cd "$(dirname "$0")"
USUARIO="${HOJAS_CAMPO_USUARIO:-RemiH06@github}"

python preparar.py
tmp="$(mktemp -d)"
cp -r backend.py static Dockerfile compose.yml "$tmp/"
rm -rf "$tmp/static/__pycache__"
mkdir "$tmp/datos"
cp ../../salida/inventario_arboles/hojas_campo/datos_campo.json "$tmp/datos/"
tar -C "$tmp" -czf "$tmp.tgz" .

scp -q "$tmp.tgz" pixilate:hojas-campo.tgz
scp -q pixilate.sh pixilate:hojas-campo-pixilate.sh
ssh pixilate "wsl -d Debian -- bash /mnt/c/Users/Pixilate2/hojas-campo-pixilate.sh /mnt/c/Users/Pixilate2/hojas-campo.tgz $USUARIO"
ssh pixilate "tailscale serve --bg --https=8049 http://127.0.0.1:8049"
rm -rf "$tmp" "$tmp.tgz"
echo "Listo: https://pixilate2.tail1e8819.ts.net:8049/"
