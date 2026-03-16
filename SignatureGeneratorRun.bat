@echo off
echo Instalando dependências Node.js...
npm install

echo Instalando dependências Python...
pip install Pillow

echo Iniciando servidor...
start http://localhost:3000
node projeto/server.js
pause
