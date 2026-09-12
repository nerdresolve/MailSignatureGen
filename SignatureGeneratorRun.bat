@echo off
title Gerador de Assinaturas

echo ==========================================
echo    MailSignatureGen
echo ==========================================
echo.

where node >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado. Baixe em https://nodejs.org/
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Baixe em https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Dependencias Node...
call npm install --silent
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias Node.
    pause
    exit /b 1
)

echo [2/3] Dependencias Python...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias Python.
    pause
    exit /b 1
)

echo [3/3] Iniciando...
echo.
echo Acesse http://localhost:3000   (Ctrl+C encerra)
echo.

start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3000"
node app/server.js
pause
