@echo off
REM Script per avviare DB-Desk in modalità sviluppo
REM Usa questo script per lo sviluppo locale con auto-reload

echo ========================================
echo DB-Desk - Avvio Server Sviluppo
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

REM Imposta l'ambiente di sviluppo
set FLASK_CONFIG=development

REM Avvia il server di sviluppo Flask
echo Avvio server di sviluppo Flask...
echo Con auto-reload attivo
echo.
python run.py

REM Se il server si ferma, mostra un messaggio
echo.
echo Server fermato.
pause
