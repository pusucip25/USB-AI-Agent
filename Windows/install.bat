@echo off
setlocal
title Portable AI - USB Setup
color 0E

echo ===================================================
echo     PORTABLE AI - USB SETUP (Windows)
echo ===================================================
echo.
echo  This installs everything onto this drive:
echo    - portable Python (nothing installed on the host PC)
echo    - portable Ollama engine
echo    - the AI model(s) you pick (~2-25 GB download)
echo.
echo  Minimum free space: 8 GB (30 GB for all 5 models)
echo  Make sure you have a good internet connection.
echo.
pause

set "CORE=%~dp0install-core.ps1"
if not exist "%CORE%" (
    echo.
    echo ===================================================
    echo  ERROR: install-core.ps1 is missing
    echo ===================================================
    echo.
    echo  It must sit next to install.bat:
    echo    %CORE%
    echo.
    echo  Re-download the repository (or restore that file)
    echo  and run install.bat again.
    echo.
    pause
    exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

rem Extra arguments are passed straight to the core script, e.g.
rem   install.bat -Models 1 -Yes        install.bat -SkipModels
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%CORE%" %*

set "RC=%errorlevel%"
echo.
if not "%RC%"=="0" (
    echo ===================================================
    echo   SETUP FINISHED WITH ERRORS ^(see messages above^)
    echo ===================================================
    echo.
    echo  Re-running install.bat is safe: finished downloads
    echo  are reused, only the failed steps are retried.
) else (
    echo ===================================================
    echo   SETUP COMPLETE! You're ready to go!
    echo ===================================================
    echo.
    echo  To start the agent:   Windows\start-agent.bat
    echo  Web chat UI:          Windows\start-fast-chat.bat
)
echo.
pause
exit /b %RC%
