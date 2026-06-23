# ============================================================
#  RedM Fishing Macro - Build Script
#  Run this on a machine with Python 3.10+ installed.
#
#  Usage:
#    powershell -ExecutionPolicy Bypass -File build_release.ps1
#
#  Output:
#    release/EpicGamesLauncher.exe  <- upload this to GitHub Releases
#    release/EpicGamesLauncher.zip  <- optional packaged backup
# ============================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

[console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $scriptDir "dist"
$releaseDir = Join-Path $scriptDir "release"
$packageDir = Join-Path $releaseDir "EpicGamesLauncher"
$releaseExePath = Join-Path $releaseDir "EpicGamesLauncher.exe"
$zipPath = Join-Path $releaseDir "EpicGamesLauncher.zip"

Set-Location $scriptDir

# ---- Find Python ----
$python = $null
foreach ($candidate in @("python", "py", "python3")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $python = $cmd.Source
        break
    }
}

if (-not $python) {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ and add it to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$pyVer = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[OK] Python $pyVer at $python" -ForegroundColor Green

# ---- Install dependencies ----
Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $python -m pip install -r (Join-Path $scriptDir "requirements.txt") --quiet
& $python -m pip install pyinstaller --quiet

# ---- Clean old build artifacts ----
Write-Host "Cleaning old build output..." -ForegroundColor Cyan
foreach ($dir in @("build", $distDir, $releaseDir)) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force
    }
}

# ---- Locate Tcl/Tk for tkinter bundling ----
$pythonRoot = Split-Path -Parent $python
$tclRoot = Join-Path $pythonRoot "tcl"
$tclLibrary = Join-Path $tclRoot "tcl8.6"
$tkLibrary = Join-Path $tclRoot "tk8.6"

# Handle embeddable Python (different layout)
if (-not (Test-Path $tclLibrary)) {
    $tclLibrary = Join-Path $pythonRoot "tcl\tcl8.6"
    $tkLibrary = Join-Path $pythonRoot "tcl\tk8.6"
}

$addDataArgs = @()
if ((Test-Path $tclLibrary) -and (Test-Path $tkLibrary)) {
    $env:TCL_LIBRARY = $tclLibrary
    $env:TK_LIBRARY = $tkLibrary
    $addDataArgs = @(
        "--add-data", "$tclLibrary;_tcl_data",
        "--add-data", "$tkLibrary;_tk_data"
    )
    Write-Host "[OK] Found Tcl/Tk" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Tcl/Tk not found - tkinter may not work in the build" -ForegroundColor Yellow
}

# ---- Build with PyInstaller ----
Write-Host "Building EpicGamesLauncher.exe..." -ForegroundColor Cyan

$pyInstallerArgs = @(
    "--noconfirm"
    "--onefile"
    "--windowed"
    "--name", "EpicGamesLauncher"
    "--hidden-import", "tkinter"
    "--hidden-import", "_tkinter"
    "--add-data", "templates;templates"
    "--add-data", "cast_profile.json;."
)
$pyInstallerArgs += $addDataArgs
$pyInstallerArgs += "fishing_gui.py"

& $python -m PyInstaller @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] PyInstaller build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$exePath = Join-Path $distDir "EpicGamesLauncher.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "[ERROR] EpicGamesLauncher.exe not found after build!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Build complete: $exePath" -ForegroundColor Green

# ---- Package into release folder ----
Write-Host "Packaging release..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

Copy-Item -Path $exePath -Destination $packageDir -Force
Copy-Item -Path $exePath -Destination $releaseExePath -Force

if (Test-Path "templates") {
    Copy-Item -Path "templates" -Destination $packageDir -Recurse -Force
}

if (Test-Path "cast_profile.json") {
    Copy-Item -Path "cast_profile.json" -Destination $packageDir -Force
}

# ---- Create zip ----
Write-Host "Creating zip..." -ForegroundColor Cyan
Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force

$zipSize = (Get-Item $zipPath).Length / 1MB
$exeSize = (Get-Item $releaseExePath).Length / 1MB
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Build successful!" -ForegroundColor Green
Write-Host "  Release EXE: $releaseExePath" -ForegroundColor White
Write-Host "  EXE Size: $([math]::Round($exeSize, 1)) MB" -ForegroundColor White
Write-Host "  Backup ZIP: $zipPath" -ForegroundColor White
Write-Host "  ZIP Size: $([math]::Round($zipSize, 1)) MB" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Upload this file to GitHub Releases as:" -ForegroundColor Yellow
Write-Host "  EpicGamesLauncher.exe" -ForegroundColor White
Write-Host ""
