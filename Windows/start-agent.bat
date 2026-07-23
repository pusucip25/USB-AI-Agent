@echo off
title USB AI Agent - Portable Agent
color 0A

echo ===================================================
echo     USB AI AGENT - Agent Portabil pe SSD
echo ===================================================
echo.
echo  Ruleaza un agent AI autonom folosind modelele
echo  tale locale de pe USB/SSD.
echo.
echo  Model default: qwen3.5:9b (schimba cu /model)
echo.

:: Set paths to USB Shared Folder
set "OLLAMA_MODELS=%~dp0..\Shared\models\ollama_data"
set "OLLAMA_ORIGINS=*"
set "OLLAMA_HOST=127.0.0.1:11434"

:: -------------------------------------------------------
:: Find Python: prefer portable USB copy, then system
:: -------------------------------------------------------
set "PYTHON_CMD="

:: Check for portable Python bundled on USB
if exist "%~dp0..\Shared\python\python.exe" (
    set "PYTHON_CMD=%~dp0..\Shared\python\python.exe"
    echo [OK] Using portable Python from USB drive.
    goto :PythonReady
)

:: Check for system-installed Python
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    echo [OK] Using system Python.
    goto :PythonReady
)

:: Python not found anywhere - download portable
echo ===================================================
echo  Python not found - downloading portable Python...
echo  (This only happens once, ~11MB download)
echo ===================================================
echo.

curl -L "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip" -o "%~dp0..\Shared\python-embed.zip"
if %errorlevel% neq 0 (
    echo Download failed. Please check your internet connection.
    pause
    exit
)

echo Extracting...
powershell -Command "Expand-Archive -Path '%~dp0..\Shared\python-embed.zip' -DestinationPath '%~dp0..\Shared\python' -Force"
del "%~dp0..\Shared\python-embed.zip" >nul 2>&1

if exist "%~dp0..\Shared\python\python.exe" (
    set "PYTHON_CMD=%~dp0..\Shared\python\python.exe"
    echo [OK] Portable Python installed on USB successfully!
) else (
    echo Failed to extract Python. Please try again.
    pause
    exit
)

:: -------------------------------------------------------
:: Start Ollama Engine (if not running)
:: -------------------------------------------------------
:PythonReady

if not exist "%~dp0..\Shared\bin\ollama-windows.exe" (
    echo.
    echo ===================================================
    echo  ERROR: Ollama Engine Not Found!
    echo ===================================================
    echo.
    echo  The AI engine hasn't been set up yet.
    echo  Please double-click "install.bat" in the Windows 
    echo  folder first to download the components.
    echo.
    pause
    exit
)

:: Check if Ollama is already running
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Ollama engine is already running!
    goto :StartAgent
)

echo Starting Ollama Engine...
start /b "" "%~dp0..\Shared\bin\ollama-windows.exe" serve

echo Waiting for engine to initialize...
:WaitLoop
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 goto :WaitLoop
echo [OK] Engine is online!

:: -------------------------------------------------------
:: Start Agent
:: -------------------------------------------------------
:StartAgent
echo.
echo ===================================================
echo  AGENT PORNIT
echo  Scrie /help pentru comenzi, /exit pentru a iesi
echo  Inchide fereastra pentru a opri totul.
echo ===================================================
echo.

%PYTHON_CMD% "%~dp0..\Shared\agent.py"

echo.
echo Shutting down...
echo Done. Goodbye!
pause
