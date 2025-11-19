@echo off
echo ======================================
echo    Installazione Servizio DB-Desk
echo ======================================

:: Verifica privilegi amministrativi
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Eseguito come amministratore
) else (
    echo [ERROR] Questo script richiede privilegi di amministratore!
    echo Eseguire lo script come amministratore.
    pause
    exit /b 1
)

:: Percorso completo dello script di avvio
set "START_SCRIPT=%~dp0start_dbdesk.bat"

:: Crea task schedulato
echo.
echo [INFO] Creazione task schedulato per avvio automatico...
schtasks /Create /SC ONLOGON /TN "DB-Desk Server" /TR "\"%START_SCRIPT%\"" /RL HIGHEST /F

if %errorLevel% == 0 (
    echo [OK] Task schedulato creato con successo
    echo [INFO] DB-Desk si avvierà automaticamente al login
) else (
    echo [ERROR] Errore durante la creazione del task
)

:: Rimuovi eventuali collegamenti esistenti nella cartella Startup per evitare duplicati
echo.
echo [INFO] Rimozione eventuali collegamenti esistenti nella cartella Startup...
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\DB-Desk Server.lnk"
del "%SHORTCUT%" 2>nul

echo [INFO] Avvio automatico configurato tramite Task Scheduler (pi\u00f9 affidabile)

echo.
echo [INFO] Installazione completata!
echo [INFO] Il server si avvierà automaticamente al prossimo login
echo [INFO] Puoi anche avviarlo manualmente eseguendo start_dbdesk.bat
echo.
pause