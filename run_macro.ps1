# ═══════════════════════════════════════
#  🎣 RedM Fishing Macro - PowerShell Launcher
# ═══════════════════════════════════════

$Host.UI.RawUI.WindowTitle = "RedM Fishing Macro"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check for Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "  [WARNING] สคริปต์นี้ต้องใช้สิทธิ์ Administrator เพื่อส่งปุ่มกดเข้าเกม!" -ForegroundColor Red
    Write-Host "  กำลังขอสิทธิ์ Administrator..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host ""
Write-Host "  ══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   🎣 RedM Fishing Macro - Launcher" -ForegroundColor Cyan
Write-Host "  ══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Find Python
$PythonPath = $null
$SearchPaths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
)

# Try 'python' from PATH first
try {
    $testPython = & python --version 2>&1
    if ($testPython -match "Python \d") {
        $PythonPath = "python"
    }
} catch {}

# If not found on PATH, search common install locations
if (-not $PythonPath) {
    foreach ($path in $SearchPaths) {
        if (Test-Path $path) {
            $PythonPath = $path
            break
        }
    }
}

if (-not $PythonPath) {
    Write-Host "  [ERROR] ไม่พบ Python!" -ForegroundColor Red
    Write-Host "  กรุณาติดตั้งจาก: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "`n  กด Enter เพื่อออก"
    exit 1
}

$pyVer = & $PythonPath --version 2>&1
Write-Host "  [OK] $pyVer" -ForegroundColor Green
Write-Host "  Path: $PythonPath" -ForegroundColor DarkGray
Write-Host ""

# Install dependencies
Write-Host "  กำลังตรวจสอบ dependencies..." -ForegroundColor Yellow
& $PythonPath -m pip install -r "$ScriptDir\requirements.txt" --quiet 2>$null
Write-Host "  [OK] dependencies พร้อม" -ForegroundColor Green
Write-Host ""

# Run macro
if ($args -contains "--capture") {
    Write-Host "  📸 เปิดโหมดจับภาพ Template..." -ForegroundColor Magenta
    & $PythonPath "$ScriptDir\fishing_macro.py" --capture
} else {
    Write-Host "  🎣 เริ่มโปรแกรม Fishing Macro..." -ForegroundColor Green
    Write-Host "  ──────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "   F9  = เริ่ม macro" -ForegroundColor Yellow
    Write-Host "   F10 = หยุด macro" -ForegroundColor Yellow
    Write-Host "  ──────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
    & $PythonPath "$ScriptDir\fishing_macro.py"
}

Write-Host ""
Read-Host "  กด Enter เพื่อออก"
