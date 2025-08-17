@echo off
REM ================================
REM Script para correr Flask App
REM ================================

REM -------------------------------
REM Ir a la carpeta del proyecto
REM -------------------------------
cd /d "%~dp0"

REM -------------------------------
REM Activar entorno virtual
REM -------------------------------
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No se encontró el entorno virtual en venv\Scripts
    pause
    exit /b
)

REM -------------------------------
REM Configurar variables de entorno
REM -------------------------------
set FLASK_DEBUG=true
set PORT=5000
set FLASK_RUN_HOST=127.0.0.1

REM -------------------------------
REM Ejecutar run.py
REM -------------------------------
python run.py

REM -------------------------------
REM Pausar al finalizar para ver errores
REM -------------------------------
pause
