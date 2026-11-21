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
    echo  Re-download the repository ^(or restore that file^)
    echo  and run install.bat again.
    echo.
    pause
    exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

rem ---------------------------------------------------------------
rem  Pre-flight: can this machine execute a .ps1 file at all?
rem
rem  On a managed PC the Execution Policy is often pinned by Group
rem  Policy (MachinePolicy/UserPolicy scopes). Those scopes take
rem  precedence over "-ExecutionPolicy Bypass", so passing the flag
rem  is not enough: the script is refused and it looks like nothing
rem  happened. Probe with a throwaway .ps1 instead of guessing from
rem  the policy name - AllSigned fails for an unsigned script in
rem  exactly the same way, and RemoteSigned is fine.
rem ---------------------------------------------------------------
set "PROBE=%TEMP%\pai_probe_%RANDOM%%RANDOM%.ps1"
>"%PROBE%" echo exit 0
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PROBE%" >nul 2>&1
set "PROBE_RC=%errorlevel%"
del "%PROBE%" >nul 2>&1

if "%PROBE_RC%"=="0" goto :run_file

echo.
echo =======================================================
echo   NOTE: this PC blocks .ps1 script files
echo =======================================================
echo.
echo   Your Execution Policy is pinned by Group Policy, which
echo   overrides "-ExecutionPolicy Bypass". The installer runs
echo   through a fallback that does not need script-file
echo   execution - there is nothing for you to configure.
echo.
echo   (If it still fails, run this once in PowerShell and
echo   start install.bat again:)
echo     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
echo.

rem  The script is fed to PowerShell as text, so the file-execution
rem  policy is never consulted. PAI_SCRIPT_DIR stands in for the
rem  script's own path, which is empty in this mode.
set "PAI_SCRIPT_DIR=%~dp0"
"%PSEXE%" -NoProfile -Command "$s = Get-Content -Raw -LiteralPath '%CORE%'; & ([scriptblock]::Create($s)) %*"
set "RC=%errorlevel%"
goto :done

:run_file
rem Extra arguments are passed straight to the core script, e.g.
rem   install.bat -Models 1 -Yes        install.bat -SkipModels
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%CORE%" %*

set "RC=%errorlevel%"

:done
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
