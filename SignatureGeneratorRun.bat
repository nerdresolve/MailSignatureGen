@echo off
echo Instalando dependencias Node.js...
npm install

echo Instalando dependencias Python...
python -m pip install -r requirements.txt

echo Iniciando servidor...
start http://localhost:3000
node projeto/server.js
pause
