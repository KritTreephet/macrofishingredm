@echo off
title EpicGamesLauncher

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo  [WARNING] GUI should run as Administrator to control RedM.
    echo  Requesting UAC Elevation...
    echo ============================================================
    powershell -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

set "PYTHON_EXE="
set "PYTHONW_EXE="
set "PYTHONW_IS_PATH_COMMAND=0"

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    set "PYTHONW_EXE=pythonw"
    set "PYTHONW_IS_PATH_COMMAND=1"
    goto :run
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    set "PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
    goto :run
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    set "PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
    goto :run
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    set "PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"
    goto :run
)

echo [ERROR] Python not found!
pause
exit /b 1

:run
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt" --quiet 2>nul
if "%PYTHONW_IS_PATH_COMMAND%"=="1" (
    pythonw --version >nul 2>&1
    if %errorlevel% neq 0 (
        set "PYTHONW_EXE=%PYTHON_EXE%"
    )
) else (
    if not exist "%PYTHONW_EXE%" (
        set "PYTHONW_EXE=%PYTHON_EXE%"
    )
)
start "" "%PYTHONW_EXE%" "%~dp0fishing_gui.py"
