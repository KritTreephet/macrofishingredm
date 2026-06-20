@echo off
title RedM Fishing Macro

:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================================
    echo  [WARNING] This script must run as Administrator to control games.
    echo  Requesting UAC Elevation...
    echo ============================================================
    powershell -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

echo.
echo  ======================================
echo   RedM Fishing Macro - Launcher
echo  ======================================
echo.

set "PYTHON_EXE="

:: Try python on PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :run
)

:: Try common install paths
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

echo  [ERROR] Python not found!
echo  Please install Python from: https://www.python.org/downloads/
pause
exit /b 1

:run
echo  [OK] Found Python
"%PYTHON_EXE%" --version
echo.

echo  Installing dependencies...
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt" --quiet 2>nul
echo  [OK] Dependencies ready
echo.

if "%1"=="--capture" (
    echo  Starting Template Capture Mode...
    "%PYTHON_EXE%" "%~dp0fishing_macro.py" --capture
) else (
    echo  Starting Fishing Macro...
    echo  ------------------------------------
    echo   F9  = Start macro
    echo   F10 = Stop macro
    echo  ------------------------------------
    echo.
    "%PYTHON_EXE%" "%~dp0fishing_macro.py"
)

echo.
pause
