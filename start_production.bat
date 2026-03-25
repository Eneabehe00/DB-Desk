@echo off
REM Script per avviare DB-Desk in modalità produzione con Waitress
REM Usa questo script per l'avvio normale del server

echo ========================================
echo DB-Desk - Avvio Server Produzione
echo ========================================
echo.

REM Verifica che Python sia installato
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: Python non trovato! Assicurati che Python sia installato e nel PATH.
    pause
    exit /b 1
)

REM Verifica che il file .env esista
if not exist .env (
    echo ATTENZIONE: File .env non trovato!
    echo Crea un file .env basandoti su .env.example
    pause
    exit /b 1
)

REM Imposta l'ambiente di produzione
set FLASK_CONFIG=production

REM Avvia il server con Waitress
echo Avvio server con Waitress...
echo.
python wsgi.py

REM Se il server si ferma, mostra un messaggio
echo.
echo Server fermato.
pause
