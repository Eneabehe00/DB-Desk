@echo off
echo ======================================
echo    Rimozione Servizio DB-Desk
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

:: Termina eventuali processi DB-Desk attivi
echo.
echo [INFO] Terminazione eventuali processi DB-Desk attivi...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq DB-Desk Server" 2>nul
timeout /t 2 >nul

:: Rimuovi task schedulato
echo.
echo [INFO] Rimozione task schedulato...
schtasks /Delete /TN "DB-Desk Server" /F

if %errorLevel% == 0 (
    echo [OK] Task schedulato rimosso con successo
) else (
    echo [WARN] Task schedulato non trovato o errore durante la rimozione
)

:: Rimuovi collegamento dal menu Start
echo.
echo [INFO] Rimozione collegamento dal menu Start...
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\DB-Desk Server.lnk"

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo [OK] Collegamento rimosso con successo
) else (
    echo [WARN] Collegamento non trovato
)

echo.
echo [INFO] Rimozione completata!
echo [INFO] Il server non si avvierà più automaticamente
echo.
pause