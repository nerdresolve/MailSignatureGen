@echo off
echo Instalando dependências Node.js...
npm install

echo Instalando dependências Python...
<<<<<<< HEAD
pip install Pillow
=======
pip install python-pptx
>>>>>>> 9ed8038559f57deb5e9d22058b3a34e04103df22

echo Iniciando servidor...
start http://localhost:3000
node projeto/server.js
pause
