@echo off
title DB-Desk Server
echo ======================================
echo    Avvio Server DB-Desk
echo ======================================

:: Imposta il percorso dell'applicazione alla directory dello script
cd /d "%~dp0"
echo [INFO] Directory di lavoro: %CD%

:: Attiva l'ambiente virtuale se esiste
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [WARN] Ambiente virtuale non trovato
)

:: Imposta variabili d'ambiente
set FLASK_APP=run.py
set FLASK_ENV=production
set FLASK_DEBUG=0

:: Verifica che run.py esista
if not exist "run.py" (
    echo [ERROR] File run.py non trovato nella directory corrente!
    echo [ERROR] Directory corrente: %CD%
    pause
    exit /b 1
)

:: Avvia il server
echo.
echo [INFO] Avvio server DB-Desk...
echo [INFO] Server disponibile su http://localhost:5000
echo [INFO] Premi CTRL+C per terminare
echo.

python "%~dp0run.py"

:: In caso di errore
if errorlevel 1 (
    echo.
    echo [ERROR] Errore durante l'avvio del server
    echo [INFO] Il server verrà riavviato automaticamente tra 10 secondi...
    timeout /t 10
    start "" "%~f0"
    exit
)