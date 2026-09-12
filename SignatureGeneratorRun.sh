#!/usr/bin/env bash
# Sobe o gerador: confere o que falta, instala e abre o navegador.
set -euo pipefail

cd "$(dirname "$0")"

echo "=========================================="
echo "   MailSignatureGen"
echo "=========================================="
echo

for programa in node python3; do
  if ! command -v "$programa" >/dev/null 2>&1; then
    echo "[ERRO] $programa não encontrado."
    exit 1
  fi
done

echo "[1/3] Dependências Node..."
npm install --silent

echo "[2/3] Dependências Python..."
python3 -m pip install -r requirements.txt --quiet

echo "[3/3] Iniciando..."
echo
echo "Acesse http://localhost:3000   (Ctrl+C encerra)"
echo

# Abre o navegador sem travar o servidor, se houver como.
if command -v xdg-open >/dev/null 2>&1; then
  (sleep 2 && xdg-open http://localhost:3000) >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
  (sleep 2 && open http://localhost:3000) >/dev/null 2>&1 &
fi

exec node app/server.js
