@echo off
title Gerador de Assinaturas - NerdResolve

echo ============================================
echo    Gerador de Assinaturas NerdResolve v2.0
echo ============================================
echo.

:: Verificar Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado.
    echo Baixe em: https://nodejs.org/
    pause
    exit /b 1
)

:: Verificar Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias Node.js...
call npm install --silent
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias Node.js.
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias Python...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias Python.
    pause
    exit /b 1
)

echo [3/3] Iniciando servidor...
echo.
echo Acesse: http://localhost:3000
echo Pressione Ctrl+C para encerrar o servidor.
echo.

:: Aguarda 2 segundos para o servidor subir antes de abrir o browser
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3000"

node projeto/server.js
pause
