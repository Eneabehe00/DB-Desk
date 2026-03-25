@echo off
REM ==============================================================================
REM Script COMPLETO per installare DB-Desk come servizio Windows
REM Combina installazione + correzione in un unico passaggio
REM ==============================================================================
REM ESEGUI COME AMMINISTRATORE!
REM ==============================================================================

echo ===============================================================================
echo Installazione Completa Servizio DB-Desk
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

REM Verifica NSSM
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: NSSM non trovato!
    echo.
    echo Installa con: winget install NSSM
    echo.
    pause
    exit /b 1
)

echo [OK] NSSM trovato
echo.

REM Trova Python REALE
echo Ricerca Python...
set "PYTHON_PATH="
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo    Trovato: %%i
    echo %%i | find /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PYTHON_PATH=%%i"
        goto :found_python
    )
)

:found_python
if "%PYTHON_PATH%"=="" (
    echo ERRORE: Python non trovato!
    pause
    exit /b 1
)

echo [OK] Python: %PYTHON_PATH%
echo.

REM Verifica file
if not exist "C:\DB-Desk\wsgi.py" (
    echo ERRORE: wsgi.py non trovato in C:\DB-Desk
    pause
    exit /b 1
)

if not exist "C:\DB-Desk\.env" (
    echo ERRORE: File .env non trovato!
    echo Crea il file .env prima di continuare
    pause
    exit /b 1
)

echo [OK] File verificati
echo.

REM Crea cartella logs
if not exist "C:\DB-Desk\logs" mkdir "C:\DB-Desk\logs"

REM Sotto-cartelle per log ordinati
if not exist "C:\DB-Desk\logs\app\main" mkdir "C:\DB-Desk\logs\app\main"
if not exist "C:\DB-Desk\logs\app\error" mkdir "C:\DB-Desk\logs\app\error"
if not exist "C:\DB-Desk\logs\service\stdout" mkdir "C:\DB-Desk\logs\service\stdout"
if not exist "C:\DB-Desk\logs\service\stderr" mkdir "C:\DB-Desk\logs\service\stderr"

REM ==============================================================================
REM FASE 1: RIMOZIONE SERVIZIO ESISTENTE (se presente)
REM ==============================================================================

sc query DBDesk >nul 2>&1
if %errorlevel% equ 0 (
    echo [Fase 1/3] Rimozione servizio esistente...
    nssm stop DBDesk >nul 2>&1
    timeout /t 2 /nobreak >nul
    nssm remove DBDesk confirm >nul 2>&1
    echo    OK - Servizio rimosso
    echo.
) else (
    echo [Fase 1/3] Nessun servizio esistente da rimuovere
    echo.
)

REM ==============================================================================
REM FASE 2: INSTALLAZIONE SERVIZIO BASE
REM ==============================================================================

echo [Fase 2/3] Installazione servizio base...

nssm install DBDesk "%PYTHON_PATH%" "C:\DB-Desk\wsgi.py"

if %errorlevel% neq 0 (
    echo    ERRORE: Installazione fallita!
    pause
    exit /b 1
)

echo    OK - Servizio installato
echo.

REM ==============================================================================
REM FASE 3: CONFIGURAZIONE COMPLETA E CORREZIONI
REM ==============================================================================

echo [Fase 3/3] Configurazione completa...

REM Directory e nomi
nssm set DBDesk AppDirectory "C:\DB-Desk" >nul
nssm set DBDesk DisplayName "DB-Desk Ticket System" >nul
nssm set DBDesk Description "Sistema di gestione ticket e clienti DB-Desk con Waitress" >nul

REM CRITICO: Python corretto (non WindowsApps)
nssm set DBDesk Application "%PYTHON_PATH%" >nul

REM CRITICO: Variabili d'ambiente
nssm set DBDesk AppEnvironmentExtra "FLASK_CONFIG=production" >nul

REM Auto-start e restart
nssm set DBDesk Start SERVICE_AUTO_START >nul
nssm set DBDesk AppExit Default Restart >nul
nssm set DBDesk AppThrottle 5000 >nul
nssm set DBDesk AppRestartDelay 5000 >nul

REM Logging
nssm set DBDesk AppStdout "C:\DB-Desk\logs\service\stdout\service_stdout.log" >nul
nssm set DBDesk AppStderr "C:\DB-Desk\logs\service\stderr\service_stderr.log" >nul

REM Rotazione log
nssm set DBDesk AppStdoutCreationDisposition 4 >nul
nssm set DBDesk AppStderrCreationDisposition 4 >nul
nssm set DBDesk AppRotateFiles 1 >nul
nssm set DBDesk AppRotateOnline 1 >nul
nssm set DBDesk AppRotateBytes 10485760 >nul

echo    OK - Servizio configurato
echo.

REM ==============================================================================
REM FASE 4: AVVIO E VERIFICA
REM ==============================================================================

echo [Fase 4/4] Avvio servizio...
echo.

nssm start DBDesk

REM Attendi avvio
timeout /t 5 /nobreak >nul

REM Verifica stato
for /L %%i in (1,1,3) do (
    nssm status DBDesk | find "SERVICE_RUNNING" >nul
    if not errorlevel 1 goto :success
    echo    Tentativo %%i/3 - Attesa...
    timeout /t 2 /nobreak >nul
)

REM Se arriviamo qui, il servizio non è running
goto :failure

:success
echo.
echo ===============================================================================
echo SUCCESSO! Servizio installato e avviato
echo ===============================================================================
echo.
echo Configurazione:
echo    Nome servizio:  DBDesk
echo    Python:         %PYTHON_PATH%
echo    Directory:      C:\DB-Desk
echo    Ambiente:       production
echo    Auto-start:     Si
echo    Auto-restart:   Si (5 secondi)
echo.
echo Verifica:
echo    1. Browser: http://192.168.191.74:5000
echo    2. Settings -^> Log Sistema
echo.
echo Gestione:
echo    nssm status DBDesk    - Stato
echo    nssm restart DBDesk   - Riavvia
echo    nssm stop DBDesk      - Ferma
echo    services.msc          - GUI Windows
echo.
goto :end

:failure
echo.
echo ===============================================================================
echo ERRORE: Il servizio non si avvia
echo ===============================================================================
echo.
nssm status DBDesk
echo.
echo Diagnostica:
echo.

if exist "C:\DB-Desk\logs\service\stderr\service_stderr.log" (
    echo === service_stderr.log ===
    type "C:\DB-Desk\logs\service\stderr\service_stderr.log"
    echo.
)

if exist "C:\DB-Desk\logs\app\error\dbdesk_error.log" (
    echo === dbdesk_error.log ===
    type "C:\DB-Desk\logs\app\error\dbdesk_error.log"
    echo.
)

echo.
echo Prova manualmente per vedere l'errore:
echo    cd C:\DB-Desk
echo    python wsgi.py
echo.
echo Oppure controlla la configurazione:
echo    nssm get DBDesk Application
echo    nssm get DBDesk AppEnvironmentExtra
echo.

:end
pause
