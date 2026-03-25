@echo off
REM ==============================================================================
REM Script per disinstallare il servizio Windows DB-Desk
REM ==============================================================================
REM
REM IMPORTANTE: Questo script deve essere eseguito come Amministratore!
REM
REM ==============================================================================

echo ===============================================================================
echo Disinstallazione Servizio Windows DB-Desk
echo ===============================================================================
echo.

REM Verifica privilegi amministratore
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: Questo script richiede privilegi di amministratore!
    echo.
    echo Fai click destro su questo file e seleziona "Esegui come amministratore"
    echo.
    pause
    exit /b 1
)

echo [OK] Privilegi amministratore verificati
echo.

REM Verifica se il servizio esiste
sc query DBDesk >nul 2>&1
if %errorlevel% neq 0 (
    echo ATTENZIONE: Il servizio DBDesk non e' installato!
    echo.
    pause
    exit /b 0
)

echo Il servizio DBDesk e' attualmente installato.
echo.
choice /C SN /M "Vuoi procedere con la disinstallazione"
if errorlevel 2 (
    echo Disinstallazione annullata.
    pause
    exit /b 0
)

echo.
echo Disinstallazione in corso...
echo.

REM Verifica presenza NSSM
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo ATTENZIONE: NSSM non trovato nel PATH!
    echo Provo a fermare il servizio con sc...
    
    sc stop DBDesk
    timeout /t 3 /nobreak >nul
    sc delete DBDesk
    
    if %errorlevel% equ 0 (
        echo [OK] Servizio rimosso
        echo.
        pause
        exit /b 0
    ) else (
        echo ERRORE: Impossibile rimuovere il servizio
        echo Rimuovilo manualmente da services.msc
        pause
        exit /b 1
    )
)

REM Ferma il servizio
echo Arresto servizio...
nssm stop DBDesk

if %errorlevel% equ 0 (
    echo [OK] Servizio fermato
) else (
    echo [ATTENZIONE] Il servizio potrebbe essere gia' fermo
)

REM Attendi che si fermi completamente
timeout /t 3 /nobreak >nul

REM Rimuovi il servizio
echo Rimozione servizio...
nssm remove DBDesk confirm

if %errorlevel% neq 0 (
    echo ERRORE: Rimozione servizio fallita!
    pause
    exit /b 1
)

echo [OK] Servizio rimosso
echo.

echo ===============================================================================
echo DISINSTALLAZIONE COMPLETATA!
echo ===============================================================================
echo.
echo Il servizio "DBDesk" e' stato disinstallato con successo.
echo.
echo NOTA: I file di log in %~dp0logs sono stati mantenuti.
echo Se vuoi eliminarli, fallo manualmente.
echo.
pause
