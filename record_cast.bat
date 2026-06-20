@echo off
title RedM Fishing Macro - Cast Recorder

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo  [WARNING] This recorder should run as Administrator.
    echo  Requesting UAC Elevation...
    echo ============================================================
    powershell -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

set "PYTHON_EXE="

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :run
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :run
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :run
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :run
)

echo [ERROR] Python not found!
pause
exit /b 1

:run
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt" --quiet 2>nul
"%PYTHON_EXE%" "%~dp0cast_recorder.py"
echo.
pause
