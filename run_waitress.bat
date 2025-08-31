@echo off
cd /d %~dp0

REM Abrir navegador con localhost en paralelo
start "" "http://127.0.0.1:5000"

REM Ejecutar waitress
waitress-serve --listen=0.0.0.0:5000 run:app

pause
