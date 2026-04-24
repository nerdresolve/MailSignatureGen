#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo "   Gerador de Assinaturas NerdResolve v2.0"
echo "============================================"
echo

# Verificar Node.js
if ! command -v node &>/dev/null; then
    echo "[ERRO] Node.js nao encontrado."
    echo "Instale com: sudo apt install nodejs npm"
    exit 1
fi

# Verificar Python
if ! command -v python3 &>/dev/null; then
    echo "[ERRO] Python 3 nao encontrado."
    echo "Instale com: sudo apt install python3 python3-pip"
    exit 1
fi

# Verificar pip
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
    echo "[ERRO] pip nao encontrado."
    echo "Instale com: sudo apt install python3-pip"
    exit 1
fi

echo "[1/3] Instalando dependencias Node.js..."
npm install --silent

echo "[2/3] Instalando dependencias Python..."
python3 -m pip install -r requirements.txt --quiet

echo "[3/3] Iniciando servidor..."
echo
echo "Acesse: http://localhost:3000"
echo "Pressione Ctrl+C para encerrar o servidor."
echo

# Abrir browser se disponível (ambientes desktop)
if command -v xdg-open &>/dev/null; then
    (sleep 2 && xdg-open http://localhost:3000) &
elif command -v open &>/dev/null; then
    (sleep 2 && open http://localhost:3000) &
fi

node projeto/server.js
